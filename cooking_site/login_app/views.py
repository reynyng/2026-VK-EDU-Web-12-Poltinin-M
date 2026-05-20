from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import models
from .models import Profile
from app.models import Tag


def login_view(request):
    if request.user.is_authenticated:
        return redirect('app:home')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Добро пожаловать, {username}!')
                return redirect('app:home')
        messages.error(request, 'Неверное имя пользователя или пароль')
    
    form = AuthenticationForm()
    context = {
        'form': form,
        'popular_tags': Tag.objects.annotate(
            questions_count=models.Count('questions')
        ).order_by('-questions_count')[:10],
        'top_members': User.objects.annotate(
            rating=models.Sum('questions__rating')
        ).order_by('-rating')[:5]
    }
    return render(request, 'login.html', context)


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('app:home')
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}!')
            return redirect('app:home')
    else:
        form = UserCreationForm()
    
    context = {
        'form': form,
        'popular_tags': Tag.objects.annotate(
            questions_count=models.Count('questions')
        ).order_by('-questions_count')[:10],
        'top_members': User.objects.annotate(
            rating=models.Sum('questions__rating')
        ).order_by('-rating')[:5]
    }
    return render(request, 'registr.html', context)


def logout_view(request):
    logout(request)
    messages.info(request, 'Вы вышли из аккаунта')
    return redirect('app:home')