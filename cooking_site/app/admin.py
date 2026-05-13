from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Tag, Question, Answer, QuestionLike, AnswerLike
# Убираем Profile отсюда - он теперь в login_app


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


class QuestionAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'rating', 'answers_count', 'created_at')
    list_filter = ('created_at', 'tags')
    search_fields = ('title', 'text')
    filter_horizontal = ('tags',)
    readonly_fields = ('rating', 'answers_count')


class AnswerAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'author', 'is_helpful', 'rating', 'created_at')
    list_filter = ('is_helpful', 'created_at')
    search_fields = ('text',)


class QuestionLikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'is_like', 'created_at')
    list_filter = ('is_like',)


class AnswerLikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'answer', 'is_like', 'created_at')
    list_filter = ('is_like',)


admin.site.register(Tag, TagAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Answer, AnswerAdmin)
admin.site.register(QuestionLike, QuestionLikeAdmin)
admin.site.register(AnswerLike, AnswerLikeAdmin)