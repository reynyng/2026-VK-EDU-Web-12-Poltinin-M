from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .utils import paginate

def generate_questions():
    questions = []
    for i in range(1, 30):
        questions.append({
            'id': i,
            'title': f'Как испечь пирог? (вопрос {i})',
            'text': 'Я не знаю как и из чего печь пироги. Можете подсказать, что мне делать?',
            'rating': i * 5,
            'answer_count': i * 2,
            'tags': ['Выпечка', 'Ягода'] if i % 2 == 0 else ['Выпечка'],
            'author': {'username': f'user{i}', 'avatar': None},
        })
    return questions

def generate_answers(question_id):
    answers = []
    for i in range(1, 15):
        answers.append({
            'id': i,
            'text': 'Для приготовления пирога вам понадобятся: мука, яйца, сахар...',
            'rating': i * 3,
            'author': {'username': f'answer_user{i}', 'avatar': None},
            'is_correct': i == 1,
        })
    return answers

def home_view(request):
    questions = generate_questions()
    page = paginate(questions, request, per_page=3)
    
    context = {
        'questions': page.object_list,
        'page': page,
        'popular_tags': [
            {'name': 'Овощи', 'color': 'rgb(0, 255, 55)'},
            {'name': 'Фрукты', 'color': 'rgb(250, 67, 11)'},
            {'name': 'Ягоды', 'color': 'rgb(0, 47, 255)'},
            {'name': 'Выпечка', 'color': 'rgba(255, 123, 0, 0.63)'},
        ],
        'top_members': [
            {'username': 'linking park'},
            {'username': 'Mr chief'},
            {'username': 'just a user'},
        ]
    }
    return render(request, 'home.html', context)

def hot_view(request):
    questions = generate_questions()
    questions.sort(key=lambda x: x['rating'], reverse=True)
    page = paginate(questions, request, per_page=3)
    
    context = {
        'questions': page.object_list,
        'page': page,
        'popular_tags': [
            {'name': 'Овощи', 'color': 'rgb(0, 255, 55)'},
            {'name': 'Фрукты', 'color': 'rgb(250, 67, 11)'},
            {'name': 'Ягоды', 'color': 'rgb(0, 47, 255)'},
            {'name': 'Выпечка', 'color': 'rgba(255, 123, 0, 0.63)'},
        ],
        'top_members': [
            {'username': 'linking park'},
            {'username': 'Mr chief'},
            {'username': 'just a user'},
        ]
    }
    return render(request, 'home.html', context)

def tag_questions_view(request, tag_name):
    questions = generate_questions()
    filtered_questions = [q for q in questions if tag_name in q['tags']]
    page = paginate(filtered_questions, request, per_page=3)
    
    context = {
        'questions': page.object_list,
        'page': page,
        'popular_tags': [
            {'name': 'Овощи', 'color': 'rgb(0, 255, 55)'},
            {'name': 'Фрукты', 'color': 'rgb(250, 67, 11)'},
            {'name': 'Ягоды', 'color': 'rgb(0, 47, 255)'},
            {'name': 'Выпечка', 'color': 'rgba(255, 123, 0, 0.63)'},
        ],
        'top_members': [
            {'username': 'linking park'},
            {'username': 'Mr chief'},
            {'username': 'just a user'},
        ]
    }
    return render(request, 'home.html', context)

def question_detail_view(request, question_id):
    questions = generate_questions()
    question = next((q for q in questions if q['id'] == question_id), None)
    
    if not question:
        # Вернуть 404, если вопрос не найден
        from django.http import Http404
        raise Http404("Вопрос не найден")
    
    answers = generate_answers(question_id)
    page = paginate(answers, request, per_page=3)
    
    context = {
        'question': question,
        'answers': page.object_list,
        'page': page,
        'popular_tags': [
            {'name': 'Овощи', 'color': 'rgb(0, 255, 55)'},
            {'name': 'Фрукты', 'color': 'rgb(250, 67, 11)'},
            {'name': 'Ягоды', 'color': 'rgb(0, 47, 255)'},
            {'name': 'Выпечка', 'color': 'rgba(255, 123, 0, 0.63)'},
        ],
        'top_members': [
            {'username': 'linking park'},
            {'username': 'Mr chief'},
            {'username': 'just a user'},
        ]
    }
    return render(request, 'question.html', context)

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next', reverse('home'))
                return redirect(next_url)
    else:
        form = AuthenticationForm()
    
    context = {
        'form': form,
        'popular_tags': [
            {'name': 'Овощи', 'color': 'rgb(0, 255, 55)'},
            {'name': 'Фрукты', 'color': 'rgb(250, 67, 11)'},
            {'name': 'Ягоды', 'color': 'rgb(0, 47, 255)'},
            {'name': 'Выпечка', 'color': 'rgba(255, 123, 0, 0.63)'},
        ],
        'top_members': [
            {'username': 'linking park'},
            {'username': 'Mr chief'},
            {'username': 'just a user'},
        ]
    }
    return render(request, 'login.html', context)

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect(reverse('home'))
    else:
        form = UserCreationForm()
    
    context = {
        'form': form,
        'popular_tags': [
            {'name': 'Овощи', 'color': 'rgb(0, 255, 55)'},
            {'name': 'Фрукты', 'color': 'rgb(250, 67, 11)'},
            {'name': 'Ягоды', 'color': 'rgb(0, 47, 255)'},
            {'name': 'Выпечка', 'color': 'rgba(255, 123, 0, 0.63)'},
        ],
        'top_members': [
            {'username': 'linking park'},
            {'username': 'Mr chief'},
            {'username': 'just a user'},
        ]
    }
    return render(request, 'registr.html', context)

def ask_view(request):
    if request.method == 'POST':
        # Здесь будет сохранение вопроса в базу данных
        return redirect(reverse('home'))
    
    context = {
        'popular_tags': [
            {'name': 'Овощи', 'color': 'rgb(0, 255, 55)'},
            {'name': 'Фрукты', 'color': 'rgb(250, 67, 11)'},
            {'name': 'Ягоды', 'color': 'rgb(0, 47, 255)'},
            {'name': 'Выпечка', 'color': 'rgba(255, 123, 0, 0.63)'},
        ],
        'top_members': [
            {'username': 'linking park'},
            {'username': 'Mr chief'},
            {'username': 'just a user'},
        ]
    }
    return render(request, 'new-question.html', context)

