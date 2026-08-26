from django import forms
from .models import Book, MediaItem


class BookForm(forms.ModelForm):
    # Set default quantity on the form field level
    quantity = forms.IntegerField(
        initial=1,
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control', 
            'value': 1, 
            'min': 1
        })
    )

    class Meta:
        model = Book
        fields = ['title', 'author', 'quantity', 'book_file', 'price']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter book title'}),
            'author': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter author name'}),
            'book_file': forms.FileInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '39.00'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(BookForm, self).__init__(*args, **kwargs)

        # Ensure initial value stays 1 if not bound to an instance or data
        if not self.is_bound and not self.instance.pk:
            self.initial['quantity'] = 1

        # Restrict price field access EXCLUSIVELY to AUTHORS
        if user and hasattr(user, 'profile'):
            if user.profile.role != 'AUTHOR':
                self.fields.pop('price', None)


class MediaItemForm(forms.ModelForm):
    CATEGORY_CHOICES = [
        ('books', 'Book (₹39.00)'),
        ('arts', 'Art Section (₹59.00)'),
        ('documentary', 'Documentary (₹109.00)'),
    ]

    category = forms.ChoiceField(
        choices=CATEGORY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Select the category for this media item."
    )

    # Baked default quantity set to 1
    quantity = forms.IntegerField(
        initial=1,
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 1,
            'value': 1
        })
    )

    class Meta:
        model = MediaItem
        fields = ['title', 'creator', 'category', 'quantity', 'file']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter media title'
            }),
            'creator': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter author, director, or artist name'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(MediaItemForm, self).__init__(*args, **kwargs)

        # Ensure initial value stays 1 if creating a new record
        if not self.is_bound and not self.instance.pk:
            self.initial['quantity'] = 1

        # Optional: Restrict price/category editing if user isn't an author/admin
        if user and hasattr(user, 'profile'):
            if user.profile.role != 'AUTHOR':
                pass