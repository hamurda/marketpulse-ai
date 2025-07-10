# Financial News Summarizer & Sentiment Analyzer

A Python project that scrapes financial news from multiple sources, summarizes articles using open-source large language models (LLMs), classifies sentiment with FinBERT, caches results for efficient reuse, and serves them via a Streamlit UI.

## Features

- Scrapes news from CNN,  
- Summarizes long-form articles into structured markdown summaries using custom LLM pipelines  
- Performs sentiment classification on summaries with FinBERT  
- Caches summaries and sentiment results to speed up repeated access  
- Batch processing optimized for GPU-friendly tokenization and generation  
- Modular design with clear separation of scraping, summarization, sentiment analysis, and orchestration  
- Interactive Streamlit UI for browsing, filtering, and exploring summarized news  

## Next Steps
- Integrate API clients fully to fetch live news data from NewsAPI, Alpha Vantage
- Add keyword search functionality across cached summaries and articles for quick retrieval  
- Design and implement a database backend to store articles, summaries, and metadata to support efficient querying and search features  
- Implement ticker extraction and classification to identify and analyze financial symbols mentioned in articles  
- Improve caching strategy for incremental updates and cache invalidation


## Installation

Clone the repo and install dependencies:

```bash
git clone https://github.com/yourusername/financial-news-summarizer.git
cd marketpulse-ai

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

## Usage

Run the Streamlit UI

```bash
streamlit run app.py
```