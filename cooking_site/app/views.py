from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from django.db import models
from .models import Question, Tag, Answer, QuestionLike, AnswerLike
from .utils import paginate


def get_common_context(request):
    popular_tags = Tag.objects.annotate(
        questions_count=models.Count('questions')
    ).order_by('-questions_count')[:10]
    
    top_members = User.objects.annotate(
        rating=models.Sum('questions__rating')
    ).order_by('-rating')[:5]
    
    return {
        'popular_tags': popular_tags,
        'top_members': top_members,
    }


def home_view(request):
    questions = Question.objects.get_new()
    page = paginate(questions, request, per_page=5)
    
    # Добавляем дополнительные поля для отображения
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
    get_object_or_404(Tag, name__iexact=tag_name)
    questions = Question.objects.get_by_tag(tag_name)
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
            # Обновляем счетчик ответов у вопроса
            question.update_answers_count()
            messages.success(request, 'Ответ успешно добавлен!')
        else:
            messages.error(request, 'Текст ответа не может быть пустым')
        return redirect('app:question_detail', question_id=question.id)
    
    # Получаем ответы с пагинацией
    answers = question.answers.filter(is_deleted=False).order_by('-is_helpful', '-rating', 'created_at')
    page = paginate(answers, request, per_page=5)
    
    # Получаем актуальный рейтинг вопроса
    question.likes_count = question.question_likes.filter(is_like=True).count()
    question.dislikes_count = question.question_likes.filter(is_like=False).count()
    question.rating = question.likes_count - question.dislikes_count
    question.answers_count = question.answers.filter(is_deleted=False).count()
    
    # Для каждого ответа считаем лайки
    for answer in page.object_list:
        answer.likes_count = answer.answer_likes.filter(is_like=True).count()
        answer.dislikes_count = answer.answer_likes.filter(is_like=False).count()
        answer.rating = answer.likes_count - answer.dislikes_count
    
    # Проверяем, поставил ли пользователь лайк на вопрос
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


@login_required
@require_POST
def question_like_view(request, question_id):
    """Лайк/дизлайк вопроса (AJAX)"""
    question = get_object_or_404(Question, id=question_id)
    is_like = request.POST.get('is_like') == 'true'
    
    # Проверяем существующий лайк
    existing_like = QuestionLike.objects.filter(
        user=request.user, question=question
    ).first()
    
    if existing_like:
        if existing_like.is_like == is_like:
            # Удаляем лайк (отмена)
            existing_like.delete()
            liked = None
        else:
            # Меняем тип лайка
            existing_like.is_like = is_like
            existing_like.save()
            liked = is_like
    else:
        # Создаем новый лайк
        QuestionLike.objects.create(
            user=request.user,
            question=question,
            is_like=is_like
        )
        liked = is_like
    
    # Обновляем рейтинг
    question.update_rating()
    
    # Возвращаем новый рейтинг и состояние
    likes_count = question.question_likes.filter(is_like=True).count()
    dislikes_count = question.question_likes.filter(is_like=False).count()
    
    return JsonResponse({
        'success': True,
        'rating': question.rating,
        'likes_count': likes_count,
        'dislikes_count': dislikes_count,
        'liked': liked  # true - лайк, false - дизлайк, null - нет оценки
    })


@login_required
@require_POST
def answer_like_view(request, answer_id):
    """Лайк/дизлайк ответа (AJAX)"""
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
    """Отметка 'ответ помог' (только автор вопроса)"""
    answer = get_object_or_404(Answer, id=answer_id)
    question = answer.question
    
    # Проверяем, что текущий пользователь - автор вопроса
    if request.user != question.author:
        return JsonResponse({
            'success': False,
            'error': 'Только автор вопроса может отмечать ответы как "помог"'
        }, status=403)
    
    # Переключаем статус (можно несколько ответов)
    is_helpful = request.POST.get('is_helpful') == 'true'
    answer.is_helpful = is_helpful
    answer.save()
    
    return JsonResponse({
        'success': True,
        'is_helpful': answer.is_helpful
    })