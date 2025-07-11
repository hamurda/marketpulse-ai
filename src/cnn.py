import streamlit as st
import requests
from datetime import date
from typing import List, Dict
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from src.utils.cache import load_from_cache, save_to_cache

TTL = 24 * 60 * 60  # 24 hours

@st.cache_data(ttl=TTL)
def get_cnn_articles() -> List[Dict]:
    cache_key = f"cnn_{date.today()}"
    cached = load_from_cache(cache_key)
    if cached:
        print("[CACHE] Using cached CNN news")
        return cached

    articles = _scrape_cnn_investing()
    return articles

def _scrape_cnn_investing() -> List[Dict]:
    cache_key = f"cnn_{date.today()}"
    print("Scraping fresh data from CNN...")
    scraper = CNNInvestingScraper()
    articles = scraper.run()
    save_to_cache(cache_key, articles)
    return articles

class CNNInvestingScraper:
    def __init__(self):
        self.url = "https://edition.cnn.com/business/investing"
        self.articles_data = []
        self.browserless_api_key = st.secrets["BROWSERLESS_API_KEY"]
        self.browserless_url = f"https://chrome.browserless.io/content?token={self.browserless_api_key}&stealth"

    def run(self) -> List[dict]:
        html = self._get_html(self.url)
        if not html:
            return []
        soup = BeautifulSoup(html, "html.parser")
        self._get_lead_plus_headlines(soup)
        self._get_vertical_strip_headlines(soup)
        self._get_text_news()
        return self.articles_data

    def _get_html(self, url: str) -> str:
        print(f"Fetching {url} via Browserless")
        payload = {
            "url": url,
            "gotoOptions": {"waitUntil": "domcontentloaded"},
            "elements": ["body"]
        }
        try:
            response = requests.post(self.browserless_url, json=payload, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"[ERROR] Could not fetch {url} via Browserless: {e}")
            return ""

    def _get_lead_plus_headlines(self, soup):
        print("Parsing lead-plus headlines...")
        try:
            main_container = soup.select_one("div.container.container_lead-plus-headlines-with-images")
            if not main_container:
                print("No main container found.")
                return
            article_cards = main_container.select("div.card.container__item")
            for card in article_cards:
                try:
                    headline = card.select_one("span.container__headline-text")
                    link = card.find("a")
                    if headline and link:
                        article_url = urljoin(self.url, link["href"])
                        self.articles_data.append({
                            "title": headline.text.strip(),
                            "url": article_url
                        })
                except Exception as e:
                    print(f"[WARN] Skipping a lead card: {e}")
        except Exception as e:
            print(f"[ERROR] in _get_lead_plus_headlines: {e}")

    def _get_vertical_strip_headlines(self, soup):
        print("Parsing vertical-strip headlines...")
        try:
            containers = soup.select("div.container.container_vertical-strip")
            for container in containers:
                try:
                    cards_wrapper = container.select_one("div.container_vertical-strip__cards-wrapper")
                    article_cards = cards_wrapper.select("div.card.container__item") if cards_wrapper else []
                    for card in article_cards:
                        headline = card.select_one("span.container__headline-text")
                        link = card.find("a")
                        if headline and link:
                            article_url = urljoin(self.url, link["href"])
                            self.articles_data.append({
                                "title": headline.text.strip(),
                                "url": article_url
                            })
                except Exception as e:
                    print(f"[WARN] Skipping vertical-strip container: {e}")
        except Exception as e:
            print(f"[ERROR] in _get_vertical_strip_headlines: {e}")

    def _get_text_news(self):
        print("Fetching full article content...")
        for news in self.articles_data:
            url = news["url"]
            html = self._get_html(url)
            if not html:
                news["content"] = ""
                continue
            try:
                soup = BeautifulSoup(html, "html.parser")
                content_div = soup.select_one("div.article__content")
                if not content_div:
                    paragraphs = soup.find_all("p")
                    text_parts = [p.get_text(strip=True) for p in paragraphs]
                else:
                    for tag in content_div(["script", "style", "img", "figure", "table", "ul", "ol"]):
                        tag.decompose()
                    text_parts = [line.strip() for line in content_div.get_text(separator="\n").splitlines()]
                news["content"] = "\n\n".join([line for line in text_parts if line])
            except Exception as e:
                print(f"[WARN] Failed to extract content from {url}: {e}")
                news["content"] = ""