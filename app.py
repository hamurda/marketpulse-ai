import streamlit as st
from src.pipeline import ArticleProcessor
from src.schemas import SummaryDict


SUMMARY_DIR = "data/summaries"

@st.cache_data(show_spinner=False)
def load_all_summaries() -> list[SummaryDict]:
    news = ArticleProcessor()
    summaries = news.get_processed_articles()
    return sorted(summaries, key=lambda x: x.get("published_at", ""), reverse=True)


def format_sentiment(label: str) -> str:
    emoji = {"POSITIVE": "📈", "NEGATIVE": "📉", "NEUTRAL": "📊"}.get(label.upper(), "")
    return f"{emoji} {label.title()}"


def render_article(summary: SummaryDict):
    with st.expander(f"📰 {summary['title']}"):
        st.markdown(f"**Published:** {summary['published_at']}  |  **Source:** {summary['source']}")
        st.markdown(f"**Sentiment:** {format_sentiment(summary['sentiment'])} ({summary['sentiment_score']:.2f})")
        st.markdown("---")
        st.markdown(summary["summary"], unsafe_allow_html=True)
        st.markdown(f"[🔗 Read more]({summary['url']})")


def main():
    st.set_page_config(page_title="FinNews Summary App", layout="wide")
    st.title("🧠 Financial News Summarizer")
    st.markdown("Summarized and analyzed financial news powered by LLMs.")

    # Sidebar filters
    st.sidebar.header("🔍 Filters")
    sentiment_filter = st.sidebar.multiselect(
        "Filter by sentiment",
        options=["POSITIVE", "NEUTRAL", "NEGATIVE"],
        default=["POSITIVE", "NEUTRAL", "NEGATIVE"]
    )

    # Load summaries
    summaries = load_all_summaries()

    filtered = [s for s in summaries if s["sentiment"].upper() in sentiment_filter]

    st.success(f"Loaded {len(filtered)} article summaries.")
    for summary in filtered:
        render_article(summary)


if __name__ == "__main__":
    main()
