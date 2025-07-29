import feedparser
import requests
import os
import logging
from gtts import gTTS
from django.conf import settings
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from django.utils import timezone as dj_timezone
from newspaper import Article as NewsArticle
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from collections import Counter
import re

# NLTK Downloads
nltk.download('punkt')
nltk.download('stopwords')

logger = logging.getLogger(__name__)

# ✅ Clean HTML using BeautifulSoup
def clean_html(raw_html):
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, 'html.parser')
    return soup.get_text(separator=' ', strip=True)

# ✅ Guess category based on keywords
def guess_category(title, content):
    categories = {
        "Lifestyle": ["lifestyle", "daily life", "routine", "fashion", "travel", "shopping", "home", "kitchen", "product", "comfort"],
        "Health": ["health", "medical", "hospital", "virus", "doctor", "vaccine", "fitness", "mental", "exercise"],
        "Technology": ["technology", "tech", "AI", "robot", "software", "hardware", "app"],
        "Education": ["education", "school", "student", "college", "exam", "university", "learning", "classroom"],
        "Politics": ["politics", "government", "election", "minister", "law", "president", "policy"],
        "Business": ["business", "stock", "market", "company", "investment", "trade", "economy"],
        "Entertainment": ["movie", "actor", "music", "series", "film", "celebrity"],
        "Sports": ["sports", "match", "tournament", "player", "cricket", "football", "olympics"],
        "Science": ["science", "space", "nasa", "experiment", "research", "climate", "environment"]
    }

    text = f"{title} {content}".lower()
    for cat, keywords in categories.items():
        if any(kw in text for kw in keywords):
            return cat
    return "General"

# ✅ Fetch news from RSS and parse content
def fetch_news_from_rss(feed_url, source_name):
    articles_data = []

    try:
        response = requests.get(feed_url, headers={'User-Agent': 'ByteNewsScraper/1.0'}, timeout=10)
        response.raise_for_status()
        feed = feedparser.parse(response.content)

        for entry in feed.entries:
            title = entry.get('title', 'No title')
            link = entry.get('link')
            cleaned_content = ""

            try:
                article = NewsArticle(link)
                article.download()
                article.parse()
                cleaned_content = clean_html(article.text)

                if len(cleaned_content.strip()) < 300:
                    fallback = requests.get(link, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
                    soup = BeautifulSoup(fallback.content, 'html.parser')
                    paragraphs = soup.find_all('p')
                    fallback_text = " ".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
                    if len(fallback_text.strip()) > 300:
                        cleaned_content = fallback_text
            except Exception as e:
                print(f"❌ Error parsing article: {e}")
                cleaned_content = "No content available."

            if not cleaned_content:
                cleaned_content = "No content available."

            raw_summary = entry.get('summary', '')
            cleaned_summary = clean_html(raw_summary) or "No summary available."

            published_date = dj_timezone.now()
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)

            category_guess = guess_category(title, cleaned_content)

            articles_data.append({
                'title': title,
                'link': link,
                'content': cleaned_content,
                'summary': cleaned_summary,
                'publication_date': published_date,
                'source': source_name,
                'guessed_category': category_guess
            })

        return articles_data

    except Exception as e:
        print(f"❌ Failed to fetch news: {e}")
        return []

# ✅ Clean summary text before audio
def clean_text_for_audio(text):
    if not text:
        return ""

    text = re.sub(r'\bShare Save\b', '', text)
    text = re.sub(r'\d+\s+(minutes|minute|hours|hour|days|day)\s+ago', '', text, flags=re.IGNORECASE)
    text = re.sub(r'BBC News.*?(in \w+)?', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Getty Images', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()[:800]

# ✅ Generate audio from summary
def generate_audio_summary(text, article_id):
    if not text:
        logger.warning(f"No text provided for audio: article_id {article_id}")
        return None

    clean_text = clean_text_for_audio(text)
    if not clean_text:
        logger.warning(f"Cleaned text is empty for article {article_id}")
        return None

    timestamp = int(datetime.now().timestamp())
    filename = f"summary_{article_id}_{timestamp}.mp3"

    audio_dir = os.path.join(settings.MEDIA_ROOT, 'news_audio')
    os.makedirs(audio_dir, exist_ok=True)
    filepath = os.path.join(audio_dir, filename)

    try:
        tts = gTTS(text=clean_text, lang='en')
        tts.save(filepath)
        logger.info(f"🎧 Audio saved at {filepath}")
        return os.path.join(settings.MEDIA_URL, 'news_audio', filename)
    except Exception as e:
        logger.error(f"❌ Audio generation failed: {e}")
        return None

# ✅ Summary Generator
def generate_summary(text, article_title="", length='medium', num_sentences=None):
    if not text or not isinstance(text, str):
        return "No content available to summarize."

    length_map = {'short': 2, 'medium': 3, 'long': 5}
    num_sentences = num_sentences or length_map.get(length, 3)

    sentences = sent_tokenize(text)
    if len(sentences) <= num_sentences:
        return text

    words = word_tokenize(text.lower())
    stop_words = set(stopwords.words('english'))
    filtered_words = [w for w in words if w.isalnum() and w not in stop_words]
    word_frequencies = Counter(filtered_words)

    if article_title:
        title_words = word_tokenize(article_title.lower())
        for word in title_words:
            if word in word_frequencies:
                word_frequencies[word] += 0.5

    sentence_scores = {}
    for i, sentence in enumerate(sentences):
        for word in word_tokenize(sentence.lower()):
            if word in word_frequencies:
                sentence_scores[i] = sentence_scores.get(i, 0) + word_frequencies[word]
        if i == 0:
            sentence_scores[i] += 1.0
        elif i == 1:
            sentence_scores[i] += 0.5

    top_indices = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)[:num_sentences]
    selected_sentences = sorted([i for i, _ in top_indices])
    return " ".join(sentences[i] for i in selected_sentences)
