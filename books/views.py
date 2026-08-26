import json
import logging
from datetime import timedelta
import razorpay
import os
import mimetypes
from decimal import Decimal

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.http import (
    HttpResponse, 
    FileResponse, 
    HttpResponseForbidden, 
    HttpResponseBadRequest, 
    JsonResponse,
    Http404
)
from django.utils import timezone
from django.db import transaction, models
from django.db.models import Q, F
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.urls import reverse

from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, inline_serializer

from django_ratelimit.decorators import ratelimit
from users.decorators import role_required

from payments.models import Order
from .models import (
    Book, 
    BookRequest, 
    LibrarySubscription, 
    BookSubscription, 
    CartItem, 
    PurchasedBook, 
    PendingGift,
    Documentary,
    Art,
    MediaItem,
    PurchasedDocumentary,
    PurchasedArt
)
from .forms import BookForm, MediaItemForm
from .serializer import BookSerializer

logger = logging.getLogger(__name__)


def get_razorpay_client():
    """Dynamically instantiates Razorpay Client with active settings keys."""
    return razorpay.Client(
        auth=(
            getattr(settings, 'RAZORPAY_KEY_ID', ''),
            getattr(settings, 'RAZORPAY_KEY_SECRET', '')
        )
    )


# ==========================================
# --- 1. CATALOG & DETAIL VIEWS ---
# ==========================================

@login_required
def book_list(request):
    query = request.GET.get('q', '').strip()
    books = Book.objects.select_related('created_by').all().order_by('-id')

    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(author__icontains=query) |
            Q(created_by__username__icontains=query)
        )

    if hasattr(request.user, 'profile') and request.user.profile.role == 'STUDENT':
        student_requests = BookRequest.objects.filter(student=request.user, book__isnull=False).values('book_id', 'status')
        request_map = {req['book_id']: req['status'] for req in student_requests}

        purchased_book_ids = set(PurchasedBook.objects.filter(student=request.user).values_list('book_id', flat=True))
        cart_book_ids = set(CartItem.objects.filter(student=request.user, book__isnull=False).values_list('book_id', flat=True))

        for book in books:
            book.user_request_status = request_map.get(book.id, None)
            book.is_purchased = book.id in purchased_book_ids
            book.in_cart = book.id in cart_book_ids

    context = {
        'books': books,
        'search_query': query,
        'cart_count': CartItem.objects.filter(student=request.user).count() if hasattr(request.user, 'profile') and request.user.profile.role == 'STUDENT' else 0
    }
    return render(request, 'books/book_list.html', context)


@login_required
def book_detail(request, book_id):
    book = get_object_or_404(Book.objects.select_related('created_by'), id=book_id)

    Book.objects.filter(id=book.id).update(views=F('views') + 1)
    book.refresh_from_db()

    user_request = None
    is_purchased = False
    in_cart = False

    if hasattr(request.user, 'profile') and request.user.profile.role == 'STUDENT':
        user_request = BookRequest.objects.filter(
            student=request.user, 
            book=book
        ).order_by('-requested_at').first()
        is_purchased = PurchasedBook.objects.filter(student=request.user, book=book).exists()
        in_cart = CartItem.objects.filter(student=request.user, book=book).exists()

    context = {
        'book': book,
        'user_request': user_request,
        'is_purchased': is_purchased,
        'in_cart': in_cart,
    }
    return render(request, 'books/book_detail.html', context)


@extend_schema(
    summary="Get user cart count",
    description="Returns the total number of items in the authenticated user's cart.",
    responses={
        200: inline_serializer(
            name='CartCountResponse',
            fields={
                'cart_count': serializers.IntegerField()
            }
        )
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cart_count(request):
    if hasattr(request.user, 'profile') and request.user.profile.role == 'STUDENT':
        count = CartItem.objects.filter(student=request.user).count()
        return JsonResponse({'cart_count': count})
    return JsonResponse({'cart_count': 0})


# ==========================================
# --- 2. CART MANAGEMENT & PURCHASES ---
# ==========================================

@login_required
def cart_detail(request):
    cart_items = CartItem.objects.filter(student=request.user).select_related('book', 'art', 'documentary', 'media_item')
    
    total_amount = Decimal('0.00')
    for item in cart_items:
        if item.book:
            price = getattr(item.book, 'price', None) or Decimal('39.00')
        elif item.art:
            price = getattr(item.art, 'price', None) or Decimal('59.00')
        elif item.documentary:
            price = getattr(item.documentary, 'price', None) or Decimal('109.00')
        elif item.media_item:
            price = getattr(item.media_item, 'price', None) or Decimal('39.00')
        else:
            price = Decimal('39.00')
            
        total_amount += Decimal(str(price))

    context = {
        'cart_items': cart_items,
        'item_count': cart_items.count(),
        'total_amount': total_amount,
    }
    return render(request, 'books/cart_detail.html', context)

view_cart = cart_detail


def resolve_media_object(category, item_id):
    cat = str(category).lower().strip()

    if cat in ["arts", "art", "art_section", "gallery"]:
        media_obj = get_object_or_404(Art, id=item_id)
        lookup_kwargs = {"art": media_obj, "book": None, "documentary": None, "media_item": None}
    elif cat in ["documentary", "documentaries", "docs"]:
        media_obj = get_object_or_404(Documentary, id=item_id)
        lookup_kwargs = {"documentary": media_obj, "book": None, "art": None, "media_item": None}
    elif cat in ["media", "media_item"]:
        media_obj = get_object_or_404(MediaItem, id=item_id)
        lookup_kwargs = {"media_item": media_obj, "book": None, "art": None, "documentary": None}
    else:
        media_obj = get_object_or_404(Book, id=item_id)
        lookup_kwargs = {"book": media_obj, "art": None, "documentary": None, "media_item": None}

    return media_obj, lookup_kwargs


def user_has_purchased(user, media_obj=None, art_obj=None):
    if not user.is_authenticated:
        return False

    if user.is_superuser or user.is_staff:
        return True

    if art_obj:
        return PurchasedArt.objects.filter(student=user, art=art_obj).exists() or \
               PurchasedBook.objects.filter(student=user, media_item__title=art_obj.title).exists()

    if media_obj:
        if isinstance(media_obj, Book):
            return PurchasedBook.objects.filter(student=user, book=media_obj).exists()
        elif isinstance(media_obj, Art):
            return PurchasedArt.objects.filter(student=user, art=media_obj).exists()
        elif isinstance(media_obj, Documentary):
            return PurchasedDocumentary.objects.filter(student=user, documentary=media_obj).exists()
        elif isinstance(media_obj, MediaItem):
            return PurchasedBook.objects.filter(student=user, media_item=media_obj).exists()

    return False


def check_already_purchased(user, media_obj):
    return user_has_purchased(user, media_obj=media_obj)


@login_required
@role_required(["STUDENT"])
def add_to_cart(request, book_id=None):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid request method."}, status=405)

    category = "books"
    item_id = book_id

    if getattr(request, 'data', None):
        data = request.data
        item_id = data.get("item_id") or data.get("media_id") or data.get("book_id") or item_id
        category = data.get("category", category)
    elif request.content_type == "application/json" and request.body:
        try:
            data = json.loads(request.body.decode('utf-8'))
            item_id = data.get("item_id") or data.get("media_id") or data.get("book_id") or item_id
            category = data.get("category", category)
        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON format."}, status=400)

    if not item_id:
        return JsonResponse({"status": "error", "message": "Item ID is required."}, status=400)

    media_obj, lookup_kwargs = resolve_media_object(category, item_id)

    if check_already_purchased(request.user, media_obj):
        msg = f'You already own "{media_obj.title}".'
        messages.info(request, msg)
        created = False
    else:
        filter_kwargs = {k: v for k, v in lookup_kwargs.items() if v is not None}
        filter_kwargs['student'] = request.user

        item, created = CartItem.objects.get_or_create(**filter_kwargs)

        if created:
            msg = f'"{media_obj.title}" was added to your cart.'
            messages.success(request, msg)
        else:
            msg = f'"{media_obj.title}" is already in your cart.'
            messages.info(request, msg)

    cart_count = CartItem.objects.filter(student=request.user).count()

    if (
        request.headers.get("x-requested-with") == "XMLHttpRequest"
        or request.content_type == "application/json"
    ):
        return JsonResponse({
            "status": "success" if created else "info",
            "message": msg,
            "cart_count": cart_count
        })

    next_url = request.META.get('HTTP_REFERER')
    if next_url:
        return redirect(next_url)
    
    return redirect('books:book_list')


@extend_schema(
    summary="Add a single item to cart",
    description="Adds a single media or book item to the authenticated student's shopping cart.",
    request=inline_serializer(
        name='AddToCartSingleRequest',
        fields={
            'item_id': serializers.IntegerField(required=False),
            'media_id': serializers.IntegerField(required=False),
            'book_id': serializers.IntegerField(required=False),
            'category': serializers.CharField(default='books', required=False),
        }
    ),
    responses={
        200: inline_serializer(
            name='AddToCartSingleResponse',
            fields={
                'status': serializers.CharField(),
                'message': serializers.CharField(),
                'cart_count': serializers.IntegerField()
            }
        ),
        400: inline_serializer(
            name='AddToCartSingleErrorResponse',
            fields={
                'status': serializers.CharField(),
                'message': serializers.CharField()
            }
        )
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_cart_single(request, book_id=None):
    data = request.data or {}
    item_id = data.get('item_id') or data.get('media_id') or data.get('book_id') or book_id
    category = data.get('category', 'books')

    if not item_id:
        return JsonResponse({'status': 'error', 'message': 'Missing item ID.'}, status=400)

    media_obj, lookup_kwargs = resolve_media_object(category, item_id)

    if check_already_purchased(request.user, media_obj):
        return JsonResponse({
            "status": "error",
            "message": f"You already own '{media_obj.title}'."
        }, status=400)

    filter_kwargs = {k: v for k, v in lookup_kwargs.items() if v is not None}
    filter_kwargs['student'] = request.user

    cart_item, created = CartItem.objects.get_or_create(**filter_kwargs)
    cart_count = CartItem.objects.filter(student=request.user).count()

    msg = f"'{media_obj.title}' added to cart." if created else f"'{media_obj.title}' is already in your cart."

    return JsonResponse({
        'status': 'success' if created else 'info',
        'message': msg,
        'cart_count': cart_count
    })


@extend_schema(
    summary="Bulk add books to cart",
    description="Adds multiple books to the authenticated student's cart at once.",
    request=inline_serializer(
        name='AddToCartBulkRequest',
        fields={
            'book_ids': serializers.ListField(child=serializers.IntegerField())
        }
    ),
    responses={
        200: inline_serializer(
            name='AddToCartBulkResponse',
            fields={
                'status': serializers.CharField(),
                'message': serializers.CharField(),
                'cart_count': serializers.IntegerField()
            }
        ),
        400: inline_serializer(
            name='AddToCartBulkErrorResponse',
            fields={
                'status': serializers.CharField(),
                'message': serializers.CharField()
            }
        ),
        429: inline_serializer(
            name='AddToCartBulkRateLimitResponse',
            fields={
                'status': serializers.CharField(),
                'message': serializers.CharField()
            }
        )
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@ratelimit(key='user_or_ip', rate='10/m', block=False)
def add_to_cart_bulk(request):
    if getattr(request, 'limited', False):
        return JsonResponse({
            "status": "error",
            "message": "Too many requests. Please slow down and try again in a minute."
        }, status=429)

    try:
        book_ids = request.data.get("book_ids", [])

        if not isinstance(book_ids, list) or not book_ids:
            return JsonResponse({
                "status": "error", 
                "message": "No valid book IDs provided."
            }, status=400)

        try:
            target_ids = {int(b_id) for b_id in book_ids}
        except (ValueError, TypeError):
            return JsonResponse({
                "status": "error", 
                "message": "Invalid book ID format."
            }, status=400)

        purchased_ids = set(
            PurchasedBook.objects.filter(
                student=request.user, book__isnull=False
            ).values_list('book_id', flat=True)
        )

        valid_book_ids = target_ids - purchased_ids

        if not valid_book_ids:
            return JsonResponse({
                "status": "error",
                "message": "Selected books are already in your library."
            }, status=400)

        with transaction.atomic():
            existing_cart_ids = set(
                CartItem.objects.filter(
                    student=request.user, 
                    book_id__in=valid_book_ids
                ).values_list('book_id', flat=True)
            )

            new_book_ids = valid_book_ids - existing_cart_ids

            new_items = [
                CartItem(student=request.user, book_id=b_id)
                for b_id in new_book_ids
            ]
            if new_items:
                CartItem.objects.bulk_create(new_items)

        cart_count = CartItem.objects.filter(student=request.user).count()

        return JsonResponse({
            "status": "success",
            "message": f"Added {len(new_book_ids)} new book(s) to cart.",
            "cart_count": cart_count
        })

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@login_required
@role_required(["STUDENT"])
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, student=request.user)
    media_obj = cart_item.book or cart_item.documentary or cart_item.art or cart_item.media_item
    title = media_obj.title if media_obj else "Item"
    cart_item.delete()
    messages.success(request, f'"{title}" was removed from your cart.')
    return redirect('books:cart_detail')


@login_required
@role_required(["STUDENT"])
@require_POST
def clear_cart(request):
    CartItem.objects.filter(student=request.user).delete()
    messages.info(request, "Your cart has been cleared.")
    return redirect('books:cart_detail')


@login_required
@role_required(["STUDENT"])
@ratelimit(key='user', rate='5/m', block=True)
def cart_checkout(request):
    cart_items = CartItem.objects.filter(student=request.user).select_related('book', 'documentary', 'art', 'media_item')

    if not cart_items.exists():
        messages.error(request, "Your cart is currently empty.")
        return redirect('books:book_list')

    total_amount_decimal = Decimal('0.00')
    book_ids = []

    for item in cart_items:
        if item.book:
            price = getattr(item.book, 'price', None) or Decimal('39.00')
            book_ids.append(item.book.id)
        elif item.art:
            price = getattr(item.art, 'price', None) or Decimal('59.00')
        elif item.documentary:
            price = getattr(item.documentary, 'price', None) or Decimal('109.00')
        elif item.media_item:
            price = getattr(item.media_item, 'price', None) or Decimal('39.00')
        else:
            price = Decimal('39.00')
            
        total_amount_decimal += Decimal(str(price))

    item_count = cart_items.count()
    total_amount_subunits = int(total_amount_decimal * 100)

    order_data = {
        "amount": total_amount_subunits,
        "currency": "INR",
        "payment_capture": 1,
        "notes": {
            "student_id": request.user.id,
            "subscription_type": "CART_PURCHASE",
            "book_ids": ",".join(map(str, book_ids)),
            "currency": "INR",
        }
    }
    client = get_razorpay_client()
    order = client.order.create(data=order_data)

    Order.objects.create(
        user=request.user,
        order_id=order['id'],
        base_amount_inr=float(total_amount_decimal),
        charged_amount=float(total_amount_decimal),
        charged_currency='INR',
        status='Pending'
    )
    
    context = {
        "razorpay_order_id": order["id"],
        "razorpay_merchant_key": getattr(settings, 'RAZORPAY_KEY_ID', ''),
        "amount_in_subunits": total_amount_subunits,
        "amount": total_amount_subunits,
        "amount_display": float(total_amount_decimal),
        "currency": "INR",
        "plan": f"Cart Checkout ({item_count} Item{'s' if item_count > 1 else ''})",
        "cart_items": cart_items,
        "callback_url": reverse('books:verify_payment')
    }
    return render(request, 'payments/checkout.html', context)


checkout_cart = cart_checkout


# ==========================================
# --- 3. ROLE-BASED BOOK CRUD ACTIONS ---
# ==========================================

@login_required
@role_required(["SUPERADMIN", "LIBRARIAN", "AUTHOR"])
def add_book(request):
    if request.method == "POST":
        form = BookForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            book = form.save(commit=False)
            book.created_by = request.user
            if not hasattr(book, 'price') or book.price is None:
                book.price = Decimal('39.00')
            book.save()
            messages.success(request, f'Book "{book.title}" added successfully.')
            return redirect("books:book_list")
    else:
        form = BookForm(user=request.user)

    return render(request, "books/book_form.html", {"form": form})


@login_required
@role_required(["SUPERADMIN", "LIBRARIAN", "AUTHOR"])
def edit_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    if request.user.profile.role == "AUTHOR" and book.created_by != request.user:
        messages.error(request, "You are not authorized to edit this book.")
        return redirect("books:book_list")

    if request.method == "POST":
        form = BookForm(request.POST, request.FILES, instance=book, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Book "{book.title}" updated successfully.')
            return redirect("books:book_list")
    else:
        form = BookForm(instance=book, user=request.user)

    return render(request, "books/book_form.html", {"form": form})


@login_required
@role_required(["SUPERADMIN", "LIBRARIAN", "AUTHOR"])
def delete_book(request, id):
    book = get_object_or_404(Book, id=id)

    if request.user.profile.role == "AUTHOR" and book.created_by != request.user:
        messages.error(request, "You are not authorized to delete this book.")
        return redirect("books:book_list")

    if request.method == "POST":
        book_title = book.title
        book.delete()
        messages.success(request, f'Book "{book_title}" was deleted.')
        return redirect("books:book_list")

    return render(request, "books/book_delete.html", {"book": book})


# ==========================================
# --- 4. BORROWING & REQUEST ACTIONS ---
# ==========================================

@login_required
@role_required(["STUDENT"])
def request_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    if BookRequest.objects.filter(student=request.user, book=book, status="PENDING").exists():
        messages.info(request, f'You already have a pending borrowing request for "{book.title}".')
        return redirect("books:book_list")

    BookRequest.objects.create(student=request.user, book=book)
    messages.success(request, f'Borrow request for "{book.title}" submitted successfully.')
    return redirect("books:book_list")


@login_required
@role_required(["STUDENT"])
def cancel_request(request, request_id):
    book_request = get_object_or_404(BookRequest, id=request_id, student=request.user)

    if book_request.status == "PENDING":
        title = book_request.item_title
        book_request.delete()
        messages.success(request, f'Borrow request for "{title}" was successfully cancelled.')
    else:
        messages.error(request, "Only pending requests can be cancelled.")

    return redirect("books:book_list")


@login_required
@role_required(["SUPERADMIN", "LIBRARIAN"])
def book_requests(request):
    search_query = request.GET.get('q', '').strip()
    requests = BookRequest.objects.all().select_related('student', 'book', 'media_item')

    if search_query:
        requests = requests.filter(
            Q(student__username__icontains=search_query) |
            Q(book__title__icontains=search_query) |
            Q(media_item__title__icontains=search_query) |
            Q(status__icontains=search_query)
        )

    return render(request, "books/book_requests.html", {
        "requests": requests,
        "search_query": search_query,
    })


@login_required
@transaction.atomic
@role_required(["SUPERADMIN", "LIBRARIAN"])
def approve_request(request, request_id):
    book_request = get_object_or_404(
        BookRequest.objects.select_for_update(), 
        id=request_id
    )

    if book_request.status != "PENDING":
        messages.error(request, "Cannot approve request. Request is not in PENDING state.")
        return redirect("books:book_requests")

    if book_request.book:
        if book_request.book.quantity > 0:
            Book.objects.filter(id=book_request.book.id).update(quantity=models.F('quantity') - 1)
            book_request.status = "APPROVED"
            book_request.save()
            messages.success(request, f'Request for "{book_request.book.title}" approved.')
        else:
            messages.error(request, f'Cannot approve request. "{book_request.book.title}" is out of stock.')
    elif book_request.media_item:
        if book_request.media_item.quantity > 0:
            MediaItem.objects.filter(id=book_request.media_item.id).update(quantity=models.F('quantity') - 1)
            book_request.status = "APPROVED"
            book_request.save()
            messages.success(request, f'Request for "{book_request.media_item.title}" approved.')
        else:
            messages.error(request, f'Cannot approve request. "{book_request.media_item.title}" is out of stock.')
    else:
        messages.error(request, "Invalid request. Item associated with this request was not found.")

    return redirect("books:book_requests")


@login_required
@role_required(["SUPERADMIN", "LIBRARIAN"])
def reject_request(request, request_id):
    book_request = get_object_or_404(BookRequest, id=request_id)

    if book_request.status == "PENDING":
        book_request.status = "REJECTED"
        book_request.save()
        messages.info(request, f'Request for "{book_request.item_title}" was rejected.')

    return redirect("books:book_requests")


@login_required
@transaction.atomic
@role_required(["SUPERADMIN", "LIBRARIAN"])
def return_book(request, request_id):
    book_request = get_object_or_404(
        BookRequest.objects.select_for_update(), 
        id=request_id
    )

    if book_request.status == "APPROVED":
        if book_request.book:
            Book.objects.filter(id=book_request.book.id).update(quantity=models.F('quantity') + 1)
        elif book_request.media_item:
            MediaItem.objects.filter(id=book_request.media_item.id).update(quantity=models.F('quantity') + 1)
            
        book_request.status = "RETURNED"
        book_request.save()
        messages.success(request, f'"{book_request.item_title}" marked as returned.')
    else:
        messages.error(request, "Only approved requests can be marked as returned.")

    return redirect("books:book_requests")


# ==========================================
# --- 5. SUBSCRIPTIONS & PAYMENT VERIFICATION ---
# ==========================================

@login_required
@role_required(["STUDENT"])
def buy_subscription(request):
    if request.method == "GET":
        return render(request, 'books/subscription.html')

    elif request.method == "POST":
        plan = request.POST.get("plan", "MONTH")
        sub_type = request.POST.get("subscription_type", "LIBRARY")
        currency = request.POST.get("currency", "INR")
        book_ids = request.POST.get("book_ids", "")

        pricing = {
            "WEEK": {"INR": 99, "USD": 2, "EUR": 2, "GBP": 2},
            "MONTH": {"INR": 299, "USD": 6, "EUR": 5, "GBP": 5},
        }

        base_price = float(pricing.get(plan, {}).get(currency, 299))
        amount_in_subunits = int(base_price * 100)

        order_data = {
            "amount": amount_in_subunits,
            "currency": currency,
            "payment_capture": 1,
            "notes": {
                "student_id": request.user.id,
                "plan": plan,
                "subscription_type": sub_type,
                "book_ids": book_ids,
                "currency": currency,
            }
        }
        client = get_razorpay_client()
        order = client.order.create(data=order_data)

        Order.objects.create(
            user=request.user,
            order_id=order['id'],
            base_amount_inr=base_price,
            charged_amount=base_price,
            charged_currency=currency,
            status='Pending'
        )

        context = {
            "razorpay_order_id": order["id"],
            "razorpay_merchant_key": getattr(settings, 'RAZORPAY_KEY_ID', ''),
            "amount_in_subunits": amount_in_subunits,
            "amount": amount_in_subunits,
            "amount_display": base_price,
            "currency": currency,
            "plan": plan,
            "callback_url": reverse('books:verify_payment')
        }
        
        return render(request, 'payments/checkout.html', context)


@csrf_exempt
@ratelimit(key='ip', rate='5/m', block=True)
def verify_payment(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid request method.")

    payment_id = request.POST.get("razorpay_payment_id", "")
    razorpay_order_id = request.POST.get("razorpay_order_id", "")
    signature = request.POST.get("razorpay_signature", "")

    params_dict = {
        "razorpay_order_id": razorpay_order_id,
        "razorpay_payment_id": payment_id,
        "razorpay_signature": signature,
    }

    try:
        client = get_razorpay_client()
        client.utility.verify_payment_signature(params_dict)

        order_obj = Order.objects.filter(order_id=razorpay_order_id).first()
        if order_obj:
            order_obj.payment_id = payment_id
            order_obj.signature = signature
            order_obj.status = 'Success'
            order_obj.save()

        order_details = client.order.fetch(razorpay_order_id)
        notes = order_details.get("notes", {})

        sub_type = notes.get("subscription_type", "LIBRARY")
        currency = notes.get("currency", "INR")
        now = timezone.now()

        divisor = 1 if currency in ["JPY", "KRW"] else 100.0
        amount_paid = order_details.get("amount", 0) / divisor

        if sub_type == "CART_PURCHASE":
            student_id = notes.get("student_id")
            if not student_id:
                return HttpResponseBadRequest("Missing student ID for cart checkout.")

            user = User.objects.get(id=int(student_id))
            cart_items = CartItem.objects.filter(student=user)

            with transaction.atomic():
                for item in cart_items:
                    if item.book:
                        PurchasedBook.objects.get_or_create(
                            student=user,
                            book=item.book,
                            defaults={'amount_paid': getattr(item.book, 'price', None) or Decimal('39.00')}
                        )
                    elif item.art:
                        PurchasedArt.objects.get_or_create(
                            student=user,
                            art=item.art,
                            defaults={'amount_paid': getattr(item.art, 'price', None) or Decimal('59.00')}
                        )
                    elif item.documentary:
                        PurchasedDocumentary.objects.get_or_create(
                            student=user,
                            documentary=item.documentary,
                            defaults={'amount_paid': getattr(item.documentary, 'price', None) or Decimal('109.00')}
                        )
                    elif item.media_item:
                        PurchasedBook.objects.get_or_create(
                            student=user,
                            media_item=item.media_item,
                            defaults={'amount_paid': getattr(item.media_item, 'price', None) or Decimal('39.00')}
                        )
                cart_items.delete()

            messages.success(request, "Payment successful! Items added to your library.")
            return redirect("books:book_list")

        elif sub_type == "GIFT_PURCHASE":
            sender_id = notes.get("sender_id")
            book_id = notes.get("book_id")
            recipient_email = notes.get("recipient_email", "").strip().lower()
            gift_msg = notes.get("gift_message", "")

            if not recipient_email or not book_id:
                return HttpResponseBadRequest("Missing gift recipient or book parameters.")

            book_obj = get_object_or_404(Book, id=int(book_id))
            recipient_user = User.objects.filter(email__iexact=recipient_email).first()

            if recipient_user:
                PurchasedBook.objects.get_or_create(
                    student=recipient_user,
                    book=book_obj,
                    defaults={'amount_paid': amount_paid}
                )
                messages.success(
                    request, 
                    f'Gift sent successfully! "{book_obj.title}" was added directly to {recipient_email}\'s library.'
                )
            else:
                pending_gift = PendingGift.objects.create(
                    sender_id=int(sender_id),
                    recipient_email=recipient_email,
                    book=book_obj,
                    message=gift_msg
                )
                send_gift_invitation_email(request, pending_gift)
                
                messages.success(
                    request, 
                    f'Gift purchased! An email invitation has been sent to {recipient_email}. They will receive "{book_obj.title}" upon signup.'
                )

            return redirect("books:book_list")

        else:
            student_id = notes.get("student_id")
            plan = notes.get("plan", "MONTH")
            book_ids_str = notes.get("book_ids", "")

            if not student_id:
                return HttpResponseBadRequest("Missing student ID in payment metadata.")

            days_map = {"WEEK": 7, "TWOWEEK": 14, "MONTH": 30}
            days_to_add = days_map.get(plan, 30)

            if sub_type == "BOOK" and book_ids_str:
                book_ids = [b for b in book_ids_str.split(",") if b]
                split_amount = amount_paid / len(book_ids)
                
                with transaction.atomic():
                    for b_id in book_ids:
                        book_obj = get_object_or_404(Book, id=int(b_id))
                        existing_sub = BookSubscription.objects.filter(
                            student_id=int(student_id),
                            book=book_obj
                        ).first()

                        if existing_sub and existing_sub.end_date and existing_sub.end_date > now.date():
                            existing_sub.end_date = existing_sub.end_date + timedelta(days=days_to_add)
                            existing_sub.amount = float(existing_sub.amount) + float(split_amount)
                            existing_sub.plan = plan
                            existing_sub.is_active = True
                            existing_sub.save()
                        else:
                            BookSubscription.objects.create(
                                student_id=int(student_id),
                                book=book_obj,
                                plan=plan,
                                amount=split_amount,
                                end_date=now.date() + timedelta(days=days_to_add),
                                is_active=True
                            )
            else:
                with transaction.atomic():
                    existing_lib_sub = LibrarySubscription.objects.filter(student_id=int(student_id)).first()

                    if existing_lib_sub and existing_lib_sub.end_date and existing_lib_sub.end_date > now.date():
                        existing_lib_sub.end_date = existing_lib_sub.end_date + timedelta(days=days_to_add)
                        existing_lib_sub.amount = float(existing_lib_sub.amount) + float(amount_paid)
                        existing_lib_sub.plan = plan
                        existing_lib_sub.is_active = True
                        existing_lib_sub.save()
                    else:
                        LibrarySubscription.objects.create(
                            student_id=int(student_id),
                            plan=plan,
                            amount=amount_paid,
                            end_date=now.date() + timedelta(days=days_to_add),
                            is_active=True
                        )

            messages.success(request, f"Subscription plan ({plan}) activated successfully!")
            return redirect("books:my_subscription")

    except razorpay.errors.SignatureVerificationError:
        if order_obj:
            order_obj.status = 'Failed'
            order_obj.save()
        return HttpResponseBadRequest("Invalid Razorpay Payment Signature.")
    except Exception as e:
        return HttpResponseBadRequest(f"Error processing payment: {str(e)}")


@login_required
@role_required(["STUDENT"])
def my_subscription(request):
    search_query = request.GET.get('q', '').strip()

    library_sub = LibrarySubscription.objects.filter(
        student=request.user
    ).order_by('-start_date', '-id').first()

    book_subs = BookSubscription.objects.filter(
        student=request.user,
        is_active=True
    ).select_related('book')

    purchased_books = PurchasedBook.objects.filter(
        student=request.user
    ).select_related('book')

    if search_query:
        book_subs = book_subs.filter(
            Q(book__title__icontains=search_query) |
            Q(book__author__icontains=search_query)
        )
        purchased_books = purchased_books.filter(
            Q(book__title__icontains=search_query) |
            Q(book__author__icontains=search_query)
        )

    return render(request, "books/my_subscription.html", {
        "subscription": library_sub,
        "book_subscriptions": book_subs,
        "purchased_books": purchased_books,
        "search_query": search_query,
    })


# ==========================================
# --- 6. GIFTING FLOW & HELPER FUNCTIONS ---
# ==========================================

@login_required
@role_required(["STUDENT"])
def gift_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    if request.method == "POST":
        recipient_email = request.POST.get("recipient_email", "").strip().lower()
        gift_message = request.POST.get("message", "")

        if not recipient_email:
            messages.error(request, "Please provide a valid recipient email address.")
            return redirect('books:gift_book', book_id=book.id)

        price_decimal = getattr(book, 'price', None) or Decimal('39.00')
        amount_in_subunits = int(price_decimal * 100)

        order_data = {
            "amount": amount_in_subunits,
            "currency": "INR",
            "payment_capture": 1,
            "notes": {
                "sender_id": request.user.id,
                "subscription_type": "GIFT_PURCHASE",
                "book_id": book.id,
                "recipient_email": recipient_email,
                "gift_message": gift_message,
            }
        }
        client = get_razorpay_client()
        order = client.order.create(data=order_data)

        Order.objects.create(
            user=request.user,
            order_id=order['id'],
            base_amount_inr=float(price_decimal),
            charged_amount=float(price_decimal),
            charged_currency='INR',
            status='Pending'
        )

        context = {
            "razorpay_order_id": order["id"],
            "razorpay_merchant_key": getattr(settings, 'RAZORPAY_KEY_ID', ''),
            "amount_in_subunits": amount_in_subunits,
            "amount": amount_in_subunits,
            "amount_display": float(price_decimal),
            "currency": "INR",
            "plan": f"Gift '{book.title}' to {recipient_email}",
            "callback_url": reverse('books:verify_payment')
        }
        return render(request, 'payments/checkout.html', context)

    return render(request, 'books/gift_form.html', {'book': book})


def send_gift_invitation_email(request, pending_gift):
    signup_path = reverse('register')
    signup_url = request.build_absolute_uri(f"{signup_path}?email={pending_gift.recipient_email}")

    context = {
        'sender': pending_gift.sender,
        'book': pending_gift.book,
        'message': pending_gift.message,
        'recipient_email': pending_gift.recipient_email,
        'signup_url': signup_url,
    }

    html_content = render_to_string('emails/gift_invitation.html', context)
    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(
        subject=f"🎁 {pending_gift.sender.username} sent you a book: '{pending_gift.book.title}'",
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[pending_gift.recipient_email],
    )
    email.attach_alternative(html_content, "text/html")
    email.send(fail_silently=True)


@receiver(post_save, sender=User)
def claim_pending_gifts_on_signup(sender, instance, created, **kwargs):
    if created:
        unclaimed_gifts = PendingGift.objects.filter(
            recipient_email__iexact=instance.email, 
            is_claimed=False
        )
        
        for gift in unclaimed_gifts:
            gift_price = getattr(gift.book, 'price', None) or Decimal('39.00')
            PurchasedBook.objects.get_or_create(
                student=instance,
                book=gift.book,
                defaults={'amount_paid': gift_price}
            )
            gift.is_claimed = True
            gift.save()


# ==========================================
# --- 7. SECURE PDF & MEDIA STREAMING ---
# ==========================================

@login_required
@role_required(["STUDENT", "SUPERADMIN", "LIBRARIAN", "AUTHOR"])
def read_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    if not book.book_file:
        messages.warning(request, f'"{book.title}" does not have a digital PDF available for reading yet.')
        return redirect('books:book_detail', book_id=book.id)

    view_field = next((vf for vf in ['views', 'views_count', 'view_count', 'click_count'] if hasattr(Book, vf)), None)

    def increment_view_count():
        if view_field:
            Book.objects.filter(id=book.id).update(**{view_field: F(view_field) + 1})

    if request.user.is_staff or (hasattr(request.user, 'profile') and request.user.profile.role in ["SUPERADMIN", "LIBRARIAN"]) or book.created_by == request.user:
        increment_view_count()
        return FileResponse(book.book_file.open("rb"), content_type="application/pdf")

    is_purchased = PurchasedBook.objects.filter(student=request.user, book=book).exists()
    if is_purchased:
        increment_view_count()
        return FileResponse(book.book_file.open("rb"), content_type="application/pdf")

    approved = BookRequest.objects.filter(
        student=request.user,
        book=book,
        status="APPROVED"
    ).exists()
    if approved:
        increment_view_count()
        return FileResponse(book.book_file.open("rb"), content_type="application/pdf")

    today = timezone.now().date()
    has_library_sub = LibrarySubscription.objects.filter(
        student=request.user,
        is_active=True,
        end_date__gte=today
    ).exists()

    if has_library_sub:
        increment_view_count()
        return FileResponse(book.book_file.open("rb"), content_type="application/pdf")

    messages.error(request, "You do not have permission or an active subscription to read this book.")
    return redirect('books:book_detail', book_id=book.id)


@login_required
def stream_book_pdf(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    if not book.book_file:
        return HttpResponseForbidden("PDF file not found.")

    file_handle = book.book_file.open('rb')
    content_type, _ = mimetypes.guess_type(book.book_file.name)
    content_type = content_type or 'application/pdf'

    response = FileResponse(file_handle, content_type=content_type)
    response['Content-Disposition'] = f'inline; filename="{os.path.basename(book.book_file.name)}"'
    return response


@login_required
def stream_documentary(request, pk):
    doc = get_object_or_404(Documentary, id=pk)

    file_handle = doc.file.open('rb')
    content_type, _ = mimetypes.guess_type(doc.file.name)
    content_type = content_type or 'application/octet-stream'

    response = FileResponse(file_handle, content_type=content_type)
    response['Content-Disposition'] = f'inline; filename="{os.path.basename(doc.file.name)}"'
    return response


@login_required
def stream_art(request, pk):
    art = get_object_or_404(Art, id=pk)

    if not user_has_purchased(request.user, art_obj=art):
        messages.error(request, "You must purchase this artwork before viewing/downloading it.")
        return redirect('books:art_detail', pk=pk)

    file_handle = art.image.open('rb')
    content_type, _ = mimetypes.guess_type(art.image.name)
    content_type = content_type or 'image/jpeg'

    response = FileResponse(file_handle, content_type=content_type)
    response['Content-Disposition'] = f'inline; filename="{os.path.basename(art.image.name)}"'
    return response


@login_required
def art_detail(request, pk):
    art = get_object_or_404(Art, id=pk)
    has_access = user_has_purchased(request.user, art_obj=art)

    return render(request, 'books/art_detail.html', {
        'art': art,
        'is_purchased': has_access
    })


# ==========================================
# --- 8. API & MEDIA ENDPOINTS ---
# ==========================================

@extend_schema(
    # operation_id="books_list_datatable_v1",  # Unique operation ID resolves drf_spectacular.W001
    summary="List books for DataTables",
    description="Server-side DataTables API endpoint for listing books.",
    parameters=[
        OpenApiParameter(name='draw', type=int, description='DataTables request counter'),
        OpenApiParameter(name='start', type=int, description='Paging first record indicator'),
        OpenApiParameter(name='length', type=int, description='Number of records to show'),
        OpenApiParameter(name='search[value]', type=str, description='Global search string'),
    ],
    responses={
        200: inline_serializer(
            name='BookDataTablesResponse',
            fields={
                'draw': serializers.IntegerField(),
                'recordsTotal': serializers.IntegerField(),
                'recordsFiltered': serializers.IntegerField(),
                'data': BookSerializer(many=True)
            }
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def book_list_api(request):
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '').strip()

    queryset = Book.objects.all().order_by('id')
    records_total = queryset.count()

    if search_value:
        queryset = queryset.filter(
            Q(title__icontains=search_value) | Q(author__icontains=search_value)
        )

    records_filtered = queryset.count()

    if length > 0:
        books_page = queryset[start:start + length]
    else:
        books_page = queryset[start:]

    purchased_book_ids = set()
    cart_book_ids = set()

    if request.user.is_authenticated:
        purchased_book_ids = set(
            PurchasedBook.objects.filter(student=request.user, book__isnull=False).values_list('book_id', flat=True)
        )
        cart_book_ids = set(
            CartItem.objects.filter(student=request.user, book__isnull=False).values_list('book_id', flat=True)
        )

    data = []
    for book in books_page:
        is_purchased = book.id in purchased_book_ids
        in_cart = book.id in cart_book_ids

        if is_purchased:
            status_str = "Purchased"
        elif in_cart:
            status_str = "In Cart"
        else:
            status_str = "Available"

        data.append({
            'id': book.id,
            'title': book.title,
            'author': book.author,
            'price': str(book.price) if getattr(book, 'price', None) is not None else "39.00",
            'is_purchased': is_purchased,
            'in_cart': in_cart,
            'status': status_str,
        })

    return JsonResponse({
        'draw': draw,
        'recordsTotal': records_total,
        'recordsFiltered': records_filtered,
        'data': data,
    })


def media_page_view(request):
    today = timezone.now().date()

    total_books = Book.objects.count()
    total_members = User.objects.filter(is_active=True).count()
    issued_books = BookRequest.objects.filter(status='APPROVED').count()
    active_passes = LibrarySubscription.objects.filter(
        is_active=True,
        end_date__gte=today
    ).count()

    context = {
        'total_books': total_books,
        'total_members': total_members,
        'issued_books': issued_books,
        'active_passes': active_passes,
    }

    return render(request, 'books/media.html', context)


@extend_schema(
    operation_id="books_read_detail",
    summary="Get book detail",
    description="Retrieves single book detail properties in JSON format.",
    responses={
        200: inline_serializer(
            name='BookDetailApiResponse',
            fields={
                'id': serializers.IntegerField(),
                'title': serializers.CharField(),
                'author': serializers.CharField(),
                'price': serializers.CharField(),
                'quantity': serializers.IntegerField(),
                'views': serializers.IntegerField(),
            }
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def book_detail_api(request, pk):
    book = get_object_or_404(Book, id=pk)
    data = {
        'id': book.id,
        'title': book.title,
        'author': book.author,
        'price': str(book.price) if getattr(book, 'price', None) is not None else "39.00",
        'quantity': getattr(book, 'quantity', 0),
        'views': getattr(book, 'views', 0),
    }
    return JsonResponse(data)


@login_required
def add_media(request):
    user_role = getattr(getattr(request.user, 'profile', None), 'role', '')
    if not (request.user.is_superuser or user_role in ['SUPERADMIN', 'LIBRARIAN', 'AUTHOR']):
        messages.error(request, "Permission denied. Only Librarians and Authors can add media items.")
        return redirect('books:book_list')

    if request.method == 'POST':
        form = MediaItemForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            media = form.save(commit=False)
            media.created_by = request.user
            media.save()

            category_label = f"{media.get_category_display() if hasattr(media, 'get_category_display') else media.category.title()} (₹{getattr(media, 'price', '39.00')})"

            messages.success(request, f'"{media.title}" uploaded successfully to {category_label}!')
            return redirect('books:book_list')
        else:
            messages.error(request, "Please correct the errors in the form below.")
    else:
        form = MediaItemForm(user=request.user)

    return render(request, 'books/add_media.html', {'form': form})


def media_by_category(request, category_name):
    items = MediaItem.objects.filter(category=category_name)
    return render(request, 'books/category_list.html', {'items': items, 'category': category_name})


def media_catalog_api(request):
    category = request.GET.get('category', '').lower().strip()
    search = request.GET.get('search', '').strip()

    data = []

    media_items = MediaItem.objects.all().order_by('-created_at')

    if category:
        media_items = media_items.filter(category=category)

    if search:
        media_items = media_items.filter(
            title__icontains=search
        ) | media_items.filter(
            creator__icontains=search
        )

    for item in media_items:
        ext = item.file.name.split('.')[-1].lower() if item.file else ''
        
        is_purchased = user_has_purchased(request.user, media_obj=item)

        data.append({
            'id': item.id,
            'title': item.title,
            'creator': getattr(item, 'creator', '') or getattr(item, 'author', ''),
            'category': item.get_category_display() if hasattr(item, 'get_category_display') else item.category.title(),
            'price': str(getattr(item, 'price', '39.00')),
            'file_url': item.file.url if item.file else '#',
            'stream_url': item.file.url if item.file else '#',
            'file_extension': ext,
            'type': 'image' if item.is_image() else ('video' if item.is_video() else 'pdf'),
            'is_image': item.is_image(),
            'is_video': item.is_video(),
            'is_document': item.is_document(),
            'is_purchased': is_purchased,
            'source_model': 'media_item'
        })

    if category in ['', 'books']:
        books = Book.objects.all()

        if search:
            books = books.filter(title__icontains=search) | books.filter(author__icontains=search)

        for book in books:
            is_purchased = user_has_purchased(request.user, media_obj=book)

            file_url = '#'
            if hasattr(book, 'file') and book.file:
                file_url = book.file.url
            elif hasattr(book, 'pdf') and book.pdf:
                file_url = book.pdf.url

            data.append({
                'id': book.id,
                'title': book.title,
                'creator': getattr(book, 'author', 'Unknown Author'),
                'category': 'Books',
                'price': str(getattr(book, 'price', '39.00')),
                'file_url': file_url,
                'stream_url': file_url,
                'file_extension': 'pdf',
                'type': 'pdf',
                'is_image': False,
                'is_video': False,
                'is_document': True,
                'is_purchased': is_purchased,
                'source_model': 'book'
            })

    return JsonResponse(data, safe=False)