from django.contrib.postgres.search import SearchQuery, SearchRank
from .models import Question

def search_questions(query, limit=10):
    """Полнотекстовый поиск по вопросам"""
    if not query:
        return []
    
    search_query = SearchQuery(query, config='russian')
    
    results = Question.objects.filter(
        is_deleted=False
    ).annotate(
        rank=SearchRank('search_vector', search_query)
    ).filter(
        search_vector=search_query
    ).order_by('-rank', '-created_at')[:limit]
    
    return results