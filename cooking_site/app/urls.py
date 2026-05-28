from django.urls import path
from . import views

app_name = 'app'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('hot/', views.hot_view, name='hot'),
    path('tag/<str:tag_name>/', views.tag_questions_view, name='tag_questions'),
    path('question/<int:question_id>/', views.question_detail_view, name='question_detail'),
    path('ask/', views.ask_view, name='ask'),
    path('search/', views.search_view, name='search'),  # НОВЫЙ маршрут для поиска
    
    # API для лайков
    path('api/question/<int:question_id>/like/', views.question_like_view, name='question_like'),
    path('api/answer/<int:answer_id>/like/', views.answer_like_view, name='answer_like'),
    path('api/answer/<int:answer_id>/helpful/', views.mark_helpful_view, name='mark_helpful'),
]