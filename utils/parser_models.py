from transformers import pipeline, AutoModelForSeq2SeqLM, AutoTokenizer
from keybert import KeyBERT
from sentence_transformers import SentenceTransformer
import torch
import logging

logging.basicConfig(level=logging.INFO)

def load_models():
    models = {}
    # Summarization - load via pipeline on CPU (avoid explicit device_map/device kwargs)
    try:
        models["summarizer"] = pipeline(
            "summarization",
            model="sshleifer/distilbart-cnn-12-6",
            device=-1  # use CPU
        )
        logging.info("Summarization model loaded on CPU.")
    except Exception as e:
        logging.error(f"Failed to load summarizer: {e}")
        models["summarizer"] = None

    # Sentiment analysis
    try:
        models["sentiment"] = pipeline(
            "sentiment-analysis",
            model="distilbert/distilbert-base-uncased-finetuned-sst-2-english",
            device=-1  # use CPU
        )
        logging.info("Sentiment model loaded on CPU.")
    except Exception as e:
        logging.error(f"Failed to load sentiment: {e}")
        models["sentiment"] = None

    # KeyBERT with SentenceTransformer
    try:
        # SentenceTransformer accepts `device` parameter; do not pass torch_dtype here
        sbert_model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
        models["keybert"] = KeyBERT(model=sbert_model)
        logging.info("KeyBERT loaded on CPU.")
    except Exception as e:
        logging.error(f"Failed to load KeyBERT: {e}")
        models["keybert"] = None

    return models
