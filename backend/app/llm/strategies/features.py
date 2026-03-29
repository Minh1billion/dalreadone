import re
import math
import collections
import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

TOP_KEYWORDS    = 15
TOP_BIGRAMS     = 10
MIN_DOC_FREQ    = 2
MIN_WORD_LEN    = 3
N_CLUSTERS      = 4
MIN_COOCCURRENCE = 2

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

_NEGATORS = {"not", "never", "no", "neither", "nor", "without"}


def _empty_features(n_rows: int) -> dict:
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


def _tokenize(text: str, stopwords: frozenset[str] = frozenset()) -> list[str]:
    return [
        t for t in re.findall(r"[a-zA-Z]+", text.lower())
        if len(t) >= MIN_WORD_LEN and t not in stopwords
    ]


def _score_row(text: str) -> float:
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


def compute_keywords(
    series: pd.Series,
    stopwords: frozenset[str] = frozenset(),
    top_n: int = TOP_KEYWORDS,
) -> list[tuple[str, float]]:
    docs   = series.fillna("").astype(str).tolist()
    n_docs = len(docs)

    tf_per_doc: list[collections.Counter] = [
        collections.Counter(_tokenize(doc, stopwords)) for doc in docs
    ]

    df_counter: collections.Counter = collections.Counter()
    for tf in tf_per_doc:
        df_counter.update(tf.keys())

    vocab = {w for w, cnt in df_counter.items() if cnt >= MIN_DOC_FREQ}

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


def compute_topic_clusters(
    series: pd.Series,
    keywords: list[str],
    stopwords: frozenset[str] = frozenset(),
) -> list[dict]:
    if not keywords:
        return []

    keyword_set = set(keywords)
    docs        = series.fillna("").astype(str).tolist()

    cooc: dict[str, collections.Counter] = {k: collections.Counter() for k in keyword_set}
    doc_counts: collections.Counter      = collections.Counter()

    for doc in docs:
        tokens = set(_tokenize(doc, stopwords)) & keyword_set
        for kw in tokens:
            doc_counts[kw] += 1
        for kw_a in tokens:
            for kw_b in tokens:
                if kw_a != kw_b:
                    cooc[kw_a][kw_b] += 1

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


def compute_length_distribution(series: pd.Series) -> dict:
    word_counts = series.fillna("").astype(str).apply(lambda x: len(x.split()))
    n = max(len(word_counts), 1)
    return {
        "short":     float((word_counts <= 10).sum()                          / n * 100),
        "medium":    float(((word_counts > 10)  & (word_counts <= 50)).sum()  / n * 100),
        "long":      float(((word_counts > 50)  & (word_counts <= 200)).sum() / n * 100),
        "very_long": float((word_counts > 200).sum()                          / n * 100),
    }


def compute_nlp_features(
    df: pd.DataFrame,
    text_cols: list[str],
    stopwords: frozenset[str] = frozenset(),
) -> dict[str, dict]:
    features: dict[str, dict] = {}

    for col in text_cols:
        n_rows = len(df)
        try:
            series               = df[col]
            keywords_with_scores = compute_keywords(series, stopwords)
            keywords             = [w for w, _ in keywords_with_scores]

            features[col] = {
                "sentiment":           compute_sentiment(series),
                "keywords":            keywords_with_scores,
                "topic_clusters":      compute_topic_clusters(series, keywords, stopwords),
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
            logger.exception("compute_nlp_features failed for col=%r — using zero-value sentinel", col)
            features[col] = _empty_features(n_rows)

    return features