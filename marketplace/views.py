from decimal import Decimal, InvalidOperation

from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction

from .models import Farmer, Listing, WeeklyCycle


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
                    user=user, name=name, phone=phone,
                    village=village, is_verified=False
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


@login_required(login_url='farmer_login')
def farmer_listings(request):
    try:
        farmer = Farmer.objects.get(user=request.user)
    except Farmer.DoesNotExist:
        logout(request)
        return redirect('farmer_login')

    cycle = WeeklyCycle.objects.filter(is_active=True).order_by('-order_open').first()
    error_message = None
    success_message = None

    if not farmer.is_verified:
        error_message = "Your account is pending verification. You can list produce after admin approval."
    elif cycle is None:
        error_message = "No active weekly cycle right now. Please check back later."
    elif request.method == 'POST':
        produce_name = request.POST.get('produce_name', '').strip()
        try:
            price = Decimal(request.POST.get('price_per_kg', ''))
            quantity = Decimal(request.POST.get('quantity_available', ''))
        except InvalidOperation:
            price = quantity = None

        if not produce_name or price is None or quantity is None or price <= 0 or quantity <= 0:
            error_message = "Please enter a valid produce name, price and quantity."
        elif Listing.objects.filter(farmer=farmer, cycle=cycle, produce_name__iexact=produce_name).exists():
            error_message = "You have already listed this produce for the current cycle."
        else:
            Listing.objects.create(
                farmer=farmer, cycle=cycle, produce_name=produce_name,
                price_per_kg=price, quantity_available=quantity,
            )
            success_message = "Produce listed successfully."

    listings = Listing.objects.filter(farmer=farmer, cycle=cycle) if cycle else []

    return render(request, 'farmer_listings.html', {
        'farmer': farmer,
        'cycle': cycle,
        'listings': listings,
        'error': error_message,
        'success': success_message,
    })