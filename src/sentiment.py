import streamlit as st
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification


@st.cache_resource
def load_sentiment_pipeline():
    model_name = "ProsusAI/finbert"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)

    return pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)

_sentiment_pipeline = load_sentiment_pipeline()

def classify_sentiment(text: str) -> tuple[str, float]:
    result = _sentiment_pipeline(text[:512])[0]  # truncate to avoid max token errors
    return result["label"], float(result["score"])
