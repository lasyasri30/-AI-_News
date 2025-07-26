from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Category,
    Article,
    UserPreference,
    ReadingHistory,
    SummaryFeedback,
)

# ✅ Register Summary Feedback directly
admin.site.register(SummaryFeedback)

# ✅ Category Admin
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']


# ✅ Article Admin with bulk approval workflow
@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'approved', 'published_date', 'created_at']
    list_filter = ['category', 'approved', 'published_date']
    search_fields = ['title', 'content']
    readonly_fields = ['created_at']
    fields = [
    'title', 'category', 'source', 'source_url',
    'content', 'summary', 'audio_file',  # 👈 include this!
    'approved', 'published_date', 'created_at'
]

    change_list_template = "admin/news/article/change_list.html"

    
    # ✅ Custom bulk actions
    actions = ['approve_articles', 'mark_as_pending']

    @admin.action(description='✅ Approve selected articles')
    def approve_articles(self, request, queryset):
        updated = queryset.update(approved=True)
        self.message_user(request, f"{updated} article(s) marked as approved.")

    @admin.action(description='❌ Mark selected as pending')
    def mark_as_pending(self, request, queryset):
        updated = queryset.update(approved=False)
        self.message_user(request, f"{updated} article(s) marked as pending.")

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        try:
            qs = response.context_data['cl'].queryset
        except (AttributeError, KeyError):
            qs = Article.objects.all()

        total = qs.count()
        approved = qs.filter(approved=True).count()
        pending = qs.filter(approved=False).count()

        response.context_data['article_stats'] = {
            'total': total,
            'approved': approved,
            'pending': pending
        }
        return response

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

