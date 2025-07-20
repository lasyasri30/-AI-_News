from django.urls import path
from . import views

urlpatterns = [
    path('article/', views.article_list, name='article_list'),
    path('article/<int:article_id>/', views.article_detail, name='article_detail'),
    path('recommendations/', views.recommendations, name='recommendations'),
    path('preferences/', views.select_preferences, name='preferences'),
    path('feed/', views.personalized_feed, name='personalized_feed'),
    #path('home/', views.home, name='home'),

]