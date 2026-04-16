from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

def paginate(objects_list, request, per_page=10):
    """
    Функция для пагинации списка объектов
    
    Args:
        objects_list: список или QuerySet объектов
        request: объект запроса Django
        per_page: количество объектов на странице (по умолчанию 10)
    
    Returns:
        page: объект страницы Paginator
    """
    paginator = Paginator(objects_list, per_page)
    
    # Получаем номер страницы из GET параметра 'page'
    page_number = request.GET.get('page', 1)
    
    try:
        page = paginator.page(page_number)
    except PageNotAnInteger:
        # Если параметр не число - показываем первую страницу
        page = paginator.page(1)
    except EmptyPage:
        # Если страница выходит за пределы - показываем последнюю
        page = paginator.page(paginator.num_pages)
    
    return page