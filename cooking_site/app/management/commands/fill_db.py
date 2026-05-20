import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from app.models import Tag, Question, Answer, QuestionLike, AnswerLike


class Command(BaseCommand):
    help = 'Fill database with test data'
    
    def add_arguments(self, parser):
        parser.add_argument('ratio', type=int, help='Коэффициент заполнения сущностей')
    
    @transaction.atomic
    def handle(self, *args, **options):
        ratio = options['ratio']
        
        self.stdout.write('=' * 60)
        self.stdout.write(f'НАЧАЛО НАПОЛНЕНИЯ БД с коэффициентом {ratio}')
        self.stdout.write('=' * 60)
        
        # 1. Пользователи
        self.stdout.write(f'\n1. Создание {ratio} пользователей...')
        users = []
        for i in range(ratio):
            user = User.objects.create_user(
                username=f'user_{i+1}',
                password='123',
                email=f'{i+1}@mail.com'
            )
            users.append(user)
            if (i + 1) % 1000 == 0:
                self.stdout.write(f'   Создано: {i + 1}')
        
        # 2. Теги
        self.stdout.write(f'\n2. Создание {ratio} тегов...')
        tags = []
        for i in range(ratio):
            tag = Tag.objects.create(
                name=f'тег_{i+1}',
                slug=f'tag_{i+1}'
            )
            tags.append(tag)
            if (i + 1) % 1000 == 0:
                self.stdout.write(f'   Создано: {i + 1}')
        
        # 3. Вопросы
        questions_count = ratio * 10
        self.stdout.write(f'\n3. Создание {questions_count} вопросов...')
        questions = []
        
        for i in range(questions_count):
            question = Question.objects.create(
                title=f'Вопрос {i+1}',
                text=f'Текст вопроса {i+1}',
                author=users[i % len(users)],
                rating=0,
                answers_count=0
            )
            question.tags.add(tags[i % len(tags)])
            questions.append(question)
            
            if (i + 1) % 10000 == 0:
                self.stdout.write(f'   Создано: {i + 1}')
        
        # 4. Ответы
        answers_count = ratio * 100
        self.stdout.write(f'\n4. Создание {answers_count} ответов...')
        answers = []
        
        for i in range(answers_count):
            answer = Answer.objects.create(
                text=f'Ответ {i+1}',
                author=users[i % len(users)],
                question=questions[i % len(questions)],
                is_helpful=(i % 20 == 0),
                rating=0
            )
            answers.append(answer)
            
            if (i + 1) % 100000 == 0:
                self.stdout.write(f'   Создано: {i + 1}')
        
        # 5. Лайки на вопросы
        required_likes = ratio * 100
        self.stdout.write(f'\n5. Создание {required_likes} лайков на вопросы...')
        
        used_pairs = set()
        likes_created = 0
        
        while likes_created < required_likes:
            user = random.choice(users)
            question = random.choice(questions)
            pair = (user.id, question.id)
            
            if pair not in used_pairs:
                is_like = random.choice([True, False])
                QuestionLike.objects.create(
                    user=user,
                    question=question,
                    is_like=is_like
                )
                used_pairs.add(pair)
                likes_created += 1
                
                if likes_created % 50000 == 0:
                    self.stdout.write(f'   Создано: {likes_created}')
        
        # 6. Лайки на ответы
        required_answer_likes = ratio * 100
        self.stdout.write(f'\n6. Создание {required_answer_likes} лайков на ответы...')
        
        used_pairs = set()
        answer_likes_created = 0
        
        while answer_likes_created < required_answer_likes:
            user = random.choice(users)
            answer = random.choice(answers)
            pair = (user.id, answer.id)
            
            if pair not in used_pairs:
                is_like = random.choice([True, False])
                AnswerLike.objects.create(
                    user=user,
                    answer=answer,
                    is_like=is_like
                )
                used_pairs.add(pair)
                answer_likes_created += 1
                
                if answer_likes_created % 50000 == 0:
                    self.stdout.write(f'   Создано: {answer_likes_created}')
        
        # 7. Обновление рейтингов
        self.stdout.write('\n7. Обновление рейтингов...')
        
        for question in questions:
            likes = question.question_likes.filter(is_like=True).count()
            dislikes = question.question_likes.filter(is_like=False).count()
            question.rating = likes - dislikes
            question.answers_count = question.answers.filter(is_deleted=False).count()
            question.save(update_fields=['rating', 'answers_count'])
        
        for answer in answers:
            likes = answer.answer_likes.filter(is_like=True).count()
            dislikes = answer.answer_likes.filter(is_like=False).count()
            answer.rating = likes - dislikes
            answer.save(update_fields=['rating'])
        
        # 8. Итог
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('ИТОГОВАЯ СТАТИСТИКА:'))
        self.stdout.write('=' * 60)
        self.stdout.write(f'Пользователей: {User.objects.count():,}')
        self.stdout.write(f'Тегов: {Tag.objects.count():,}')
        self.stdout.write(f'Вопросов: {Question.objects.count():,}')
        self.stdout.write(f'Ответов: {Answer.objects.count():,}')
        self.stdout.write(f'Лайков вопросов: {QuestionLike.objects.count():,}')
        self.stdout.write(f'Лайков ответов: {AnswerLike.objects.count():,}')
        self.stdout.write('=' * 60)
        
        if ratio >= 10000:
            self.stdout.write(self.style.SUCCESS('\n ТРЕБОВАНИЯ ЗАДАНИЯ ВЫПОЛНЕНЫ!'))
        
        self.stdout.write(self.style.SUCCESS('\n НАПОЛНЕНИЕ БД ЗАВЕРШЕНО!'))