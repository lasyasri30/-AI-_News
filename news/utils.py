import feedparser
import requests
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from django.utils import timezone as dj_timezone
from newspaper import Article as NewsArticle
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from collections import Counter

nltk.download('punkt')
nltk.download('stopwords')

def clean_html(raw_html):
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, 'html.parser')
    return soup.get_text(separator=' ', strip=True)


def guess_category(title, content):
    categories = {
        "Lifestyle": ["top", "lifestyle", "daily life", "routine", "fashion", "travel", "shopping", "tips", "home", "kitchen", "product", "comfort"],
        "Health": ["health", "medical", "hospital", "virus", "doctor", "vaccine", "fitness", "mental", "exercise"],
        "Technology": ["technology", "tech", "AI", "robot", "software", "hardware", "app"],
        "Education": ["education", "school", "student", "college", "exam", "university", "learning", "classroom", "courses"],
        "Politics": ["politics", "government", "election", "minister", "law", "president", "policy", "senate", "votes", "voter"],
        "Business": ["business", "stock", "market", "company", "investment", "trade", "economy", "startup"],
        "Entertainment": ["movie", "actor", "music", "series", "film", "celebrity", "drama", "hollywood"],
        "Sports": ["sports", "match", "tournament", "player", "cricket", "football", "olympics", "score"],
        "Science": ["science", "space", "nasa", "experiment", "research", "climate", "environment"]
    }

    # Combine title and content into one searchable string
    text = f"{title} {content}".lower()

    # Ordered check for categories to control priority
    for cat in [
        "Lifestyle", "Health", "Technology", "Education",
        "Politics", "Business", "Entertainment", "Sports", "Science"
    ]:
        keywords = categories[cat]
        if any(kw.lower() in text for kw in keywords):
            print(f"🧠 Assigned category: {cat} for title: {title}")
            return cat

    print(f"🧠 Defaulted to General for: {title}")
    return "General"




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
            raw_content = ""

            # Prefer content, fallback to summary or description
            if 'content' in entry and entry['content']:
                raw_content = entry['content'][0].get('value', '')
            elif 'summary' in entry:
                raw_content = entry['summary']
            elif 'description' in entry:
                raw_content = entry['description']

            cleaned_content = clean_html(raw_content)

            # If content is too short, try fetching full article
            if (not cleaned_content or len(cleaned_content.strip()) < 100) and 'cnn-underscored' not in link and '/videos/' not in link:
                try:
                    news_article = NewsArticle(link)
                    news_article.download()
                    news_article.parse()
                    cleaned_content = clean_html(news_article.text)

                    # Fallback: If still too short, try BeautifulSoup scraping
                    if len(cleaned_content.strip()) < 100:
                        print(f"⚠️ Newspaper3k content too short for: {title}. Trying fallback scraping...")
                        try:
                            fallback_response = requests.get(link, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
                            soup = BeautifulSoup(fallback_response.content, 'html.parser')
                            paragraphs = soup.find_all('p')
                            fallback_text = " ".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
                            if len(fallback_text.strip()) > 100:
                                cleaned_content = fallback_text
                        except Exception as fallback_error:
                            print(f"🛑 Fallback scraping also failed: {fallback_error}")
                except Exception as e:
                    print(f"🛑 Failed to fetch full content for {title}: {e}")

            # Final content check
            if not cleaned_content or cleaned_content.strip() == "":
                cleaned_content = "No content available."

            # Summary and publication date
            raw_summary = entry.get('summary', '')
            cleaned_summary = clean_html(raw_summary) or "No summary available."

            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            else:
                published_date = dj_timezone.now()

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

    except requests.exceptions.RequestException as e:
        print(f"Error fetching RSS feed from {source_name}: {e}")
        return []
    except Exception as e:
        print(f"An error occurred during RSS parsing for {source_name}: {e}")
        return []

def generate_summary(text, article_title="", num_sentences=3):
    if not text or not isinstance(text, str):
        return "No content available to summarize."

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
            sentence_scores[i] = sentence_scores.get(i, 0) + 1.0
        elif i == 1:
            sentence_scores[i] = sentence_scores.get(i, 0) + 0.5

    top_indices = sorted(
        sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)[:num_sentences]
    )
    summary = " ".join(sentences[i] for i, _ in top_indices)
    return summary
