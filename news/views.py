from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST

from .models import Article, Category, UserPreference, ReadingHistory, SummaryFeedback
from .forms import PreferenceForm
from .utils import generate_summary

# ✅ 1. Homepage — You can improve this later by adding top stories or featured articles
def home(request):
    return HttpResponse("🎉 Welcome to ByteNews Homepage!")

# ✅ 2. Article List View — only approved
def article_list(request):
    category = request.GET.get('category', '')
    search_query = request.GET.get('search', '')
    articles = Article.objects.filter(approved=True)

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
        'search_query': search_query,
        'categories': categories,
        'is_paginated': page_obj.has_other_pages()
    })

# ✅ 3. Article Detail — only approved unless staff
def article_detail(request, article_id):
    if request.user.is_staff:
        article = get_object_or_404(Article, id=article_id)
    else:
        article = get_object_or_404(Article, id=article_id, approved=True)

    if request.user.is_authenticated:
        ReadingHistory.objects.get_or_create(user=request.user, article=article)

    return render(request, 'news/article_detail.html', {
        'article': article
    })

# ✅ 4. Select Preferences
@login_required
def select_preferences(request):
    preference, _ = UserPreference.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = PreferenceForm(request.POST, instance=preference)
        if form.is_valid():
            form.save()
            return redirect('personalized_feed')
    else:
        form = PreferenceForm(instance=preference)

    return render(request, 'news/preferences.html', {'form': form})

# ✅ 5. Personalized Feed — only approved
@login_required
def personalized_feed(request):
    try:
        preferences = request.user.userpreference.categories.all()
        articles = Article.objects.filter(category__in=preferences, approved=True).order_by('-created_at')
    except UserPreference.DoesNotExist:
        articles = Article.objects.none()

    paginator = Paginator(articles, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'news/personalized_feed.html', {
        'articles': page_obj,
        'page_obj': page_obj
    })

# ✅ 6. Recommendations — only approved
@login_required
def recommendations(request):
    read_ids = ReadingHistory.objects.filter(user=request.user).values_list('article_id', flat=True)
    try:
        preferences = request.user.userpreference.categories.all()
        articles = Article.objects.filter(category__in=preferences, approved=True).exclude(id__in=read_ids)
    except UserPreference.DoesNotExist:
        articles = Article.objects.none()

    return render(request, 'news/recommendations.html', {'articles': articles})

# ✅ 7. Summary Generation
@login_required
def generate_summary_view(request, article_id):
    if request.method == 'POST':
        article = get_object_or_404(Article, id=article_id)
        try:
            num_sentences = int(request.POST.get('num_sentences', 3))
            summary = generate_summary(article.content, article_title=article.title, num_sentences=num_sentences)
            article.summary = summary
            article.save()
            messages.success(request, "✅ Summary generated successfully!")
        except Exception as e:
            messages.error(request, f"❌ Error generating summary: {e}")
    return redirect('article_detail', article_id=article_id)

# ✅ 8. Summary Feedback
@login_required
@require_POST
def submit_summary_feedback(request, pk):
    article = get_object_or_404(Article, pk=pk)
    is_helpful = request.POST.get('is_helpful')

    if is_helpful is not None:
        is_helpful_bool = (is_helpful.lower() == 'true')
        feedback, created = SummaryFeedback.objects.update_or_create(
            user=request.user,
            article=article,
            defaults={'is_helpful': is_helpful_bool}
        )

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'helpful': is_helpful_bool, 'created': created})

        messages.success(request, '✅ Thank you for your feedback!')
        return redirect('article_detail', article_id=pk)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'error', 'message': 'Invalid feedback'}, status=400)

    messages.error(request, '❌ Invalid feedback.')
    return redirect('article_detail', article_id=pk)

# ✅ 9. Reading History
@login_required
def reading_history(request):
    history_entries = (
        ReadingHistory.objects
        .filter(user=request.user)
        .select_related('article')
        .order_by('-read_at')
    )
    articles = [entry.article for entry in history_entries]
    paginator = Paginator(articles, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'news/reading_history.html', {
        'articles': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
    })

# ✅ 10. Clear History
@login_required
def clear_history(request):
    ReadingHistory.objects.filter(user=request.user).delete()
    messages.success(request, "✅ Reading history cleared.")
    return redirect('reading_history')
