import torch
import numpy as np
import pandas as pd
from pathlib import Path

MODEL_NAME = "ProsusAI/finbert"
CACHE_DIR  = (Path(__file__).parent.parent.parent
              / "models" / "finbert_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)


class FinBERTScorer:
    """
    Financial sentiment scorer using FinBERT.

    Why a class and not a function?
    Loading FinBERT takes ~5 seconds and ~500MB RAM.
    We load once in __init__ and reuse across all calls.
    Calling a function would reload the model every time.

    Score range: -1.0 (maximally negative) to +1.0 (maximally positive)
    Computed as: P(positive) - P(negative)
    Neutral probability is ignored — it dilutes but doesn't flip sign.
    """

    def __init__(self):
        from transformers import (AutoTokenizer,
                                   AutoModelForSequenceClassification)
        print("Loading FinBERT model "
              "(downloads ~500MB on first run)...")

        self.tokenizer = AutoTokenizer.from_pretrained(
            MODEL_NAME, cache_dir=CACHE_DIR
        )
        self.model = AutoModelForSequenceClassification.from_pretrained(
            MODEL_NAME, cache_dir=CACHE_DIR
        )
        self.model.eval()

        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )
        self.model  = self.model.to(self.device)

        # FinBERT label order: positive=0, negative=1, neutral=2
        # Confirmed from the model card on HuggingFace
        print(f"  FinBERT loaded on {self.device}")

    def score_batch(
        self,
        texts     : list,
        batch_size: int = 16
    ) -> list:
        """
        Score a list of texts in batches.

        Batching is faster than one-by-one because the GPU
        (or CPU) processes multiple inputs simultaneously.
        batch_size=16 is safe for most CPU RAM sizes.
        Reduce to 8 if you get out-of-memory errors.
        """
        scores = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            inputs = self.tokenizer(
                batch,
                return_tensors = "pt",
                max_length     = 512,
                truncation     = True,
                padding        = True
            ).to(self.device)

            with torch.no_grad():
                outputs = self.model(**inputs)

            # Softmax converts raw logits to probabilities
            probs = torch.nn.functional.softmax(
                outputs.logits, dim=1
            ).cpu().numpy()

            # P(positive) - P(negative)
            batch_scores = [
                round(float(p[0]) - float(p[1]), 4)
                for p in probs
            ]
            scores.extend(batch_scores)

        return scores

    def score_dataframe(
        self,
        df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Score a news DataFrame from news_fetcher.py.
        Combines headline + description for richer context.
        Returns same DataFrame with 'sentiment_score' added.
        """
        df    = df.copy()
        texts = []

        for _, row in df.iterrows():
            headline    = str(row.get("headline",    "")).strip()
            description = str(row.get("description", "")).strip()

            if description and description != "nan":
                combined = f"{headline}. {description}"
            else:
                combined = headline

            texts.append(combined[:1000])

        print(f"  Scoring {len(texts)} articles with FinBERT...")
        df["sentiment_score"] = self.score_batch(texts)
        return df