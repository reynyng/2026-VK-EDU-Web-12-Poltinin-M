from django.urls import path
from . import views

app_name = 'app'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('hot/', views.hot_view, name='hot'),
    path('tag/<str:tag_name>/', views.tag_questions_view, name='tag_questions'),
    path('question/<int:question_id>/', views.question_detail_view, name='question_detail'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('ask/', views.ask_view, name='ask'),
]