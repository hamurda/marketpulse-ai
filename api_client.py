from abc import ABC, abstractmethod
from typing import List, TypedDict
from datetime import datetime, timedelta
from utils.cache import save_to_cache, load_from_cache
import requests


# --- Article Schema ---
class ArticleDict(TypedDict):
    title: str
    description: str
    content: str
    published_at: str
    url: str
    source: str


# --- Base Client ---
class BaseNewsAPIClient(ABC):
    def __init__(self, api_key: str):
        self.api_key = api_key

    @abstractmethod
    def fetch_latest_articles(self, **kwargs) -> List[ArticleDict]:
        pass


# --- NewsAPI Client ---
class NewsAPIClient(BaseNewsAPIClient):
    BASE_URL = "https://newsapi.org/v2/top-headlines"

    def fetch_latest_articles(self, country: str="us", category: str = None, page_size: int = 50) -> List[ArticleDict]:
        cache_key = f"newsapi_{country}_{category}_{page_size}"
        cached = load_from_cache(cache_key)
        if cached:
            print("[CACHE] Using cached NewsAPI data")
            return cached
        
        headers = {"X-Api-Key":self.api_key}
        params = {
            "apiKey": self.api_key,
            "country": country,
            "pageSize": page_size,
            "language": "en",
        }
        if category:
            params["category"] = category

        try:
            response = requests.get(self.BASE_URL, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            print(f"[ERROR] Failed to fetch articles: {e}")
            return []

        articles = []
        for item in data.get("articles", []):
            article: ArticleDict = {
                "title": item.get("title", ""),
                "description": item.get("description", ""),
                "content": item.get("content") or item.get("description", ""),
                "published_at": item.get("publishedAt", ""),
                "url": item.get("url", ""),
                "source": item.get("source", {}).get("name", "")
            }

            articles.append(article)

        save_to_cache(cache_key, articles)
        return articles
    

class AlphaVantageAPIClient(BaseNewsAPIClient):
    BASE_URL = "https://www.alphavantage.co/query"

    def fetch_latest_articles(self, tickers: str = "", topics: str = "") -> List[ArticleDict]:
        cache_key = f"alpha_{tickers}_{topics}"
        cached = load_from_cache(cache_key)
        if cached:
            print("[CACHE] Using cached Alpha Vantage data")
            return cached
        
        print("API CALLED")
        
        params = {
            "function": "NEWS_SENTIMENT",
            "apikey": self.api_key,
        }
        if tickers:
            params["tickers"] = tickers
        if topics:
            params["topics"] = topics

        today = datetime.now()
        two_weeks_ago = today - timedelta(days=14)
        params["time_from"] = two_weeks_ago.strftime("%Y%m%dT%H%M%S")
        params["time_to"] = today.strftime("%Y%m%dT%H%M%S")

        try:
            response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            print(f"[ERROR] Failed to fetch Alpha Vantage articles: {e}")
            return []

        articles = []
        for item in data.get("feed", []):
            print(item)
            article: ArticleDict = {
                "title": item.get("title", ""),
                "description": item.get("summary", ""),
                "content": item.get("summary", ""),
                "published_at": item.get("time_published", ""),
                "url": item.get("url", ""),
                "source": item.get("source_domain", "")
            }

            articles.append(article)

        save_to_cache(cache_key, articles)
        return articles
