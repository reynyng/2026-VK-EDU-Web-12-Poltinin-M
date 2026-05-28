import requests
from celery import shared_task
from django.core.cache import cache
from django.core.mail import send_mail, EmailMultiAlternatives
from django.db.models import Count, Q
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


@shared_task
def update_popular_tags():
    from .models import Tag
    three_months_ago = timezone.now() - timedelta(days=90)

    popular_tags = list(Tag.objects.filter(
        questions__created_at__gte=three_months_ago,
        questions__is_deleted=False
    ).annotate(
        questions_count=Count('questions')
    ).filter(
        questions_count__gt=0
    ).order_by('-questions_count')[:10].values('id', 'name', 'slug', 'questions_count'))

    cache.set('popular_tags', popular_tags, timeout=60 * 60)
    return popular_tags


@shared_task
def update_top_users():
    one_week_ago = timezone.now() - timedelta(days=7)

    top_users = list(User.objects.filter(
        Q(questions__created_at__gte=one_week_ago) |
        Q(answers__created_at__gte=one_week_ago)
    ).distinct().annotate(
        total_rating=Count('questions__rating') + Count('answers__rating')
    ).order_by('-total_rating')[:10].values('id', 'username', 'total_rating'))

    cache.set('top_users', top_users, timeout=60 * 60)
    return top_users


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_new_answer_notification(self, question_id, answer_data):
    """Отправляет real-time уведомление через Centrifugo API"""
    from django.conf import settings

    api_url = f"{settings.CENTRIFUGO_URL}/api/publish"
    headers = {
        'Authorization': f'apikey {settings.CENTRIFUGO_API_KEY}',
        'Content-Type': 'application/json',
    }
    payload = {
        'channel': f"questions:{question_id}",
        'data': answer_data,
    }

    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=5)
        response.raise_for_status()
        print(f"[Centrifugo] Published to questions:{question_id} → {response.status_code}")
        return response.json()
    except requests.RequestException as e:
        print(f"[Centrifugo] Error: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_new_answer_email(self, question_title, author_email, answer_author,
                          question_id, answer_text=''):
    """
    Отправляет email автору вопроса когда кто-то добавил ответ.
    Использует EmailMultiAlternatives для отправки HTML + plain text.
    """
    from django.conf import settings

    question_url = f"http://localhost:8000/question/{question_id}/"

    subject = f'Новый ответ на ваш вопрос: «{question_title}»'

    # Plain text версия
    text_body = (
        f"Здравствуйте!\n\n"
        f"Пользователь {answer_author} ответил на ваш вопрос «{question_title}».\n\n"
        f"Текст ответа:\n{answer_text}\n\n"
        f"Перейти к вопросу: {question_url}\n\n"
        f"С уважением,\nКоманда «Домашняя книга рецептов»"
    )

    # HTML версия
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #333; border-bottom: 2px solid #eee; padding-bottom: 10px;">
            Новый ответ на ваш вопрос
        </h2>

        <p style="color: #555;">Здравствуйте!</p>

        <p style="color: #555;">
            Пользователь <strong>{answer_author}</strong> ответил на ваш вопрос
            <strong>«{question_title}»</strong>.
        </p>

        <div style="background: #f9f9f9; border-left: 4px solid #6464ff;
                    padding: 15px; margin: 20px 0; border-radius: 4px;">
            <p style="margin: 0; color: #333;">{answer_text}</p>
        </div>

        <a href="{question_url}"
           style="display: inline-block; background: #6464ff; color: white;
                  padding: 12px 24px; border-radius: 8px; text-decoration: none;
                  font-weight: bold; margin-top: 10px;">
            Посмотреть ответ
        </a>

        <hr style="margin-top: 30px; border: none; border-top: 1px solid #eee;">
        <p style="color: #aaa; font-size: 12px;">
            Домашняя книга рецептов — вы получили это письмо, потому что являетесь
            автором вопроса на сайте.
        </p>
    </div>
    """

    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[author_email],
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send()
        print(f"[Email] Отправлено на {author_email} (вопрос #{question_id})")
    except Exception as e:
        print(f"[Email] Ошибка отправки на {author_email}: {e}")
        raise self.retry(exc=e)