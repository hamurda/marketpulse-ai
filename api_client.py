from abc import ABC, abstractmethod
from typing import List, TypedDict
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
        print("fetch_latest_articles")
        params = {
            "apiKey": self.api_key,
            "country": country,
            "pageSize": page_size,
        }
        if category:
            params["category"] = category

        try:
            response = requests.get(self.BASE_URL, params=params)
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

        return articles