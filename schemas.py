from typing import TypedDict


class ArticleDict(TypedDict):
    title: str
    description: str
    content: str
    published_at: str
    url: str
    source: str


class SummaryDict(TypedDict):
    title: str
    summary: str
    source: str
    published_at: str
    url: str
