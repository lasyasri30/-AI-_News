from django.core.management.base import BaseCommand
from django.utils import timezone
from news.utils import fetch_news_from_rss
from news.models import Article, Category
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Scrapes news articles from multiple RSS feeds and saves them.'

    def handle(self, *args, **kwargs):
        self.stdout.write("🔄 Starting multi-source news scraping...")

        NEWS_SOURCES = {
            'BBC News': "https://feeds.bbci.co.uk/news/rss.xml",
            'CNN': "http://rss.cnn.com/rss/cnn_topstories.rss",
            'Reuters': "http://feeds.reuters.com/reuters/topNews",
        }

        total_articles_added = 0

        for source_name, feed_url in NEWS_SOURCES.items():
            self.stdout.write(f"📡 Fetching from {source_name} ({feed_url})...")
            logger.info(f"Fetching from {source_name}")

            articles_data = fetch_news_from_rss(feed_url, source_name)

            if not articles_data:
                self.stdout.write(self.style.WARNING(f"⚠️ No articles fetched from {source_name}."))
                continue

            articles_added_from_source = 0

            for article_data in articles_data:
                try:
                    # Ensure 'General' category exists
                    general_category, _ = Category.objects.get_or_create(name='General')

                    # Skip if duplicate
                    if not Article.objects.filter(link=article_data['link']).exists():
                        Article.objects.create(
                            title=article_data['title'],
                            content=article_data['content'],
                            summary=article_data['summary'],
                            published_date=article_data.get('publication_date') or timezone.now(),
                            source=article_data.get('source', 'Unknown'),
                            link=article_data['link'],
                            source_url=article_data['link'],
                            category=general_category
                        )
                        articles_added_from_source += 1
                    else:
                        logger.info(f"Skipping duplicate article: {article_data['title']}")

                except Exception as e:
                    logger.error(
                        f"❌ Error saving article from {source_name}: {e} - {article_data.get('title', 'N/A')}"
                    )

            self.stdout.write(
                self.style.SUCCESS(f"✅ Added {articles_added_from_source} new articles from {source_name}")
            )
            total_articles_added += articles_added_from_source

        self.stdout.write(self.style.SUCCESS(f"🏁 Finished. Total new articles: {total_articles_added}"))
