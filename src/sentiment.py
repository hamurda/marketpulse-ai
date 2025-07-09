from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification

_model_name = "ProsusAI/finbert"
_tokenizer = AutoTokenizer.from_pretrained(_model_name)
_model = AutoModelForSequenceClassification.from_pretrained(_model_name)

_sentiment_pipeline = pipeline("sentiment-analysis", model=_model, tokenizer=_tokenizer)


def classify_sentiment(text: str) -> tuple[str, float]:
    result = _sentiment_pipeline(text[:512])[0]  # truncate to avoid max token errors
    return result["label"], float(result["score"])
