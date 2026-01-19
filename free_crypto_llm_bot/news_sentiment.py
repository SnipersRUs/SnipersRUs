#!/usr/bin/env python3
"""
News and Sentiment Analysis
Fetches crypto news from RSS feeds and performs sentiment analysis
"""
import feedparser
import requests
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import re

# Try to import sentiment analysis libraries
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False
    try:
        from textblob import TextBlob
        TEXTBLOB_AVAILABLE = True
    except ImportError:
        TEXTBLOB_AVAILABLE = False

logger = logging.getLogger(__name__)


class NewsFetcher:
    """Fetches crypto news from RSS feeds"""

    # Free crypto news RSS feeds
    RSS_FEEDS = {
        "cointelegraph": "https://cointelegraph.com/rss",
        "coindesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "theblock": "https://www.theblock.co/rss.xml",
        "decrypt": "https://decrypt.co/feed"
    }

    def __init__(self):
        """Initialize news fetcher"""
        self.cache = {}
        self.cache_duration = 300  # 5 minutes

    def fetch_news(self, source: Optional[str] = None, limit: int = 5) -> List[Dict]:
        """
        Fetch news from RSS feeds

        Args:
            source: Specific source to fetch from (None = all sources)
            limit: Maximum number of articles to return per source

        Returns:
            List of news articles with title, link, published date, summary
        """
        articles = []

        sources = [source] if source and source in self.RSS_FEEDS else list(self.RSS_FEEDS.keys())

        for feed_name in sources:
            try:
                feed_url = self.RSS_FEEDS[feed_name]
                feed = feedparser.parse(feed_url)

                if feed.bozo:
                    logger.warning(f"Error parsing feed {feed_name}: {feed.bozo_exception}")
                    continue

                for entry in feed.entries[:limit]:
                    # Parse published date
                    published = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        try:
                            published = datetime(*entry.published_parsed[:6])
                        except:
                            pass

                    article = {
                        "title": entry.get('title', 'No title'),
                        "link": entry.get('link', ''),
                        "published": published or datetime.now(),
                        "summary": entry.get('summary', entry.get('description', ''))[:200],
                        "source": feed_name
                    }
                    articles.append(article)

            except Exception as e:
                logger.error(f"Error fetching news from {feed_name}: {e}")
                continue

        # Sort by published date (newest first)
        articles.sort(key=lambda x: x['published'], reverse=True)
        return articles[:limit * len(sources)]

    def format_news_message(self, articles: List[Dict], limit: int = 5) -> str:
        """Format news articles into a Discord-friendly message"""
        if not articles:
            return "❌ No news articles found."

        message = "📰 **Latest Crypto News**\n\n"

        for i, article in enumerate(articles[:limit], 1):
            title = article['title'][:100]  # Truncate long titles
            link = article['link']
            source = article['source'].title()
            published = article['published'].strftime('%Y-%m-%d %H:%M') if article['published'] else "Unknown"

            message += f"{i}. **{title}**\n"
            message += f"   📅 {published} | 📰 {source}\n"
            message += f"   🔗 {link}\n\n"

        return message


class SentimentAnalyzer:
    """Performs sentiment analysis on text"""

    def __init__(self):
        """Initialize sentiment analyzer"""
        if VADER_AVAILABLE:
            self.analyzer = SentimentIntensityAnalyzer()
            self.method = "vader"
        elif TEXTBLOB_AVAILABLE:
            self.method = "textblob"
        else:
            self.method = None
            logger.warning("No sentiment analysis library available. Install vaderSentiment or textblob.")

    def analyze(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment of text

        Args:
            text: Text to analyze

        Returns:
            Dict with 'sentiment' (positive/negative/neutral) and 'score' (-1 to 1)
        """
        if not self.method:
            return {"sentiment": "neutral", "score": 0.0, "error": "No analyzer available"}

        try:
            if self.method == "vader":
                scores = self.analyzer.polarity_scores(text)
                compound = scores['compound']

                if compound >= 0.05:
                    sentiment = "positive"
                elif compound <= -0.05:
                    sentiment = "negative"
                else:
                    sentiment = "neutral"

                return {
                    "sentiment": sentiment,
                    "score": compound,
                    "positive": scores['pos'],
                    "negative": scores['neg'],
                    "neutral": scores['neu']
                }

            elif self.method == "textblob":
                blob = TextBlob(text)
                polarity = blob.sentiment.polarity

                if polarity > 0:
                    sentiment = "positive"
                elif polarity < 0:
                    sentiment = "negative"
                else:
                    sentiment = "neutral"

                return {
                    "sentiment": sentiment,
                    "score": polarity
                }

        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {"sentiment": "neutral", "score": 0.0, "error": str(e)}

    def analyze_news(self, articles: List[Dict]) -> Dict[str, any]:
        """
        Analyze sentiment of multiple news articles

        Args:
            articles: List of news article dicts

        Returns:
            Dict with overall sentiment and per-article analysis
        """
        if not articles:
            return {"overall_sentiment": "neutral", "overall_score": 0.0, "articles": []}

        article_sentiments = []
        total_score = 0.0

        for article in articles:
            # Combine title and summary for analysis
            text = f"{article.get('title', '')} {article.get('summary', '')}"
            sentiment_data = self.analyze(text)

            article_sentiment = {
                "title": article.get('title', ''),
                "sentiment": sentiment_data.get('sentiment', 'neutral'),
                "score": sentiment_data.get('score', 0.0)
            }
            article_sentiments.append(article_sentiment)
            total_score += sentiment_data.get('score', 0.0)

        # Calculate overall sentiment
        avg_score = total_score / len(articles) if articles else 0.0

        if avg_score >= 0.05:
            overall_sentiment = "positive"
        elif avg_score <= -0.05:
            overall_sentiment = "negative"
        else:
            overall_sentiment = "neutral"

        return {
            "overall_sentiment": overall_sentiment,
            "overall_score": avg_score,
            "articles": article_sentiments
        }

    def format_sentiment_message(self, sentiment_data: Dict) -> str:
        """Format sentiment analysis into a Discord-friendly message"""
        overall = sentiment_data.get('overall_sentiment', 'neutral')
        score = sentiment_data.get('overall_score', 0.0)

        # Emoji based on sentiment
        emoji_map = {
            "positive": "🟢",
            "negative": "🔴",
            "neutral": "🟡"
        }
        emoji = emoji_map.get(overall, "🟡")

        message = f"{emoji} **Market Sentiment: {overall.upper()}**\n"
        message += f"📊 **Score:** {score:.3f} ({'Positive' if score > 0 else 'Negative' if score < 0 else 'Neutral'})\n\n"

        articles = sentiment_data.get('articles', [])
        if articles:
            message += "**Article Sentiments:**\n"
            for article in articles[:5]:  # Show top 5
                title = article['title'][:60]
                sent = article['sentiment']
                sent_emoji = emoji_map.get(sent, "🟡")
                message += f"{sent_emoji} {title}... ({sent})\n"

        return message



