"""Feature pipeline + canonicalizer for the guardrail project."""
from __future__ import annotations

import re
import unicodedata

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion, Pipeline


# Order-sensitive list of (pattern, replacement) canonicalization rules.
_ROLE_MARKER_RE = re.compile(r"^\s*(system|assistant|user)\s*[:>]\s*", re.IGNORECASE | re.MULTILINE)
_TAG_ROLE_RE = re.compile(r"\[?<?\s*(system|assistant|user)\s*>?\]?", re.IGNORECASE)
_NORMALIZE_PATTERNS = [
    (re.compile(r"ignore\s+(all\s+)?(the\s+)?previous\s+instructions?", re.IGNORECASE),
     " injection_pattern_ignore_previous "),
    (re.compile(r"disregard\s+(the\s+)?(above|previous|prior)", re.IGNORECASE),
     " injection_pattern_disregard "),
    (re.compile(r"forget\s+(what\s+you|the\s+previous|all)", re.IGNORECASE),
     " injection_pattern_forget "),
    (re.compile(r"override\s+your\s+instructions?", re.IGNORECASE),
     " injection_pattern_override "),
    (re.compile(r"reveal\s+(the\s+)?system\s+prompt", re.IGNORECASE),
     " injection_pattern_reveal_system "),
    (re.compile(r"<\s*tool_output\s*>", re.IGNORECASE),
     " injection_pattern_tool_output_open "),
]


def canonicalize(text: str) -> str:
    """Reversible-ish canonicalizer: lowercase, normalize whitespace + role markers + known tricks."""
    if not isinstance(text, str):
        return ""
    # Unicode normalize (NBSP and friends -> space)
    t = unicodedata.normalize("NFKC", text)
    t = t.replace("\xa0", " ")
    # Strip leading/trailing whitespace per line, collapse multiline
    t = "\n".join(line.strip() for line in t.splitlines())
    # Lowercase
    t = t.lower()
    # Strip role markers at line start
    t = _ROLE_MARKER_RE.sub(" canon_role_marker ", t)
    # Replace inline role tags
    t = _TAG_ROLE_RE.sub(" canon_role_tag ", t)
    # Tag known injection idioms
    for pat, repl in _NORMALIZE_PATTERNS:
        t = pat.sub(repl, t)
    # Collapse whitespace
    t = re.sub(r"\s+", " ", t).strip()
    return t


def build_input_pipeline() -> FeatureUnion:
    """Char + word TF-IDF feature union, used as the feature step in the input classifier."""
    return FeatureUnion(transformer_list=[
        ("char", TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(3, 5),
            max_features=30000,
            min_df=2,
            sublinear_tf=True,
        )),
        ("word", TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 2),
            max_features=30000,
            min_df=2,
            sublinear_tf=True,
        )),
    ])


def build_output_pipeline() -> TfidfVectorizer:
    """Simpler word-level TF-IDF for output classifier."""
    return TfidfVectorizer(
        analyzer="word",
        ngram_range=(1, 2),
        max_features=20000,
        min_df=2,
        sublinear_tf=True,
    )
