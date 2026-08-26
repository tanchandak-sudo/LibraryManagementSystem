import json
import razorpay
import hmac
import hashlib
from datetime import timedelta

from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseBadRequest, JsonResponse
from django.utils import timezone
from django.conf import settings
from django.db import transaction

from .models import Order
from .utils import convert_currency
from books.models import LibrarySubscription, BookSubscription, Book, PurchasedBook, CartItem


def initiate_payment(request):
    """
    Handles dynamic currency conversion, Razorpay Order creation,
    and renders checkout context.
    """
    amount_str = request.GET.get('amount', '299')
    target_currency = request.GET.get('currency', 'INR').upper()
    plan = request.GET.get('plan', 'MONTH')
    sub_type = request.GET.get('type', 'LIBRARY')
    book_id = request.GET.get('book_id', '')

    try:
        base_amount_inr = float(amount_str)
    except ValueError:
        base_amount_inr = 299.0

    charged_amount, amount_in_subunits = convert_currency(base_amount_inr, target_currency)

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    razorpay_order = client.order.create({
        "amount": amount_in_subunits,
        "currency": target_currency,
        "payment_capture": 1
    })

    # Save initial pending order to database
    Order.objects.create(
        user=request.user if request.user.is_authenticated else None,
        order_id=razorpay_order['id'],
        base_amount_inr=base_amount_inr,
        charged_amount=charged_amount,
        charged_currency=target_currency,
        status='Pending'
    )

    context = {
        'razorpay_order_id': razorpay_order['id'],
        'razorpay_merchant_key': settings.RAZORPAY_KEY_ID,
        'base_amount_inr': base_amount_inr,
        'charged_amount': float(charged_amount),
        'amount_display': base_amount_inr,
        'amount_in_subunits': amount_in_subunits,
        'currency': target_currency,
        'plan': plan,
        'type': sub_type,
        'book_id': book_id,
        'callback_url': f"/payments/callback/?plan={plan}&type={sub_type}&book_id={book_id}"
    }

    return render(request, 'payments/checkout.html', context)


@csrf_exempt
def payment_callback(request):
    """
    Verifies Razorpay HMAC signature and handles user access extensions.
    """
    if request.method == "POST":
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                data = {}
        else:
            data = request.POST

        order_id = data.get('razorpay_order_id', '')
        payment_id = data.get('razorpay_payment_id', '')
        received_signature = data.get('razorpay_signature', '')

        if not order_id or not payment_id or not received_signature:
            return HttpResponseBadRequest("Missing payment parameters.")

        order = get_object_or_404(Order, order_id=order_id)

        msg = f"{order_id}|{payment_id}".encode('utf-8')
        secret = settings.RAZORPAY_KEY_SECRET.encode('utf-8')
        generated_signature = hmac.new(secret, msg, hashlib.sha256).hexdigest()

        if hmac.compare_digest(generated_signature, received_signature):
            with transaction.atomic():
                order.payment_id = payment_id
                order.signature = received_signature
                order.status = 'Success'
                order.save(update_fields=['payment_id', 'signature', 'status'])

                today = timezone.now().date()
                sub_type = request.GET.get('type', 'LIBRARY')
                plan = request.GET.get('plan', 'MONTH')
                book_id_str = request.GET.get('book_id', '')

                days_map = {'WEEK': 7, 'TWOWEEK': 14, 'MONTH': 30}
                added_days = days_map.get(plan, 30)

                user = order.user or (request.user if request.user.is_authenticated else None)

                if user:
                    if sub_type == 'BOOK' and book_id_str:
                        book_ids = [b.strip() for b in book_id_str.split(',') if b.strip()]
                        per_book_amount = order.base_amount_inr / len(book_ids) if book_ids else order.base_amount_inr

                        for b_id in book_ids:
                            book = get_object_or_404(Book, id=b_id)
                            PurchasedBook.objects.get_or_create(
                                student=user,
                                book=book,
                                defaults={'amount_paid': per_book_amount}
                            )
                            existing_book_sub = BookSubscription.objects.filter(
                                student=user,
                                book=book,
                                is_active=True
                            ).first()

                            if existing_book_sub:
                                base_date = existing_book_sub.end_date if existing_book_sub.end_date >= today else today
                                existing_book_sub.end_date = base_date + timedelta(days=added_days)
                                existing_book_sub.plan = plan
                                existing_book_sub.amount = per_book_amount
                                existing_book_sub.save()
                            else:
                                BookSubscription.objects.create(
                                    student=user,
                                    book=book,
                                    plan=plan,
                                    amount=per_book_amount,
                                    start_date=today,
                                    end_date=today + timedelta(days=added_days),
                                    is_active=True
                                )

                        # Clean up user cart upon success
                        CartItem.objects.filter(student=user).delete()

                    else:
                        existing_lib_sub = LibrarySubscription.objects.filter(
                            student=user,
                            is_active=True
                        ).first()

                        if existing_lib_sub:
                            base_date = existing_lib_sub.end_date if existing_lib_sub.end_date >= today else today
                            existing_lib_sub.end_date = base_date + timedelta(days=added_days)
                            existing_lib_sub.plan = plan
                            existing_lib_sub.amount = order.base_amount_inr
                            existing_lib_sub.save()
                        else:
                            LibrarySubscription.objects.create(
                                student=user,
                                plan=plan,
                                amount=order.base_amount_inr,
                                start_date=today,
                                end_date=today + timedelta(days=added_days),
                                is_active=True
                            )

            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({'status': 'success', 'redirect_url': '/payments/success/'})

            return render(request, 'payments/payment_success.html', {'order': order})
        else:
            order.status = 'Failed'
            order.save(update_fields=['status'])
            retry_url = f"/payments/checkout/?amount={order.base_amount_inr}&currency={order.charged_currency}"

            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({'status': 'failed', 'retry_url': retry_url}, status=400)

            return render(request, 'payments/payment_failed.html', {'order': order, 'retry_url': retry_url}, status=400)

    return HttpResponseBadRequest("Invalid request method")

def payment_success(request):
    """
    Renders the success page after a successful AJAX payment redirect.
    """
    return render(request, 'payments/payment_success.html')