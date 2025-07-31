from rest_framework import serializers
from .models import Article, Category, SummaryFeedback, UserPreference

class ArticleSerializer(serializers.ModelSerializer):
    categories = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Article
        fields = ['id', 'title', 'summary', 'link', 'published_date', 'source', 'categories', 'audio_file']

class UserPreferenceSerializer(serializers.ModelSerializer):
    categories = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        many=True
    )

    class Meta:
        model = UserPreference
        fields = ['id', 'user', 'categories']
        read_only_fields = ['user']  # user will be set from the view
