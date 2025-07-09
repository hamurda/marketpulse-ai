import os
import hashlib
from typing import List
from src.schemas import ArticleDict, SummaryDict

import torch
import ollama
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

_model_id = "us4/fin-llama3.1-8b"
_tokenizer = AutoTokenizer.from_pretrained(_model_id)

_bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16
)

_model = AutoModelForCausalLM.from_pretrained(
    _model_id,
    quantization_config=_bnb_config,
    device_map="auto"
)

class FinNewsSummarizer:
    DEFAULT_OLLAMA_MODEL = "llama3.2"
    SYSTEM_PROMPT = """You are a financial news analyst assistant.
    Given a financial news article, your task is to extract a structured summary with the following sections:
    -Market Summary  
    -Valuation Metrics  
    -Macro & FX  
    -Key Drivers  
    -Tickers  
    -Sentiment
    Be concise, accurate, and avoid repeating the entire article. Reply in markdown format.
    Do not add information. Summarise only the written information in the given article.
    """

    def __init__(self, model=_model, tokenizer=_tokenizer, cache_dir="data/summaries", use_local_model=True):
        self.model = model
        self.tokenizer = tokenizer
        self.cache_dir = cache_dir
        self.use_local_model = use_local_model

    def summarize(self, article: ArticleDict) -> str:        
        if self.use_local_model:
            summary = self._summarize_llama32(article)
        else:
            summary = self._summarize_fin_llama31(article)

        summarised: SummaryDict = {
                "title": article.get("title", ""),
                "summary": summary,
                "description": article.get("description", ""),
                "published_at": article.get("publishedAt", ""),
                "url": article.get("url", ""),
                "source": article.get("source", {}).get("name", ""),
                "sentiment": article.get("overall_sentiment_label", ""),
                "sentiment_score": article.get("overall_sentiment_score", 0),
                "topics": article.get("topics", []),
                "ticker_sentiment": article.get("ticker_sentiment", []),
            }

        return summarised

    def _summarize_llama32(self, article):
        """
        Placeholder summarizing method to use llama3.2 locally. Otherwise GPU needed.
        """
        messages = [
            {"role": "system", "content":self.SYSTEM_PROMPT},
            {"role": "user", "content": self._build_prompt(article)}
        ]

        response = ollama.chat(model=self.DEFAULT_OLLAMA_MODEL, messages=messages, 
                               stream=False,
                               options= {
                                    "temperature": 0.7
                                })
    
        return response['message']['content']
    
    def _summarize_fin_llama31(self, article):
        """
        Using "us4/fin-llama3.1-8b" to summarize finance news.
        """
        prompt = self._build_prompt(article)
        inputs = self.tokenizer(prompt, return_tensors="pt").to("cuda")

        outputs = self.model.generate(
            **inputs,
            max_new_tokens=1000,
            temperature=0.7,
        )

        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response[len(prompt):].strip()
    
    def _build_prompt(self, article: ArticleDict) -> str:
        return (
            f"<|system|>\n{self.SYSTEM_PROMPT}\n"
            f"<|user|>\n"
            f"### News Title:\n{article['title']}\n\n"
            f"### Article:\n{article['content']}\n\n"
            f"### The summary:\n"
            f"<|assistant|>\n"
        )

    def _hash(self, text: str) -> str:
        return hashlib.sha1(text.encode()).hexdigest()