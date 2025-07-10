import streamlit as st
from datetime import date
from typing import List, Dict
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from src.utils.cache import load_from_cache, save_to_cache


TTL = 24 * 60 * 60  # 24 hours

@st.cache_data(ttl=TTL)
def get_cnn_articles() -> List[Dict]:
    """
    Load from cache if available, otherwise scrape and save.
    """
    cache_key = f"cnn_{date.today()}"
    cached = load_from_cache(cache_key)
    if cached:
        print("[CACHE] Using cached CNN news")
        return cached
    
    articles = _scrape_cnn_investing()

    return articles

def _scrape_cnn_investing() -> List[Dict]:
    """
    Scrape CNN investing articles and save them to a local JSON cache file.
    """
    cache_key = f"cnn_{date.today()}"
    print("Scraping fresh data from CNN...")
    scraper = CNNInvestingScraper()
    articles = scraper.run()

    save_to_cache(cache_key, articles)
    return articles


class CNNInvestingScraper:
    def __init__(self, driver=None):
        self.url = "https://edition.cnn.com/business/investing"
        self.articles_data = []

        self._driver = driver
        self._owns_driver = driver is None
        self._wait_time = 10
    
    def run(self) -> List[dict]:
        self._initialise_driver()
        self._scrape_content(self.url)
        self._get_lead_plus_headlines()
        self._get_vertical_strip_headlines()
        self._get_text_news()
        self._close_driver()

        return self.articles_data


    def _initialise_driver(self) -> None:
        if self._driver:
            return
        
        chrome_options=Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36")

        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            self._driver = driver
            self._owns_driver = True
        except Exception as e:
            print(f"An error occurred while initialising Chrome driver {self.url}: {e}")

    def _close_driver(self) -> None:
        if self._driver and self._owns_driver:
            self._driver.quit()
            print("Browser closed.")
            self._driver = None

    def _scrape_content(self, target_url) -> bool:
        """
        Scrapes the article.
        """
        if not self._driver:
            print("WebDriver is not initialized. Cannot scrape content.")
            return False
        try:
            print(f"Navigating to: {target_url}")
            self._driver.get(target_url)

            WebDriverWait(self._driver, self._wait_time).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            WebDriverWait(self._driver, self._wait_time).until(
                EC.presence_of_element_located((By.TAG_NAME, "section"))
            )       
            return True
        except Exception as e:
            print(f"An error occurred while scraping {target_url}: {e}")
            return False

    def _get_lead_plus_headlines(self)->None:
        """
        Extracts headlines and their links from the main article column.
        """
        articles_data = []
        if not self._driver:
            print("WebDriver is not initialized. Cannot extract articles.")
            return articles_data

        try:
            main_container = WebDriverWait(self._driver, self._wait_time).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.container.container_lead-plus-headlines-with-images'))
            )

            article_cards = main_container.find_elements(By.CSS_SELECTOR, 'div.card.container__item')

            print(f"Found {len(article_cards)} potential article cards.")

            for card in article_cards:
                try:
                    headline_element = card.find_element(By.CSS_SELECTOR, 'span.container__headline-text')
                    headline_text = headline_element.text.strip()

                    link_element = card.find_element(By.TAG_NAME, 'a')
                    article_link = link_element.get_attribute('href')

                    if article_link and not article_link.startswith(('http://', 'https://')):
                        from urllib.parse import urljoin
                        article_link = urljoin(self.url, article_link)

                    if headline_text and article_link:
                        articles_data.append({
                            'title': headline_text,
                            'url': article_link
                        })

                except Exception as e:
                    print(f"Could not extract data from one article card: {e}")
                    continue

            self.articles_data.extend(articles_data)

        except Exception as e:
            print(f"Error finding the main article container or cards: {e}")

    def _get_vertical_strip_headlines(self) -> None:
        """
        Accesses and extracts news headlines and links from the
        'container container_vertical-strip' element.
        """
        articles_data = []
        if not self._driver:
            print("WebDriver is not initialized. Cannot extract articles.")
            return articles_data
        try:
            # Find ALL instances of the main vertical strip containers
            all_vertical_strip_containers = WebDriverWait(self._driver, self._wait_time).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.container.container_vertical-strip'))
            )

            print(f"Found {len(all_vertical_strip_containers)} 'container_vertical-strip' sections.")

            for container in all_vertical_strip_containers:
                try:
                    cards_wrapper = container.find_element(By.CSS_SELECTOR, 'div.container_vertical-strip__cards-wrapper')
                    article_cards = cards_wrapper.find_elements(By.CSS_SELECTOR, 'div.card.container__item')

                    print(f"  Found {len(article_cards)} potential article cards in a 'vertical-strip' section.")

                    for card in article_cards:
                        try:
                            headline_element = card.find_element(By.CSS_SELECTOR, 'span.container__headline-text')
                            headline_text = headline_element.text.strip()

                            link_element = card.find_element(By.TAG_NAME, 'a')
                            article_link = link_element.get_attribute('href')

                            if article_link and not article_link.startswith(('http://', 'https://')):
                                article_link = urljoin(self.url, article_link)

                            if headline_text and article_link:
                                articles_data.append({
                                    'title': headline_text,
                                    'url': article_link
                                })

                        except Exception as e:
                            print(f"    Could not extract data from one article card in a 'vertical-strip' section: {e}")
                            continue
                    self.articles_data.extend(articles_data)
                except Exception as e:
                    print(f"  Could not find cards wrapper or articles in one of the 'vertical-strip' containers: {e}")
                    continue

        except Exception as e:
            print(f"Error finding any 'container_vertical-strip' elements: {e}")

    def _get_article_content(self, article_url:str)->str:
        """
        Cleans scraped article.
        """
        if not self._driver:
            print("WebDriver is not initialized. Cannot get article content.")
            return ""

        print(f"Attempting to get content from: {article_url}")
        if not self._scrape_content(article_url):
            return ""

        try:
            soup = BeautifulSoup(self._driver.page_source, 'html.parser')  
            article_body_element = soup.select_one('div.article__content')

            if not article_body_element:
                print("  Could not find a specific article body container. Attempting to get all paragraphs.")
                paragraphs = soup.find_all('p')
                article_text_parts = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
                return "\n\n".join(article_text_parts)


            for script_or_style in article_body_element(["script", "style", "img", "picture", "iframe", "figure", "table", "ul", "ol", "header", "footer", "aside", "nav", "svg"]):
                script_or_style.decompose()
            article_content_text = article_body_element.get_text(separator="\n", strip=True)
            clean_text = "\n".join([line.strip() for line in article_content_text.splitlines() if line.strip()])

            return clean_text

        except Exception as e:
            print(f"Error extracting article content from {article_url}: {e}")
            return ""

    def _get_text_news(self):
        for news in self.articles_data:
            link = news['url']
            content = self._get_article_content(link)
            news['content'] = content