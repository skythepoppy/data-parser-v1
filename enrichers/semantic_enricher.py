from typing import Dict, Any
from utils.logger import logger

# nlp libraries
import spacy
from keybert import KeyBERT
from transformers import pipeline, Pipeline

# loaded models
nlp_model = None
kw_model = None
summarizer_pipeline: Pipeline | None = None
sentiment_pipeline: Pipeline | None = None

# safe-length constants
MAX_SUMMARIZER_LENGTH = 1024  
MAX_SENTIMENT_LENGTH = 512    

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

def chunk_text(text: str, chunk_size: int = MAX_SUMMARIZER_LENGTH) -> list[str]:
    
    if len(text) <= chunk_size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        if end < len(text):
            # try not to cut mid-sentence
            period_pos = text.rfind('.', start, end)
            if period_pos != -1:
                end = period_pos + 1
        chunks.append(text[start:end].strip())
        start = end
    return chunks

def summarize_text(text: str, max_length=150, min_length=40):
    if not text.strip() or not summarizer_pipeline:
        return ""
    try:
        chunks = chunk_text(text)
        chunk_summaries = []
        for chunk in chunks:
            res = summarizer_pipeline(chunk, max_length=max_length, min_length=min_length, do_sample=False)
            if res and isinstance(res, list) and "summary_text" in res[0]:
                chunk_summaries.append(res[0]["summary_text"])
        combined_summary = " ".join(chunk_summaries)
        # if multiple chunks, optionally summarize combined summary
        if len(chunk_summaries) > 1:
            res = summarizer_pipeline(combined_summary, max_length=max_length, min_length=min_length, do_sample=False)
            if res and isinstance(res, list) and "summary_text" in res[0]:
                return res[0]["summary_text"]
        return combined_summary
    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        return ""

def analyze_sentiment(text: str):
    if not text.strip() or not sentiment_pipeline:
        return "neutral"

    try:
        # split text into  chunks
        chunks = [text[i:i+MAX_SENTIMENT_LENGTH] for i in range(0, len(text), MAX_SENTIMENT_LENGTH)]
        results = []
        for chunk in chunks:
            res = sentiment_pipeline(chunk)
            if res and isinstance(res, list) and "label" in res[0]:
                results.append(res[0]["label"].lower())

        # aggregate results--> simple majority vote
        if not results:
            return "neutral"
        pos_count = results.count("positive")
        neg_count = results.count("negative")
        neu_count = results.count("neutral")

        if pos_count >= neg_count and pos_count >= neu_count:
            return "positive"
        elif neg_count >= pos_count and neg_count >= neu_count:
            return "negative"
        else:
            return "neutral"
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

    # entities/keywords
    entities = extract_entities(content)
    keywords = extract_keywords(content, top_n_keywords)

    # chunk summarization
    if summarizer_pipeline:
        summary_chunks = []
        for i in range(0, len(content), MAX_SUMMARIZER_LENGTH):
            chunk = content[i:i + MAX_SUMMARIZER_LENGTH]
            try:
                res = summarizer_pipeline(chunk, max_length=150, min_length=40, do_sample=False)
                if res and isinstance(res, list) and "summary_text" in res[0]:
                    summary_chunks.append(res[0]["summary_text"])
            except Exception as e:
                logger.error(f"Summarization chunk failed: {e}")
        summary_text = " ".join(summary_chunks) if summary_chunks else ""
    else:
        summary_text = ""

    # chunk sentiment
    sentiment_text = analyze_sentiment(content)

    article.update({
        "entities": entities,
        "keywords": keywords,
        "summary": summary_text,
        "sentiment": sentiment_text
    })

    return article

