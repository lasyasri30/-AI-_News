from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Article, Category

def home(request):
    return HttpResponse("🎉 Welcome to ByteNews Homepage!")

def article_list(request):
    category = request.GET.get('category')
    query = request.GET.get('q')  # Optional: search query

    articles = Article.objects.all()

    if category:
        articles = articles.filter(category__name__iexact=category)

    if query:
        articles = articles.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query)
        )

    categories = Category.objects.all()
    paginator = Paginator(articles, 5)  # Show 5 articles per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'news/article_list.html', {
        'page_obj': page_obj,
        'category': category,
        'categories': categories,
        'search_query': query,
        'is_paginated': page_obj.has_other_pages()
    })

def article_detail(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    return render(request, 'news/article_detail.html', {'article': article})
