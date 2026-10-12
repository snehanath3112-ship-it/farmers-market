from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from .models import Farmer


def farmer_register(request):
    error_message = None

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        village = request.POST.get('village', '').strip()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if User.objects.filter(username=username).exists():
            error_message = "This username is already taken. Please choose another one."
        elif Farmer.objects.filter(phone=phone).exists():
            error_message = "This phone number is already registered."
        else:
            with transaction.atomic():
                user = User.objects.create_user(username=username, password=password)
                Farmer.objects.create(
                    user=user,
                    name=name,
                    phone=phone,
                    village=village,
                    is_verified=False
                )
            return redirect('farmer_login')

    return render(request, 'farmer_register.html', {'error': error_message})


def farmer_login(request):
    error_message = None

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('farmer_dashboard')
        else:
            error_message = "Invalid username or password."

    return render(request, 'farmer_login.html', {'error': error_message})


@login_required(login_url='farmer_login')
def farmer_dashboard(request):
    try:
        farmer = Farmer.objects.get(user=request.user)
    except Farmer.DoesNotExist:
        logout(request)
        return redirect('farmer_login')
    return render(request, 'farmer_dashboard.html', {'farmer': farmer})


def farmer_logout(request):
    logout(request)
    return redirect('farmer_login')