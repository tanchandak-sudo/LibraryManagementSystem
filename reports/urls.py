from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.reports_dashboard, name='reports_dashboard'),
    path('api/data/', views.get_report_data, name='get_report_data'),
    path('export/excel/', views.export_report_excel, name='export_report_excel'),
]