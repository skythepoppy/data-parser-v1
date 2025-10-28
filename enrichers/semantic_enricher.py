
from typing import Dict, Any
from utils.logger import logger

# nlp libraries
import spacy
from keybert import KeyBERT
from transformers import pipeline

# loaded models
nlp_model = None
kw_model = None
summarizer_pipeline = None
sentiment_pipeline = None

def init_models():
    global nlp_model, kw_model, summarizer_pipeline, sentiment_pipeline

    if not nlp_model:
        try:
            nlp_model = spacy.load("en_core_web_sm")
        except Exception as e:
            logger.error(f"Failed to load spaCy model: {e}")
            nlp_model = None

    if not kw_model:
        try:
            kw_model = KeyBERT()
        except Exception as e:
            logger.error(f"Failed to load KeyBERT model: {e}")
            kw_model = None

    if not summarizer_pipeline:
        try:
            summarizer_pipeline = pipeline("summarization")
        except Exception as e:
            logger.error(f"Failed to load summarization pipeline: {e}")
            summarizer_pipeline = None

    if not sentiment_pipeline:
        try:
            sentiment_pipeline = pipeline("sentiment-analysis")
        except Exception as e:
            logger.error(f"Failed to load sentiment-analysis pipeline: {e}")
            sentiment_pipeline = None


# enrichment helper functions

def extract_entities(text: str):
    if not text.strip() or not nlp_model:
        return []
    try:
        doc = nlp_model(text)
        return [{"text": ent.text, "label": ent.label_} for ent in doc.ents]
    except Exception as e:
        logger.error(f"NER failed: {e}")
        return []

def extract_keywords(text: str, top_n: int = 10):
    if not text.strip() or not kw_model:
        return []
    try:
        return [kw for kw, _ in kw_model.extract_keywords(text, top_n=top_n)]
    except Exception as e:
        logger.error(f"Keyword extraction failed: {e}")
        return []

def summarize_text(text: str, max_length=150, min_length=40):
    if not text.strip() or not summarizer_pipeline:
        return ""
    try:
        res = summarizer_pipeline(text, max_length=max_length, min_length=min_length, do_sample=False)
        return res[0]["summary_text"] if res else ""
    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        return ""

def analyze_sentiment(text: str):
    if not text.strip() or not sentiment_pipeline:
        return "neutral"
    try:
        res = sentiment_pipeline(text[:512])  # limit --> 512 chars
        return res[0]["label"].lower() if res else "neutral"
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        return "neutral"


# main func

def enrich_text(article: Dict[str, Any], top_n_keywords: int = 10) -> Dict[str, Any]:
    init_models()  

    content = article.get("content", "")
    if not content.strip():
        logger.warning("Semantic enrichment: empty content")
        article.update({
            "entities": [],
            "keywords": [],
            "summary": "",
            "sentiment": "neutral"
        })
        return article

    article.update({
        "entities": extract_entities(content),
        "keywords": extract_keywords(content, top_n_keywords),
        "summary": summarize_text(content),
        "sentiment": analyze_sentiment(content)
    })

    return article
