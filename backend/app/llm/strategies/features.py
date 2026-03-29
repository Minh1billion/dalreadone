"""
strategies/features.py

Pre-computed NLP feature extractors that run server-side before any LLM call.

Intentionally uses only stdlib + pandas + numpy — no spacy, transformers,
or nltk — so there are no extra dependencies and results stay fast and
deterministic.

Features computed per text column:
    sentiment           : lexicon-based scores with simple negation handling
    keywords            : TF-IDF approximation (no sklearn)
    topic_clusters      : keyword co-occurrence grouping
    length_distribution : word-count buckets (short / medium / long / very_long)

Entry point:
    compute_nlp_features(df, text_cols) -> dict[col_name, feature_dict]
"""
import re
import math
import collections
import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Sentinel — returned when a column fails so the rest of the pipeline
# always sees a fully-formed dict with every expected key.
# ---------------------------------------------------------------------------
def _empty_features(n_rows: int) -> dict:
    """Return a fully-formed feature dict with safe zero values."""
    return {
        "sentiment": {
            "scores":       [0.0] * n_rows,
            "mean":         0.0,
            "positive_pct": 0.0,
            "negative_pct": 0.0,
            "neutral_pct":  100.0,
        },
        "keywords":            [],
        "topic_clusters":      [],
        "length_distribution": {
            "short":     100.0,
            "medium":    0.0,
            "long":      0.0,
            "very_long": 0.0,
        },
    }


# ---------------------------------------------------------------------------
# Sentiment lexicon
# Covers common review / feedback / support language.
# Extend these sets to improve accuracy for your domain.
# ---------------------------------------------------------------------------
_POSITIVE_WORDS = {
    "good", "great", "excellent", "amazing", "wonderful", "fantastic",
    "love", "loved", "best", "perfect", "awesome", "outstanding",
    "happy", "pleased", "satisfied", "recommend", "helpful", "easy",
    "fast", "clean", "friendly", "beautiful", "enjoy", "enjoyed",
    "impressive", "reliable", "delicious", "fresh", "comfortable",
}

_NEGATIVE_WORDS = {
    "bad", "worst", "terrible", "awful", "horrible", "poor", "hate",
    "hated", "disappointed", "disappointing", "slow", "dirty", "rude",
    "broken", "useless", "waste", "boring", "cheap", "wrong", "never",
    "problem", "issue", "error", "fail", "failed", "avoid", "refund",
    "unfortunately", "annoying", "difficult", "expensive", "missing",
}

# Words that flip the polarity of the next sentiment word
_NEGATORS = {"not", "never", "no", "neither", "nor", "without"}


# ---------------------------------------------------------------------------
# TF-IDF / tokenizer config
# ---------------------------------------------------------------------------
TOP_KEYWORDS    = 15    # number of keywords to extract per column
TOP_BIGRAMS     = 10    # number of bigrams to include in stats
MIN_DOC_FREQ    = 2     # minimum document frequency for a word to qualify
MIN_WORD_LEN    = 3     # minimum token length (filters noise)


# ---------------------------------------------------------------------------
# Topic clustering config
# ---------------------------------------------------------------------------
N_CLUSTERS       = 4   # maximum number of topic clusters to return
MIN_COOCCURRENCE = 2   # minimum co-occurrence count to link two keywords


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------
def _tokenize(text: str) -> list[str]:
    """Lowercase, split on non-alpha, filter short tokens."""
    return [
        t for t in re.findall(r"[a-zA-Z]+", text.lower())
        if len(t) >= MIN_WORD_LEN
    ]


# ---------------------------------------------------------------------------
# Sentiment
# ---------------------------------------------------------------------------
def _score_row(text: str) -> float:
    """
    Score a single text string in [-1, 1].

    Iterates tokens left-to-right; a negator word flips the polarity
    of the immediately following sentiment word.
    Score is normalised by token count so longer texts don't dominate.
    """
    tokens = _tokenize(text)
    score  = 0
    negate = False

    for token in tokens:
        if token in _NEGATORS:
            negate = True
            continue
        if token in _POSITIVE_WORDS:
            score += -1 if negate else 1
        elif token in _NEGATIVE_WORDS:
            score += 1 if negate else -1
        negate = False

    return score / max(len(tokens), 1)


def compute_sentiment(series: pd.Series) -> dict:
    """
    Compute sentiment statistics for a text column.

    Returns:
        scores       : list[float]  — one score per row, range [-1, 1]
        mean         : float
        positive_pct : float        — % of rows with score > 0
        negative_pct : float        — % of rows with score < 0
        neutral_pct  : float        — % of rows with score == 0
    """
    scores = series.fillna("").astype(str).apply(_score_row).tolist()
    arr    = np.array(scores)
    n      = max(len(arr), 1)
    return {
        "scores":       scores,
        "mean":         float(arr.mean()),
        "positive_pct": float((arr > 0).sum() / n * 100),
        "negative_pct": float((arr < 0).sum() / n * 100),
        "neutral_pct":  float((arr == 0).sum() / n * 100),
    }


# ---------------------------------------------------------------------------
# TF-IDF keyword extraction
# ---------------------------------------------------------------------------
def compute_keywords(series: pd.Series, top_n: int = TOP_KEYWORDS) -> list[tuple[str, float]]:
    """
    Approximate TF-IDF keyword extraction without sklearn.

    Aggregates TF-IDF scores across all documents and returns
    the top_n words sorted by total score descending.

    Returns:
        list of (word, score) tuples
    """
    docs   = series.fillna("").astype(str).tolist()
    n_docs = len(docs)

    tf_per_doc: list[collections.Counter] = [
        collections.Counter(_tokenize(doc)) for doc in docs
    ]

    # Document frequency — how many docs contain each word
    df_counter: collections.Counter = collections.Counter()
    for tf in tf_per_doc:
        df_counter.update(tf.keys())

    # Discard words that appear in too few documents
    vocab = {w for w, cnt in df_counter.items() if cnt >= MIN_DOC_FREQ}

    # Sum TF-IDF scores across all documents
    tfidf_totals: dict[str, float] = collections.defaultdict(float)
    for tf in tf_per_doc:
        total_terms = max(sum(tf.values()), 1)
        for word, count in tf.items():
            if word not in vocab:
                continue
            tf_score  = count / total_terms
            idf_score = math.log(n_docs / (df_counter[word] + 1)) + 1
            tfidf_totals[word] += tf_score * idf_score

    return sorted(tfidf_totals.items(), key=lambda x: x[1], reverse=True)[:top_n]


# ---------------------------------------------------------------------------
# Topic clustering (keyword co-occurrence)
# ---------------------------------------------------------------------------
def compute_topic_clusters(
    series: pd.Series,
    keywords: list[str],
) -> list[dict]:
    """
    Group keywords into topic clusters using co-occurrence counts.

    Two keywords are linked if they appear together in at least
    MIN_COOCCURRENCE documents. Clustering is greedy: each keyword
    joins the cluster of its most co-occurring already-assigned neighbour.

    Returns:
        list of dicts, each:
            topic     : str           — label (top keyword in cluster)
            keywords  : list[str]
            doc_count : int           — total document coverage
    """
    if not keywords:
        return []

    keyword_set = set(keywords)
    docs        = series.fillna("").astype(str).tolist()

    # Build co-occurrence and per-keyword document counts
    cooc: dict[str, collections.Counter] = {k: collections.Counter() for k in keyword_set}
    doc_counts: collections.Counter      = collections.Counter()

    for doc in docs:
        tokens = set(_tokenize(doc)) & keyword_set
        for kw in tokens:
            doc_counts[kw] += 1
        for kw_a in tokens:
            for kw_b in tokens:
                if kw_a != kw_b:
                    cooc[kw_a][kw_b] += 1

    # Greedy assignment
    assigned: dict[str, int] = {}
    clusters: list[list[str]] = []

    for kw in keywords:
        neighbours = [
            n for n, cnt in cooc[kw].items()
            if cnt >= MIN_COOCCURRENCE and n in assigned
        ]
        if neighbours:
            best       = max(neighbours, key=lambda n: cooc[kw][n])
            cluster_id = assigned[best]
            clusters[cluster_id].append(kw)
            assigned[kw] = cluster_id
        else:
            assigned[kw] = len(clusters)
            clusters.append([kw])

    # Rank clusters by total document coverage and return top N
    cluster_objs = [
        {
            "topic":     members[0],
            "keywords":  members,
            "doc_count": sum(doc_counts[k] for k in members),
        }
        for members in clusters
    ]
    cluster_objs.sort(key=lambda c: c["doc_count"], reverse=True)
    return cluster_objs[:N_CLUSTERS]


# ---------------------------------------------------------------------------
# Length distribution
# ---------------------------------------------------------------------------
def compute_length_distribution(series: pd.Series) -> dict:
    """
    Bucket rows by word count into four size categories.

    Thresholds:
        short     : <= 10 words
        medium    : 11 – 50 words
        long      : 51 – 200 words
        very_long : > 200 words

    Returns:
        dict with keys short, medium, long, very_long — each a % float.
    """
    word_counts = series.fillna("").astype(str).apply(lambda x: len(x.split()))
    n = max(len(word_counts), 1)
    return {
        "short":     float((word_counts <= 10).sum()                          / n * 100),
        "medium":    float(((word_counts > 10)  & (word_counts <= 50)).sum()  / n * 100),
        "long":      float(((word_counts > 50)  & (word_counts <= 200)).sum() / n * 100),
        "very_long": float((word_counts > 200).sum()                          / n * 100),
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def compute_nlp_features(df: pd.DataFrame, text_cols: list[str]) -> dict[str, dict]:
    """
    Run all feature extractors for each text column.

    Each column is processed independently inside a try/except so that a
    failure in one column (e.g. all-null data, unexpected dtypes) never
    prevents the others from being computed and never propagates a partial
    dict upward.  A column that fails gets a fully-formed zero-value sentinel
    so downstream code (engine/nlp.py, the sandbox) can always safely access
    every expected key without defensive checks.

    Args:
        df        : Full DataFrame.
        text_cols : Column names identified as text-heavy.

    Returns:
        {
            col_name: {
                "sentiment"           : { mean, positive_pct, negative_pct, neutral_pct, scores },
                "keywords"            : [ (word, tfidf_score), ... ],
                "topic_clusters"      : [ { topic, keywords, doc_count }, ... ],
                "length_distribution" : { short, medium, long, very_long },
            }
        }
    """
    features: dict[str, dict] = {}

    for col in text_cols:
        n_rows = len(df)
        try:
            series               = df[col]
            keywords_with_scores = compute_keywords(series)
            keywords             = [w for w, _ in keywords_with_scores]

            features[col] = {
                "sentiment":           compute_sentiment(series),
                "keywords":            keywords_with_scores,
                "topic_clusters":      compute_topic_clusters(series, keywords),
                "length_distribution": compute_length_distribution(series),
            }

            logger.debug(
                "nlp_features OK  col=%r  sentiment_mean=%.3f  keywords=%d  clusters=%d",
                col,
                features[col]["sentiment"]["mean"],
                len(features[col]["keywords"]),
                len(features[col]["topic_clusters"]),
            )

        except Exception:
            logger.exception(
                "compute_nlp_features failed for col=%r — using zero-value sentinel",
                col,
            )
            features[col] = _empty_features(n_rows)

    return features