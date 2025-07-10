from typing import TypedDict, List


class TopicDict(TypedDict):
    label: str
    score: float

class TickerSentimentDict(TypedDict):
    ticker: str
    label: str
    confidence: float
    sentence: str

class ArticleDict(TypedDict):
    title: str
    description: str
    content: str
    published_at: str
    url: str
    source: str
    overall_sentiment_label: str
    overall_sentiment_score: float
    topics: List[TopicDict]
    ticker_sentiment: List[TickerSentimentDict]


class SummaryDict(TypedDict):
    title: str
    summary: str
    source: str
    published_at: str
    url: str
    sentiment: str
    sentiment_score: float
    topics: List[TopicDict]
    ticker_sentiment: List[TickerSentimentDict]
