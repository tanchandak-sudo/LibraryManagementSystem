"""
URL configuration for LibraryManagementSystem project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

from books.views import media_page_view

urlpatterns = [
    # Root page mapping
    path('', media_page_view, name='home'),
    
    # Admin and User auth management
    path('admin/', admin.site.urls),  
    path('users/', include('users.urls')),  # Includes login/logout endpoints
    
    # App & Domain Routes
    path('books/', include('books.urls')),
    path('payments/', include('payments.urls')),

    # ==========================================
    # --- SWAGGER & OPENAPI DOCUMENTATION ---
    # ==========================================
    # Raw OpenAPI Schema (JSON/YAML)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    
    # Swagger UI mounted directly at /api/
    path('api/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # ReDoc UI (Alternative Clean Documentation View)
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # REST API endpoints (Included AFTER /api/ so it doesn't hijack the root index)
    path('api/', include('rest.urls')),

    path('reports/', include('reports.urls')),
]

# Serve uploaded media files during local development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)