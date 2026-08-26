from django.urls import path
from . import views

urlpatterns = [
    path("",views.login_view,name="login"),
    path('landing/',views.landing, name = "landing"),
    path('logout/',views.logout_view, name ="logout"),
    path("students/", views.student_list, name="student_list"),
    path("students/add/", views.add_student, name="add_student"),
    path("students/edit/<int:id>/", views.edit_student, name="edit_student"),
    path("students/delete/<int:id>/", views.delete_student, name="delete_student"),  
    path("signup",views.signup, name ="signup")   

]