from django.contrib import admin
from .models import Book, BookRequest, LibrarySubscription, BookSubscription

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'quantity', 'price', 'created_by')
    search_fields = ('title', 'author', 'created_by__username')
    list_filter = ('created_by',)

@admin.register(BookRequest)
class BookRequestAdmin(admin.ModelAdmin):
    list_display = ('student', 'book', 'status', 'requested_at')
    list_filter = ('status', 'requested_at')
    search_fields = ('student__username', 'book__title')

@admin.register(LibrarySubscription)
class LibrarySubscriptionAdmin(admin.ModelAdmin):
    list_display = ('student', 'plan', 'amount', 'start_date', 'end_date', 'is_active')
    list_filter = ('plan', 'is_active')
    search_fields = ('student__username',)

@admin.register(BookSubscription)
class BookSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('student', 'book', 'plan', 'amount', 'start_date', 'end_date', 'is_active')
    list_filter = ('plan', 'is_active')
    search_fields = ('student__username', 'book__title')

from .models import Book, Documentary, Art  # Import your new models

@admin.register(Documentary)
class DocumentaryAdmin(admin.ModelAdmin):
    list_display = ('title', 'director_or_author', 'price', 'created_at')
    search_fields = ('title', 'director_or_author')

@admin.register(Art)
class ArtAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'price', 'created_at')
    search_fields = ('title', 'artist')