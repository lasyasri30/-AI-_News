# news/utils.py
# news/utils.py

import feedparser
import requests
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from django.utils import timezone as dj_timezone
from newspaper import Article as NewsArticle  # For full article fallback

def clean_html(raw_html):
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, 'html.parser')
    return soup.get_text(separator=' ', strip=True)

def fetch_news_from_rss(feed_url, source_name):
    articles_data = []

    try:
        response = requests.get(
            feed_url,
            headers={'User-Agent': 'ByteNewsScraper/1.0'},
            timeout=10
        )
        response.raise_for_status()
        feed = feedparser.parse(response.content)

        for entry in feed.entries:
            title = entry.get('title', 'No title')
            link = entry.get('link')

            # Try content > summary > description
            raw_content = ""
            if 'content' in entry and entry['content']:
                raw_content = entry['content'][0].get('value', '')
            elif 'summary' in entry:
                raw_content = entry['summary']
            elif 'description' in entry:
                raw_content = entry['description']

            cleaned_content = clean_html(raw_content)

            # Fallback using newspaper3k if content is short or missing
            if (not cleaned_content or len(cleaned_content.strip()) < 100) and 'cnn-underscored' not in link:
                try:
                    news_article = NewsArticle(link)
                    news_article.download()
                    news_article.parse()
                    cleaned_content = clean_html(news_article.text)
                except Exception as e:
                    print(f"🛑 Failed to fetch full content for {title}: {e}")

            # Still fallback to placeholder
            if not cleaned_content or cleaned_content.strip() == "":
                cleaned_content = "No content available."

            # Extract summary separately for cards/listing
            raw_summary = entry.get('summary', '')
            cleaned_summary = clean_html(raw_summary) or "No summary available."

            # Published date fallback
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            else:
                published_date = dj_timezone.now()

            articles_data.append({
                'title': title,
                'link': link,
                'content': cleaned_content,
                'summary': cleaned_summary,
                'publication_date': published_date,
                'source': source_name
            })

        return articles_data

    except requests.exceptions.RequestException as e:
        print(f"Error fetching RSS feed from {source_name}: {e}")
        return []
    except Exception as e:
        print(f"An error occurred during RSS parsing for {source_name}: {e}")
        return []
# text_summ
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer

def generate_summary(text, num_sentences=3):
    """
    Generates a summary of the given text using the LSA algorithm.
    """
    try:
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LsaSummarizer()
        summary = summarizer(parser.document, num_sentences)
        return ' '.join(str(sentence) for sentence in summary)
    except Exception as e:
        print(f"Summary generation failed: {e}")
        return "Summary not available."
