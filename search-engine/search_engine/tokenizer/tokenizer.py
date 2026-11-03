"""Tokenization: text -> normalized list of terms.

Kept deterministic and dependency-light on purpose so vocabulary size and
tokenization behavior are easy to reason about and benchmark.
"""
import re

# Start small; grow this list as you inspect real vocabulary output.
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "has", "he", "in", "is", "it", "its", "of", "on", "that", "the",
    "to", "was", "were", "will", "with",
}

_TOKEN_RE = re.compile(r"[^a-z0-9\s]")


def tokenize(text: str, remove_stopwords: bool = True) -> list[str]:
    """Lowercase, strip punctuation, split on whitespace, drop stopwords.

    Stemming is intentionally left out of v1 -- add it later and re-measure
    vocabulary size before/after as a benchmark data point.
    """
    text = text.lower()
    text = _TOKEN_RE.sub(" ", text)
    tokens = text.split()
    if remove_stopwords:
        tokens = [t for t in tokens if t not in STOPWORDS]
    return tokens
