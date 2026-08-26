from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.models import User
from .models import Profile
from .forms import UserForm, ProfileForm, StudentRegistrationForm
from django.shortcuts import get_object_or_404
from .decorators import role_required

@role_required(["SUPERADMIN","LIBRARIAN"])
def student_list(request):
    students = Profile.objects.filter().exclude(user__is_superuser=True)
    return render(request, "users/student_list.html", {"students": students})


@role_required(["SUPERADMIN"])
def add_student(request):
    if request.method == "POST":
        user_form = UserForm(request.POST)
        profile_form = ProfileForm(request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            user.set_password(user.password)
            user.save()

            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()

            return redirect("student_list")
    else:
        user_form = UserForm()
        profile_form = ProfileForm()

    return render(
        request,
        "users/student_form.html",
        {
            "user_form": user_form,
            "profile_form": profile_form,
        },
    )


@role_required(["SUPERADMIN"])
def edit_student(request, id):
    profile = get_object_or_404(Profile, id=id)
    user = profile.user

    if request.method == "POST":
        user_form = UserForm(request.POST, instance=user)
        profile_form = ProfileForm(request.POST, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)

            password = user_form.cleaned_data.get("password")
            if password:
                user.set_password(password)

            user.save()
            profile_form.save()

            return redirect("student_list")
    else:
        user_form = UserForm(instance=user)
        profile_form = ProfileForm(instance=profile)

    return render(
        request,
        "users/student_form.html",
        {
            "user_form": user_form,
            "profile_form": profile_form,
        },
    )


@role_required(["SUPERADMIN"])
def delete_student(request, id):
    profile = get_object_or_404(Profile, id=id)

    if request.method == "POST":
        profile.user.delete()
        return redirect("student_list")

    return render(
        request,
        "users/student_delete.html",
        {
            "profile": profile,
        },
    )

def login_view(request):
    if request.method == "POST":
        username  = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request,username=username,password=password)

        if user is not None:
            login(request, user)
            return redirect("landing")
        
        messages.error(request,"invalid username and password")

    return render(request,"users/login.html")
    
def landing(request):
    return render(request, "users/landing.html")

def logout_view(request):
    logout(request)
    return redirect("login")

def signup(request):
    if request.method == "POST":
        form = StudentRegistrationForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.save()

            Profile.objects.create(
                user=user,
                role="STUDENT"
            )

            return redirect("login")

    else:
        form = StudentRegistrationForm()

    return render(request, "users/signup.html", {"form": form})