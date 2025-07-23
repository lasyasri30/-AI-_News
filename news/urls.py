from django.urls import path
from . import views

urlpatterns = [
    path('article/', views.article_list, name='article_list'),
    path('article/<int:article_id>/', views.article_detail, name='article_detail'),
    path('recommendations/', views.recommendations, name='recommendations'),
    path('preferences/', views.select_preferences, name='preferences'),
    path('feed/', views.personalized_feed, name='personalized_feed'),
    #path('generate-summary/<int:article_id>/', views.generate_summary_view, name='generate_summary_view'),

    path('generate-summary/<int:article_id>/', views.generate_summary_view, name='generate_summary'),

    # Optional: Uncomment this if you have a home view
    # path('', views.home, name='home'),
]
