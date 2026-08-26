from django.urls import path
from . import views

urlpatterns = [
    path('checkout/', views.initiate_payment, name='initiate_payment'),
    path('callback/', views.payment_callback, name='payment_callback'),
    path('success/', views.payment_success, name='payment_success'),  
]