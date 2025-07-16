
# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"

class Article(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    summary = models.TextField(blank=True)
    source_url = models.URLField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    published_date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    audio_file = models.FileField(upload_to='audio/', blank=True, null=True)
    
    def _str_(self):
        return self.title
    
    class Meta:
        ordering = ['-published_date']

class UserPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    preferred_categories = models.ManyToManyField(Category, blank=True)
    
    def _str_(self):
        return f"{self.user.username}'s preferences"

class ReadingHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True)
    
    def _str_(self):
        return f"{self.user.username} read {self.article.title}"
    class Meta:
        verbose_name_plural = "Reading History"
