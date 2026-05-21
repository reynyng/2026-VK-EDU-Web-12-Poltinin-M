from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator
from django.urls import reverse


class Tag(models.Model):
    id = models.AutoField(primary_key=True)  # SERIAL
    name = models.CharField(max_length=50, unique=True, db_index=True)
    slug = models.SlugField(max_length=50, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name


class QuestionManager(models.Manager):
    def get_new(self):
        return self.filter(is_deleted=False).order_by('-created_at')
    
    def get_best(self):
        return self.filter(is_deleted=False).order_by('-rating', '-created_at')
    
    def get_by_tag(self, tag_name):
        return self.filter(tags__name__iexact=tag_name, is_deleted=False).order_by('-created_at')


class Question(models.Model):
    id = models.AutoField(primary_key=True)  # SERIAL
    title = models.CharField(max_length=200, validators=[MinLengthValidator(5)], db_index=True)
    text = models.TextField(validators=[MinLengthValidator(10)])
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='questions')
    tags = models.ManyToManyField(Tag, related_name='questions', blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    rating = models.IntegerField(default=0, db_index=True)
    answers_count = models.IntegerField(default=0, db_index=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    
    objects = QuestionManager()
    
    def __str__(self):
        return self.title[:100]
    
    def get_absolute_url(self):
        return reverse('app:question_detail', args=[self.id])
    
    def update_rating(self):
        likes = self.question_likes.filter(is_like=True).count()
        dislikes = self.question_likes.filter(is_like=False).count()
        self.rating = likes - dislikes
        self.save(update_fields=['rating'])
    
    def update_answers_count(self):
        self.answers_count = self.answers.filter(is_deleted=False).count()
        self.save(update_fields=['answers_count'])


class Answer(models.Model):
    id = models.AutoField(primary_key=True)  # SERIAL
    text = models.TextField(validators=[MinLengthValidator(5)])
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    is_helpful = models.BooleanField(default=False, db_index=True)
    rating = models.IntegerField(default=0, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    
    def __str__(self):
        return f"Ответ от {self.author.username}"
    
    def update_rating(self):
        likes = self.answer_likes.filter(is_like=True).count()
        dislikes = self.answer_likes.filter(is_like=False).count()
        self.rating = likes - dislikes
        self.save(update_fields=['rating'])


class QuestionLike(models.Model):
    id = models.AutoField(primary_key=True)  # SERIAL
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='question_likes')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='question_likes')
    is_like = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'question']


class AnswerLike(models.Model):
    id = models.AutoField(primary_key=True)  # SERIAL
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='answer_likes')
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name='answer_likes')
    is_like = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'answer']