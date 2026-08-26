from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):

    ROLE_CHOICE = [('SUPERADMIN','SuperAdmin'),('LIBRARIAN', 'Librarian'),('STUDENT','Student'),('AUTHOR','Author')]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices = ROLE_CHOICE)

    def __str__(self):
        return f"{self.user.username} - {self.role}"
