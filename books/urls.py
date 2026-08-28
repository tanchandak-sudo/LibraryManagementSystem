from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from . import views

app_name = 'books'

urlpatterns = [
    # Catalog Views
    path('', views.book_list, name='book_list'),
    path('add/', views.add_book, name='add_book'),

    # Cart Routes
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/', views.add_to_cart_single, name='add_to_cart_single_api'),
    path('cart/add/<int:book_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/add-single/<int:book_id>/', views.add_to_cart, name='add_to_cart_single'),
    path('cart/add-bulk/', views.add_to_cart_bulk, name='add_to_cart_bulk'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    path('cart/checkout/', views.cart_checkout, name='cart_checkout'),
    path('cart/view/', views.cart_detail, name='view_cart'),
    path('cart/checkout-legacy/', views.cart_checkout, name='checkout_cart'),

    # Requests & Actions
    path('requests/', views.book_requests, name='book_requests'),
    path('request/<int:request_id>/cancel/', views.cancel_request, name='cancel_request'),
    path('requests/<int:request_id>/approve/', views.approve_request, name='approve_request'),
    path('requests/<int:request_id>/reject/', views.reject_request, name='reject_request'),
    path('requests/<int:request_id>/return/', views.return_book, name='return_book'),

    # Subscriptions & Payment Handling
    path('subscription/', views.buy_subscription, name='buy_subscription'),
    path('subscription/my/', views.my_subscription, name='my_subscription'),
    path('verify-payment/', views.verify_payment, name='verify_payment'),
    path('payments/verify/', views.verify_payment, name='verify_payment_alias'),
    path('payment-confirmation/<int:order_id>/', views.payment_confirmation, name='payment_confirmation'),

    # Media & APIs
    path('media/', views.media_page_view, name='media_page'),
    path('media/add/', views.add_media, name='add_media'),
    path('stream/documentary/<int:pk>/', views.stream_documentary, name='stream_documentary'),
    path('stream/art/<int:pk>/', views.stream_art, name='stream_art'),
    path('api/books/', views.book_list_api, name='book_list_api'),
    path('api/media/', views.media_catalog_api, name='media_catalog_api'),
    path('api/cart/count/', views.get_cart_count, name='get_cart_count'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='books:schema'), name='swagger-ui'),

    # Book Specific Routes
    path('<int:book_id>/', views.book_detail, name='book_detail'),
    path('<int:book_id>/edit/', views.edit_book, name='edit_book'),
    path('<int:book_id>/delete/', views.delete_book, name='delete_book'),
    path('<int:book_id>/request/', views.request_book, name='request_book'),
    path('<int:book_id>/gift/', views.gift_book, name='gift_book'),
    path('gift/<int:book_id>/', views.gift_book, name='gift_book_alias'),
    path('<int:book_id>/read/', views.read_book, name='read_book'),
]

# from django.urls import path
# from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
# from . import views

# app_name = 'books'

# urlpatterns = [
#     # Catalog Views
#     path('', views.book_list, name='book_list'),
#     path('add/', views.add_book, name='add_book'),

#     # Cart Routes
#     path('cart/', views.cart_detail, name='cart_detail'),
#     path('cart/add/', views.add_to_cart_single, name='add_to_cart_single_api'),
#     path('cart/add/<int:book_id>/', views.add_to_cart, name='add_to_cart'),
#     path('cart/add-single/<int:book_id>/', views.add_to_cart, name='add_to_cart_single'),
#     path('cart/add-bulk/', views.add_to_cart_bulk, name='add_to_cart_bulk'),
#     path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
#     path('cart/clear/', views.clear_cart, name='clear_cart'),
#     path('cart/checkout/', views.cart_checkout, name='cart_checkout'),
#     path('cart/view/', views.cart_detail, name='view_cart'),
#     path('cart/checkout-legacy/', views.cart_checkout, name='checkout_cart'),

#     # Requests & Actions
#     path('requests/', views.book_requests, name='book_requests'),
#     path('request/<int:request_id>/cancel/', views.cancel_request, name='cancel_request'),
#     path('requests/<int:request_id>/approve/', views.approve_request, name='approve_request'),
#     path('requests/<int:request_id>/reject/', views.reject_request, name='reject_request'),
#     path('requests/<int:request_id>/return/', views.return_book, name='return_book'),

#     # Subscriptions & Payment Handling
#     path('subscription/', views.buy_subscription, name='buy_subscription'),
#     path('subscription/my/', views.my_subscription, name='my_subscription'),
#     path('verify-payment/', views.verify_payment, name='verify_payment'),
#     path('payments/verify/', views.verify_payment, name='verify_payment_alias'),

#     # Media & APIs
#     path('media/', views.media_page_view, name='media_page'),
#     path('media/add/', views.add_media, name='add_media'),
#     path('stream/documentary/<int:pk>/', views.stream_documentary, name='stream_documentary'),
#     path('stream/art/<int:pk>/', views.stream_art, name='stream_art'),
#     path('api/books/', views.book_list_api, name='book_list_api'),
#     path('api/media/', views.media_catalog_api, name='media_catalog_api'),
#     path('api/cart/count/', views.get_cart_count, name='get_cart_count'),
#     path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
#     path('api/docs/', SpectacularSwaggerView.as_view(url_name='books:schema'), name='swagger-ui'),

#     # Book Specific Routes
#     path('<int:book_id>/', views.book_detail, name='book_detail'),
#     path('<int:book_id>/edit/', views.edit_book, name='edit_book'),
#     path('<int:book_id>/delete/', views.delete_book, name='delete_book'),
#     path('<int:book_id>/request/', views.request_book, name='request_book'),
#     path('<int:book_id>/gift/', views.gift_book, name='gift_book'),
#     path('gift/<int:book_id>/', views.gift_book, name='gift_book_alias'),
#     path('<int:book_id>/read/', views.read_book, name='read_book'),
# ]