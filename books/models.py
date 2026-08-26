import os
import uuid
from decimal import Decimal
from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.utils import timezone

User = get_user_model()


class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(default=1)
    book_file = models.FileField(upload_to='books/pdfs/', null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=39.00, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_books', null=True, blank=True)
    pdf = models.FileField(upload_to='books/', null=True, blank=True)
    views = models.PositiveIntegerField(default=0)


    def __str__(self):
        return self.title


class MediaItem(models.Model):
    CATEGORY_CHOICES = [
        ('books', 'Book'),
        ('documentary', 'Documentary'),
        ('arts', 'Art Section'),
    ]

    title = models.CharField(max_length=200)
    creator = models.CharField(max_length=200, help_text="Author, Director, or Artist name")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='books')
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=39.00)
    file = models.FileField(upload_to='media_files/')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_media', null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        if not self.pk:
            if self.category == 'arts':
                self.price = Decimal('59.00')
            elif self.category == 'documentary':
                self.price = Decimal('109.00')
            else:
                self.price = Decimal('39.00')

        super().save(*args, **kwargs)

    def is_image(self):
        ext = os.path.splitext(self.file.name)[1].lower() if self.file else ''
        return ext in ['.jpg', '.jpeg', '.png', '.webp', '.svg', '.gif']

    def is_video(self):
        ext = os.path.splitext(self.file.name)[1].lower() if self.file else ''
        return ext in ['.mp4', '.mkv', '.avi', '.webm', '.mov']

    def is_document(self):
        ext = os.path.splitext(self.file.name)[1].lower() if self.file else ''
        return ext in ['.pdf', '.epub']

    def __str__(self):
        return f"{self.title} ({self.get_category_display()}) - ₹{self.price}"


class BookRequest(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('RETURNED', 'Returned'),
    )

    student = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, null=True, blank=True)
    media_item = models.ForeignKey(MediaItem, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    requested_at = models.DateTimeField(default=timezone.now)

    @property
    def item_title(self):
        if self.book:
            return self.book.title
        if self.media_item:
            return self.media_item.title
        return "Unknown Item"

    @property
    def item_type(self):
        if self.book:
            return "Book"
        if self.media_item:
            return self.media_item.get_category_display()
        return "Item"

    def __str__(self):
        return f"{self.student.username} - {self.item_title} ({self.status})"


class LibrarySubscription(models.Model):
    PLAN_CHOICES = (
        ('WEEK', 'Weekly'),
        ('TWOWEEK', 'Two Weeks'),
        ('MONTH', 'Monthly'),
    )

    student = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.student.username} - Library ({self.plan})"


class BookSubscription(models.Model):
    PLAN_CHOICES = (
        ('WEEK', 'Weekly'),
        ('TWOWEEK', 'Two Weeks'),
        ('MONTH', 'Monthly'),
    )

    student = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, null=True, blank=True)
    media_item = models.ForeignKey(MediaItem, on_delete=models.CASCADE, null=True, blank=True)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        item_title = self.book.title if self.book else (self.media_item.title if self.media_item else "Item")
        return f"{self.student.username} - {item_title} ({self.plan})"


class PurchasedBook(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='purchased_books')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, null=True, blank=True)
    media_item = models.ForeignKey(MediaItem, on_delete=models.CASCADE, null=True, blank=True)
    purchased_at = models.DateTimeField(default=timezone.now)
    amount_paid = models.DecimalField(max_digits=8, decimal_places=2, default=39.00)

    class Meta:
        verbose_name = "Purchased Media/Book"
        verbose_name_plural = "Purchased Media/Books"

    def __str__(self):
        item_title = self.book.title if self.book else (self.media_item.title if self.media_item else "Purchased Item")
        return f"{self.student.username} bought {item_title}"


class PendingGift(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_gifts')
    recipient_email = models.EmailField()
    book = models.ForeignKey(Book, on_delete=models.CASCADE, null=True, blank=True)
    media_item = models.ForeignKey(MediaItem, on_delete=models.CASCADE, null=True, blank=True)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    message = models.TextField(blank=True, null=True)
    is_claimed = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        item_title = self.book.title if self.book else (self.media_item.title if self.media_item else "Gift Item")
        return f"Gift: {item_title} from {self.sender.username} to {self.recipient_email}"


class Documentary(models.Model):
    title = models.CharField(max_length=255)
    director_or_author = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    
    file = models.FileField(
        upload_to='documentaries/',
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'mp4', 'mkv', 'avi', 'webm']
            )
        ]
    )
    price = models.DecimalField(max_digits=10, decimal_places=2, default=109.00)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)

    def is_pdf(self):
        ext = os.path.splitext(self.file.name)[1].lower() if self.file else ''
        return ext == '.pdf'

    def is_video(self):
        ext = os.path.splitext(self.file.name)[1].lower() if self.file else ''
        return ext in ['.mp4', '.mkv', '.avi', '.webm']

    def __str__(self):
        return f"[Documentary] {self.title}"


class Art(models.Model):
    title = models.CharField(max_length=255)
    artist = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    
    image = models.ImageField(
        upload_to='artworks/',
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'webp', 'svg']
            )
        ]
    )
    price = models.DecimalField(max_digits=10, decimal_places=2, default=59.00)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"[Art] {self.title}"


class CartItem(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='cart_items'
    )
    book = models.ForeignKey(
        Book, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    media_item = models.ForeignKey(
        MediaItem,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    documentary = models.ForeignKey(
        Documentary, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    art = models.ForeignKey(
        Art, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        item = self.media_item or self.book or self.documentary or self.art
        title = item.title if item else "Unknown Item"
        return f"{self.student.username}'s Cart - {title}"


class PurchasedArt(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='purchased_arts')
    art = models.ForeignKey(Art, on_delete=models.CASCADE)
    purchased_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'art')

    def __str__(self):
        return f"{self.student} - {self.art.title}"


class PurchasedDocumentary(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='purchased_documentaries')
    documentary = models.ForeignKey(Documentary, on_delete=models.CASCADE)
    purchased_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'documentary')

    def __str__(self):
        return f"{self.student} - {self.documentary.title}"