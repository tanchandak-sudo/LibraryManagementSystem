from django.contrib import admin
from .models import (
    Book,
    MediaItem,
    BookRequest,
    LibrarySubscription,
    BookSubscription,
    PurchasedBook,
    PendingGift,
    Documentary,
    Art,
    CartItem,
    PurchasedArt,
    PurchasedDocumentary
)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'price', 'quantity', 'views')
    search_fields = ('title', 'author')
    list_filter = ('created_by',)


@admin.register(MediaItem)
class MediaItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'creator', 'category', 'price', 'quantity', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('title', 'creator')


@admin.register(BookRequest)
class BookRequestAdmin(admin.ModelAdmin):
    list_display = ('student', 'item_title', 'item_type', 'status', 'requested_at')
    list_filter = ('status', 'requested_at')
    search_fields = ('student__username', 'book__title', 'media_item__title')


@admin.register(LibrarySubscription)
class LibrarySubscriptionAdmin(admin.ModelAdmin):
    list_display = ('student', 'plan', 'amount', 'start_date', 'end_date', 'is_active')
    list_filter = ('plan', 'is_active', 'start_date')
    search_fields = ('student__username',)


@admin.register(BookSubscription)
class BookSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('student', 'plan', 'amount', 'start_date', 'end_date', 'is_active')
    list_filter = ('plan', 'is_active', 'start_date')
    search_fields = ('student__username',)


@admin.register(PurchasedBook)
class PurchasedBookAdmin(admin.ModelAdmin):
    list_display = ('student', 'book', 'media_item', 'amount_paid', 'purchased_at')
    list_filter = ('purchased_at',)
    search_fields = ('student__username', 'book__title', 'media_item__title')


@admin.register(PendingGift)
class PendingGiftAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient_email', 'token', 'is_claimed', 'created_at')
    list_filter = ('is_claimed', 'created_at')
    search_fields = ('sender__username', 'recipient_email')


@admin.register(Documentary)
class DocumentaryAdmin(admin.ModelAdmin):
    list_display = ('title', 'director_or_author', 'price', 'created_by', 'created_at')
    search_fields = ('title', 'director_or_author')


@admin.register(Art)
class ArtAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'price', 'created_by', 'created_at')
    search_fields = ('title', 'artist')


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('student', 'book', 'media_item', 'documentary', 'art', 'created_at')
    search_fields = ('student__username',)


@admin.register(PurchasedArt)
class PurchasedArtAdmin(admin.ModelAdmin):
    list_display = ('student', 'art', 'purchased_at')
    search_fields = ('student__username', 'art__title')


@admin.register(PurchasedDocumentary)
class PurchasedDocumentaryAdmin(admin.ModelAdmin):
    list_display = ('student', 'documentary', 'purchased_at')
    search_fields = ('student__username', 'documentary__title')