import os
import hashlib
from datasets import Dataset
from datetime import date
from typing import List

from src.schemas import ArticleDict, SummaryDict
from src.summarizer import FinNewsSummarizer
from src.sentiment import classify_sentiment
from src.utils.cache import load_from_cache, save_to_cache

from src.cnn import get_cnn_articles


class ArticleProcessor:
    CACHE_DIR = "data/summaries"
    def __init__(self):
        os.makedirs(self.CACHE_DIR, exist_ok=True)
        self.summarizer = FinNewsSummarizer()

        self.cnn_articles = []
        self.processed_articles = []

    def get_processed_articles(self) -> List[SummaryDict]:
        cache_key = f"processed_{date.today()}"
        cached = load_from_cache(key=cache_key, cache_dir=self.CACHE_DIR)
        if cached:
            print("[CACHE] Using cached processed data")
            return cached
        
        self._process_cnn()

        save_to_cache(key=cache_key, data=self.processed_articles, cache_dir=self.CACHE_DIR)
        return self.processed_articles
    
    def _batch_process_articles(self, articles: List[ArticleDict]):
        dataset = Dataset.from_list(articles)
        summaries = self.summarizer.summarize_openai(dataset)

        for article, summary_text in zip(articles, summaries):
            article_id = self._hash(article["url"])
            cache_path = f"{article_id}.json"

            sentiment_label, sentiment_score = classify_sentiment(summary_text)

            summarised = {
                "title": article.get("title", ""),
                "summary": summary_text,
                "description": article.get("description", ""),
                "published_at": article.get("published_at", ""),
                "url": article.get("url", ""),
                "source": article.get("source", ""),
                "sentiment": sentiment_label,
                "sentiment_score": sentiment_score,
                "topics": article.get("topics", []),
                "ticker_sentiment": article.get("ticker_sentiment", []),
            }

            save_to_cache(key=cache_path, data=summarised, cache_dir=self.CACHE_DIR)
            self.processed_articles.append(summarised) 

    def _process_cnn(self):
        print("[INFO] Processing CNN articles")
        self.cnn_articles = get_cnn_articles()
        self._batch_process_articles(self.cnn_articles)

    def _hash(self, text: str) -> str:
        return hashlib.sha1(text.encode()).hexdigest()