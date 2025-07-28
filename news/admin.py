from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import redirect
from django.contrib import messages
from django.conf import settings
from django.db.models import Count
import os

from .models import (
    Category,
    Article,
    UserPreference,
    ReadingHistory,
    SummaryFeedback,
)
from .utils import generate_audio_summary


# ✅ Summary Feedback
admin.site.register(SummaryFeedback)


# ✅ Category Admin
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']


# ✅ Article Admin with custom audio regeneration logic
@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'approved', 'published_date', 'created_at']
    list_filter = ['category', 'approved', 'published_date']
    search_fields = ['title', 'content']
    readonly_fields = ['created_at', 'audio_file']
    fields = [
        'title', 'category', 'source', 'source_url',
        'content', 'summary', 'audio_file',
        'approved', 'published_date', 'created_at'
    ]
    change_form_template = "admin/news/article/change_form.html"

    # ✅ Bulk actions
    actions = ['approve_articles', 'mark_as_pending']

    @admin.action(description='✅ Approve selected articles')
    def approve_articles(self, request, queryset):
        updated = queryset.update(approved=True)
        self.message_user(request, f"{updated} article(s) marked as approved.")

    @admin.action(description='❌ Mark selected as pending')
    def mark_as_pending(self, request, queryset):
        updated = queryset.update(approved=False)
        self.message_user(request, f"{updated} article(s) marked as pending.")

    # ✅ Override changelist view to include article stats
    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        if hasattr(response, 'context_data'):
            try:
                qs = response.context_data['cl'].queryset
            except (AttributeError, KeyError):
                qs = Article.objects.all()

            response.context_data['article_stats'] = {
                'total': qs.count(),
                'approved': qs.filter(approved=True).count(),
                'pending': qs.filter(approved=False).count()
            }
        return response

    # ✅ Save model: regenerate audio when summary is changed manually
    def save_model(self, request, obj, form, change):
        if change and 'summary' in form.changed_data:
            audio_path = generate_audio_summary(obj.summary, obj.id)
            if audio_path:
                relative_path = os.path.relpath(audio_path, settings.MEDIA_ROOT)
                obj.audio_file.name = relative_path
        super().save_model(request, obj, form, change)

    # ✅ Add admin URL for manual audio regeneration
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:article_id>/regenerate-audio/',
                self.admin_site.admin_view(self.regenerate_audio_view),
                name='regenerate-audio',
            ),
        ]
        return custom_urls + urls

    def regenerate_audio_view(self, request, article_id):
        article = Article.objects.get(id=article_id)
        try:
            audio_url = generate_audio_summary(article.summary, article.id)
            if audio_url:
                relative_path = os.path.relpath(audio_url, settings.MEDIA_ROOT)
                article.audio_file.name = relative_path
                article.save()
                self.message_user(request, "✅ Audio regenerated successfully.")
            else:
                self.message_user(request, "❌ Failed to generate audio.", level=messages.ERROR)
        except Exception as e:
            self.message_user(request, f"❌ Error: {e}", level=messages.ERROR)

        return redirect(f'../../{article_id}/change/')


# ✅ User Preferences Admin
@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user']
    filter_horizontal = ['categories']


# ✅ Reading History Admin
@admin.register(ReadingHistory)
class ReadingHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'article', 'read_at']
    list_filter = ['read_at']
    readonly_fields = ['read_at']
