from django.urls import path
from books import views

urlpatterns = [
    # Catalog Endpoints
    path("books/", views.book_list_api, name="book_list_api"),
    path("books/<int:pk>/", views.book_detail_api, name="book_detail_api"),
    path("media/", views.media_catalog_api, name="media_catalog_api"),
    
    # Cart API Endpoints
    path("cart/count/", views.get_cart_count, name="get_cart_count_api"),
    path("cart/add-single/", views.add_to_cart_single, name="add_to_cart_single_api"),
    path("cart/add-bulk/", views.add_to_cart_bulk, name="add_to_cart_bulk_api"),
]