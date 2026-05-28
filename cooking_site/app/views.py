from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import JsonResponse, Http404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Count
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from .models import Question, Tag, Answer, QuestionLike, AnswerLike
from .utils import paginate
from .search import search_questions


# ========== КЭШИРОВАНИЕ ==========

def get_cached_popular_tags():
    """Получает популярные теги из кэша или БД"""
    popular_tags = cache.get('popular_tags')
    if popular_tags is None:
        from .tasks import update_popular_tags
        update_popular_tags.delay()
        # Временный fallback
        popular_tags = list(Tag.objects.all().values('name', 'slug')[:10])
    return popular_tags


def get_cached_top_users():
    """Получает лучших пользователей из кэша или БД"""
    top_users = cache.get('top_users')
    if top_users is None:
        from .tasks import update_top_users
        update_top_users.delay()
        # Временный fallback
        top_users = list(User.objects.all().values('username')[:5])
    return top_users


def get_common_context(request):
    """Общий контекст для всех страниц"""
    popular_tags = get_cached_popular_tags()
    top_members = get_cached_top_users()
    
    return {
        'popular_tags': popular_tags,
        'top_members': top_members,
    }


# ========== ОСНОВНЫЕ СТРАНИЦЫ ==========

def home_view(request):
    """Главная страница - новые вопросы"""
    questions = Question.objects.get_new()
    page = paginate(questions, request, per_page=5)
    
    for question in page.object_list:
        question.likes_count = question.question_likes.filter(is_like=True).count()
        question.dislikes_count = question.question_likes.filter(is_like=False).count()
        question.answers_count = question.answers.filter(is_deleted=False).count()
    
    context = {
        'questions': page.object_list,
        'page': page,
    }
    context.update(get_common_context(request))
    return render(request, 'home.html', context)


def hot_view(request):
    """Лучшие вопросы"""
    questions = Question.objects.get_best()
    page = paginate(questions, request, per_page=5)
    
    for question in page.object_list:
        question.likes_count = question.question_likes.filter(is_like=True).count()
        question.dislikes_count = question.question_likes.filter(is_like=False).count()
        question.answers_count = question.answers.filter(is_deleted=False).count()
    
    context = {
        'questions': page.object_list,
        'page': page,
    }
    context.update(get_common_context(request))
    return render(request, 'home.html', context)


def tag_questions_view(request, tag_name):
    """Вопросы по тегу"""
    tag = get_object_or_404(Tag, name__iexact=tag_name)
    questions = tag.questions.filter(is_deleted=False).order_by('-created_at')
    page = paginate(questions, request, per_page=5)
    
    for question in page.object_list:
        question.likes_count = question.question_likes.filter(is_like=True).count()
        question.dislikes_count = question.question_likes.filter(is_like=False).count()
        question.answers_count = question.answers.filter(is_deleted=False).count()
    
    context = {
        'questions': page.object_list,
        'page': page,
        'current_tag': tag_name,
    }
    context.update(get_common_context(request))
    return render(request, 'home.html', context)


def question_detail_view(request, question_id):
    """Детальная страница вопроса + обработка ответов"""
    question = get_object_or_404(Question, id=question_id, is_deleted=False)
    
    # Обработка отправки ответа
    if request.method == 'POST' and request.user.is_authenticated:
        answer_text = request.POST.get('text')
        if answer_text:
            answer = Answer.objects.create(
                text=answer_text,
                author=request.user,
                question=question
            )
            question.update_answers_count()
            
            # Подготавливаем данные для real-time уведомления
            answer_data = {
                'id': answer.id,
                'text': answer.text,
                'author': answer.author.username,
                'author_id': answer.author.id,
                'created_at': answer.created_at.isoformat(),
                'is_helpful': answer.is_helpful,
                'rating': 0
            }
            
            # Отправляем уведомление через Centrifugo (асинхронно)
            from .tasks import send_new_answer_notification, send_new_answer_email
            send_new_answer_notification.delay(question_id, answer_data)
            
            # Отправляем email автору вопроса
            # Не отправляем если автор вопроса сам же и отвечает
            if request.user != question.author:
                if question.author.email:
                    send_new_answer_email.delay(
                        question_title=question.title,
                        author_email=question.author.email,
                        answer_author=request.user.username,
                        question_id=question.id,
                        answer_text=answer.text,
                    )
                else:
                    print(f"[Email] Автор вопроса {question.author.username} не имеет email, уведомление пропущено")
            
            messages.success(request, 'Ответ успешно добавлен!')
        else:
            messages.error(request, 'Текст ответа не может быть пустым')
        return redirect('app:question_detail', question_id=question.id)
    
    # GET запрос - показываем страницу
    answers = question.answers.filter(is_deleted=False).order_by('-is_helpful', '-rating', 'created_at')
    page = paginate(answers, request, per_page=5)
    
    question.likes_count = question.question_likes.filter(is_like=True).count()
    question.dislikes_count = question.question_likes.filter(is_like=False).count()
    
    # Собираем информацию о лайках пользователя для ответов
    answer_likes_map = {}
    if request.user.is_authenticated:
        for answer in page.object_list:
            user_like = AnswerLike.objects.filter(
                user=request.user, answer=answer
            ).first()
            if user_like:
                answer_likes_map[answer.id] = user_like.is_like
    
    for answer in page.object_list:
        answer.likes_count = answer.answer_likes.filter(is_like=True).count()
        answer.dislikes_count = answer.answer_likes.filter(is_like=False).count()
        answer.user_liked = answer_likes_map.get(answer.id)
    
    user_like = None
    if request.user.is_authenticated:
        user_like = QuestionLike.objects.filter(
            user=request.user, question=question
        ).first()
    
    context = {
        'question': question,
        'answers': page.object_list,
        'page': page,
        'user_like': user_like,
    }
    context.update(get_common_context(request))
    return render(request, 'question.html', context)


@login_required
def ask_view(request):
    """Создание нового вопроса"""
    if request.method == 'POST':
        title = request.POST.get('title')
        text = request.POST.get('text')
        tags_input = request.POST.get('tags', '')
        
        if title and text:
            question = Question.objects.create(
                title=title,
                text=text,
                author=request.user
            )
            
            if tags_input:
                tag_names = [t.strip().lower() for t in tags_input.split(',')]
                for tag_name in tag_names:
                    if tag_name:
                        tag, created = Tag.objects.get_or_create(
                            name=tag_name,
                            defaults={'slug': tag_name.replace(' ', '-')}
                        )
                        question.tags.add(tag)
            
            messages.success(request, 'Вопрос успешно создан!')
            return redirect('app:question_detail', question_id=question.id)
        else:
            messages.error(request, 'Заполните заголовок и текст вопроса')
    
    context = {}
    context.update(get_common_context(request))
    return render(request, 'new-question.html', context)


def search_view(request):
    """Поиск вопросов (AJAX)"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    results = search_questions(query)
    data = {
        'results': [
            {
                'id': q.id,
                'title': q.title,
                'url': q.get_absolute_url(),
                'text_preview': q.text[:100] + '...' if len(q.text) > 100 else q.text
            }
            for q in results
        ]
    }
    return JsonResponse(data)


# ========== API ДЛЯ ЛАЙКОВ ==========

@login_required
@require_POST
def question_like_view(request, question_id):
    """Оценка вопроса (лайк/дизлайк)"""
    question = get_object_or_404(Question, id=question_id)
    is_like = request.POST.get('is_like') == 'true'
    
    existing_like = QuestionLike.objects.filter(
        user=request.user, question=question
    ).first()
    
    if existing_like:
        if existing_like.is_like == is_like:
            existing_like.delete()
            liked = None
        else:
            existing_like.is_like = is_like
            existing_like.save()
            liked = is_like
    else:
        QuestionLike.objects.create(
            user=request.user,
            question=question,
            is_like=is_like
        )
        liked = is_like
    
    question.update_rating()
    
    likes_count = question.question_likes.filter(is_like=True).count()
    dislikes_count = question.question_likes.filter(is_like=False).count()
    
    return JsonResponse({
        'success': True,
        'rating': question.rating,
        'likes_count': likes_count,
        'dislikes_count': dislikes_count,
        'liked': liked
    })


@login_required
@require_POST
def answer_like_view(request, answer_id):
    """Оценка ответа (лайк/дизлайк)"""
    answer = get_object_or_404(Answer, id=answer_id)
    is_like = request.POST.get('is_like') == 'true'
    
    existing_like = AnswerLike.objects.filter(
        user=request.user, answer=answer
    ).first()
    
    if existing_like:
        if existing_like.is_like == is_like:
            existing_like.delete()
            liked = None
        else:
            existing_like.is_like = is_like
            existing_like.save()
            liked = is_like
    else:
        AnswerLike.objects.create(
            user=request.user,
            answer=answer,
            is_like=is_like
        )
        liked = is_like
    
    answer.update_rating()
    
    likes_count = answer.answer_likes.filter(is_like=True).count()
    dislikes_count = answer.answer_likes.filter(is_like=False).count()
    
    return JsonResponse({
        'success': True,
        'rating': answer.rating,
        'likes_count': likes_count,
        'dislikes_count': dislikes_count,
        'liked': liked
    })


@login_required
@require_POST
def mark_helpful_view(request, answer_id):
    """Отметить/снять отметку 'помог' с ответа (только для автора вопроса)"""
    answer = get_object_or_404(Answer, id=answer_id)
    question = answer.question
    
    if request.user != question.author:
        return JsonResponse({
            'success': False,
            'error': 'Только автор вопроса может отмечать ответы как "помог"'
        }, status=403)
    
    is_helpful = request.POST.get('is_helpful') == 'true'
    answer.is_helpful = is_helpful
    answer.save()
    
    return JsonResponse({
        'success': True,
        'is_helpful': answer.is_helpful
    })