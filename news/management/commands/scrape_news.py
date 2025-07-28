# news/management/commands/scrape_news.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from news.utils import fetch_news_from_rss, generate_summary, generate_audio_summary
from news.models import Article, Category
from django.conf import settings
import logging
import os
import requests

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Scrapes news articles from multiple RSS feeds and saves them.'

    def handle(self, *args, **kwargs):
        self.stdout.write("🔄 Starting multi-source news scraping...\n")

        NEWS_SOURCES = {
            'BBC News': "https://feeds.bbci.co.uk/news/rss.xml",
            'CNN': "http://rss.cnn.com/rss/cnn_topstories.rss",
            'Reuters': "https://feeds.reuters.com/reuters/topNews",
        }

        total_articles_added = 0

        for source_name, feed_url in NEWS_SOURCES.items():
            self.stdout.write(f"📡 Fetching from {source_name} ({feed_url})...")
            logger.info(f"Fetching from {source_name}...")

            articles_data = fetch_news_from_rss(feed_url, source_name)

            if not articles_data:
                self.stdout.write(self.style.WARNING(f"⚠️ No articles fetched from {source_name}.\n"))
                continue

            articles_added_from_source = 0

            for article_data in articles_data:
                try:
                    # Get or create category
                    category_name = article_data.get('guessed_category', 'General')
                    category_obj, _ = Category.objects.get_or_create(name=category_name)

                    # Check for duplicates using the link
                    if not Article.objects.filter(link=article_data['link']).exists():
                        # Generate summary
                        article_summary = article_data.get('summary')
                        if not article_summary:
                            article_summary = generate_summary(
                                article_data['content'],
                                article_data['title'],
                                length='medium'  # ✅ NEW: choose summary length
                            )

                        # First save the article (without audio)
                        article = Article.objects.create(
                            title=article_data['title'],
                            content=article_data['content'],
                            summary=article_summary,
                            published_date=article_data.get('publication_date') or timezone.now(),
                            source=article_data.get('source', 'Unknown'),
                            link=article_data['link'],
                            source_url=article_data['link'],
                            category=category_obj,
                            approved=False  # new articles start as pending
                        )

                        # Now generate audio
                        audio_url = generate_audio_summary(article_summary, article.id)
                        if audio_url:
                            relative_path = os.path.relpath(audio_url, settings.MEDIA_URL)
                            article.audio_file.name = relative_path
                            article.save()

                        articles_added_from_source += 1
                        self.stdout.write(f"   ✅ Saved: {article.title[:60]}... [{category_name}]")

                    else:
                        logger.info(f"Skipping duplicate: {article_data['title']}")

                except Exception as e:
                    logger.error(
                        f"❌ Error saving article from {source_name}: {e} - {article_data.get('title', 'N/A')}"
                    )
                    self.stdout.write(self.style.ERROR(f"❌ Failed to save: {article_data.get('title', '')[:60]}"))

            self.stdout.write(
                self.style.SUCCESS(f"✅ Added {articles_added_from_source} new articles from {source_name}\n")
            )
            total_articles_added += articles_added_from_source

        self.stdout.write(self.style.SUCCESS(f"🏁 Finished. Total new articles: {total_articles_added}"))
