from rest_framework import serializers
from .models import Book  # Replace with your actual Book model

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'