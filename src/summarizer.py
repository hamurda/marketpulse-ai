import os
import hashlib
from typing import List
from src.schemas import ArticleDict, SummaryDict

import torch
import ollama
from tqdm import tqdm
from datasets import Dataset
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

    def __init__(self, model=_model, tokenizer=_tokenizer):
        self.model = model
        self.tokenizer = tokenizer

    def batch_summarize(self, articles: Dataset, batch_size: int = 8) -> list[str]:
        prompts = [self._build_prompt(article) for article in articles]
        summaries = []

        for i in tqdm(range(0, len(prompts), batch_size), desc="Summarizing"):
            batch_prompts = prompts[i:i+batch_size]
            tokenized = self.tokenizer(batch_prompts, return_tensors="pt", padding=True, truncation=True).to("cuda")

            outputs = self.model.generate(
                **tokenized,
                max_new_tokens=1000,
                do_sample=False,
            )

            decoded = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)
            batch_summaries = [res[len(prompt):].strip() for res, prompt in zip(decoded, batch_prompts)]
            summaries.extend(batch_summaries)

        return summaries
    
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