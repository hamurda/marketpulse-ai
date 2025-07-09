import os
import hashlib
from datetime import date
from typing import List
from dotenv import load_dotenv

from src.schemas import ArticleDict, SummaryDict
from src.summarizer import FinNewsSummarizer
from src.sentiment import classify_sentiment
from src.utils.cache import load_from_cache, save_to_cache

from clients.api_client import NewsAPIClient, AlphaVantageAPIClient
from clients.cnn import get_cnn_articles

class ArticleProcessor:
    def __init__(self, cache_dir="data/summaries"):
        os.makedirs(cache_dir, exist_ok=True)
        self.cache_dir = cache_dir
        self.summarizer = FinNewsSummarizer(cache_dir=cache_dir)

        self.news_api_articles = []
        self.alpha_articles = []
        self.cnn_articles = []
        self.processed_articles = []
    
    def get_processed_articles(self) -> List[SummaryDict]:
        cache_key = f"processed_{date.today()}"
        cached = load_from_cache(cache_key)
        if cached:
            print("[CACHE] Using cached processed data")
            return cached
        
        self._process_cnn()
        self._process_alpha()
        self._process_news_api()

        save_to_cache(cache_key, self.processed_articles)
        return self.processed_articles


    def get_processed_article(self, article: ArticleDict) -> SummaryDict:
        article_id = self._hash(article["url"])
        cache_path = os.path.join(self.cache_dir, f"{article_id}.json")
        if os.path.exists(cache_path):
            return load_from_cache(cache_path)
        
        return self._process_article(article=article)
    
    def _process_article(self, article: ArticleDict) -> SummaryDict:     
        article_id = self._hash(article["url"])
        cache_path = os.path.join(self.cache_dir, f"{article_id}.json")

        summarised = self.summarizer.summarize(article)
        sentiment_label, sentiment_score = classify_sentiment(summarised['summary'])

        summarised["sentiment"]=sentiment_label
        summarised["sentiment_score"]=sentiment_score
    
        save_to_cache(summarised, cache_path)
        return summarised

    def _process_cnn(self):
        print("[INFO] Processing CNN articles")
        self.cnn_articles = get_cnn_articles()

        for item in self.cnn_articles:
            processed = self.get_processed_article(item)
            self.processed_articles.append(processed)
        
    def _process_alpha(self):
        print("[INFO] Processing Alpha Vantage articles")
        load_dotenv()
        alpha_key = os.getenv("ALPHA_VANTAGE_KEY")
        if not alpha_key:
            print("[WARN] ALPHA_VANTAGE_KEY not set.")
            return
        self.alpha_articles = AlphaVantageAPIClient(alpha_key).fetch_latest_articles()

        for item in self.alpha_articles:
            processed = self.get_processed_article(item)
            self.processed_articles.append(processed)
        
    def _process_news_api(self):
        print("[INFO] Processing News API articles")
        load_dotenv()
        news_key = os.getenv("NEWS_API_KEY")
        if not news_key:
            print("[WARN] NEWS_API_KEY not set.")
            return
        self.news_api_articles = NewsAPIClient(news_key).fetch_latest_articles()

        for item in self.news_api_articles:
            processed = self.get_processed_article(item)
            self.processed_articles.append(processed)

    def _hash(self, text: str) -> str:
        return hashlib.sha1(text.encode()).hexdigest()


    


