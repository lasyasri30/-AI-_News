from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.contrib.auth.decorators import login_required
from .models import Article, Category, UserPreference, ReadingHistory
from .forms import PreferenceForm
from django.contrib import messages
from .utils import generate_summary  # 🧠 Import summarizer function

def home(request):
    return HttpResponse("🎉 Welcome to ByteNews Homepage!")

def article_list(request):
    category = request.GET.get('category', '')
    articles = Article.objects.all()

    if category:
        articles = articles.filter(category__name__iexact=category)

    categories = Category.objects.annotate(count=Count('article'))
    paginator = Paginator(articles, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'news/article_list.html', {
        'articles': page_obj,
        'page_obj': page_obj,
        'category': category,
        'categories': categories,
        'is_paginated': page_obj.has_other_pages()
    })

def article_detail(request, article_id):
    article = get_object_or_404(Article, id=article_id)

    # ✅ Save to reading history if logged in
    if request.user.is_authenticated:
        ReadingHistory.objects.get_or_create(user=request.user, article=article)

    return render(request, 'news/article_detail.html', {
        'article': article
    })

@login_required
def select_preferences(request):
    preference, created = UserPreference.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = PreferenceForm(request.POST, instance=preference)
        if form.is_valid():
            form.save()
            return redirect('personalized_feed')
    else:
        form = PreferenceForm(instance=preference)

    return render(request, 'news/preferences.html', {'form': form})

@login_required
def personalized_feed(request):
    try:
        preferences = request.user.userpreference.categories.all()
        articles = Article.objects.filter(category__in=preferences).order_by('-created_at')
    except UserPreference.DoesNotExist:
        articles = Article.objects.none()

    paginator = Paginator(articles, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'news/personalized_feed.html', {
        'articles': page_obj,
        'page_obj': page_obj
    })

@login_required
def recommendations(request):
    read_ids = ReadingHistory.objects.filter(user=request.user).values_list('article_id', flat=True)
    try:
        preferences = request.user.userpreference.categories.all()
        articles = Article.objects.filter(category__in=preferences).exclude(id__in=read_ids)
    except UserPreference.DoesNotExist:
        articles = Article.objects.none()

    return render(request, 'news/recommendations.html', {'articles': articles})

# ✅ NEW VIEW — Generate Summary on-demand
@login_required
def generate_summary_view(request, article_id):
    if request.method == 'POST':
        article = get_object_or_404(Article, id=article_id)
        try:
            summary = generate_summary(article.content)
            article.summary = summary
            article.save()
            messages.success(request, "Summary generated successfully!")
        except Exception as e:
            messages.error(request, f"Error generating summary: {e}")
    return redirect('article_detail', article_id=article_id)