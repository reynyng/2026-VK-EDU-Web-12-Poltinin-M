from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
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
        username_or_email = request.POST.get('username', '')
        password = request.POST.get('password', '')
        
        user = None
        if '@' in username_or_email:
            try:
                user_obj = User.objects.get(email=username_or_email)
                user = authenticate(username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None
        else:
            user = authenticate(username=username_or_email, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}!')
            return redirect('app:home')
        else:
            messages.error(request, 'Неверное имя пользователя/email или пароль')
    
    context = {
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
            
            email = request.POST.get('email', '')
            
            if email:
                user.email = email
                user.save()
            
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}!')
            return redirect('app:home')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
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


@login_required
def profile_view(request):
    user = request.user
    profile = user.profile
    
    questions_count = user.questions.count()
    answers_count = user.answers.count()
    
    from django.db.models import Sum
    questions_rating = user.questions.aggregate(total=Sum('rating'))['total'] or 0
    answers_rating = user.answers.aggregate(total=Sum('rating'))['total'] or 0
    total_rating = questions_rating + answers_rating
    
    given_likes = user.question_likes.count() + user.answer_likes.count()
    
    context = {
        'profile_user': user,
        'profile': profile,
        'questions_count': questions_count,
        'answers_count': answers_count,
        'total_rating': total_rating,
        'given_likes': given_likes,
        'popular_tags': Tag.objects.annotate(
            questions_count=models.Count('questions')
        ).order_by('-questions_count')[:10],
        'top_members': User.objects.annotate(
            rating=models.Sum('questions__rating')
        ).order_by('-rating')[:5]
    }
    return render(request, 'profile.html', context)


@login_required
def profile_edit_view(request):
    user = request.user
    profile = user.profile
    
    if request.method == 'POST':
        email = request.POST.get('email')
        old_password = request.POST.get('old_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        
        if email and email != user.email:
            user.email = email
            user.save()
        
        if old_password and new_password1 and new_password2:
            if user.check_password(old_password):
                if new_password1 == new_password2:
                    if len(new_password1) >= 8:
                        user.set_password(new_password1)
                        user.save()
                        update_session_auth_hash(request, user)
                        messages.success(request, 'Пароль успешно изменен!')
                    else:
                        messages.error(request, 'Пароль должен содержать не менее 8 символов')
                else:
                    messages.error(request, 'Новые пароли не совпадают')
            else:
                messages.error(request, 'Неверный текущий пароль')
        
        messages.success(request, 'Профиль успешно обновлен!')
        return redirect('login_app:profile')
    
    context = {
        'profile_user': user,
        'profile': profile,
        'popular_tags': Tag.objects.annotate(
            questions_count=models.Count('questions')
        ).order_by('-questions_count')[:10],
        'top_members': User.objects.annotate(
            rating=models.Sum('questions__rating')
        ).order_by('-rating')[:5]
    }
    return render(request, 'profile_edit.html', context)