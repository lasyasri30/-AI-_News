from django.urls import path
from . import views

urlpatterns = [
    path('article/', views.article_list, name='article_list'),
    path('article/<int:article_id>/', views.article_detail, name='article_detail'),
    path('recommendations/', views.recommendations, name='recommendations'),
    path('preferences/', views.select_preferences, name='preferences'),
    path('feed/', views.personalized_feed, name='personalized_feed'),
    path('article/<int:article_id>/regenerate_summary/', views.generate_summary_view, name='generate_summary'),
    path('article/<int:pk>/feedback/', views.submit_summary_feedback, name='submit_summary_feedback'),
    path('article/<int:pk>/generate_audio_ajax/', views.generate_audio_ajax, name='generate_audio_ajax'),  # ✅ New AJAX URL
    path('history/', views.reading_history, name='reading_history'),
    path('history/clear/', views.clear_history, name='clear_history'),
]
