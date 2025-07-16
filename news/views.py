
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import Article, Category

def home(request):
    return HttpResponse("🎉 Welcome to ByteNews Homepage!")

def article_list(request):
    category = request.GET.get('category')
    if category:
        articles = Article.objects.filter(category__name=category)
    else:
        articles = Article.objects.all()
    
    categories = Category.objects.all()
    paginator = Paginator(articles, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'news/article_list.html', {'page_obj': page_obj, 'category': category, 'categories': categories,  'is_paginated': page_obj.has_other_pages()})

def article_detail(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    return render(request, 'news/article_detail.html', {'article': article})
