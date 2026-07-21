"""İşe Uygun — ingestion servisi.

Dış dünyaya açılan tek kapı ``registry.assert_fetchable``'dır. Bu paket
içinde başka hiçbir yerde doğrudan ağ çağrısı yapılmaz (D-002).
"""

from .pipeline import (
    ADAPTER_VERSION,
    CONTENT_SIMILARITY_THRESHOLD,
    NormalizedPosting,
    RawPosting,
    cluster,
    content_similarity,
    normalize,
    normalize_employer,
    normalize_title,
    pick_canonical,
    run_fixture_ingest,
)
from .registry import PermissionError_, SourceRecord, assert_fetchable, audit, get

__all__ = [
    "ADAPTER_VERSION", "CONTENT_SIMILARITY_THRESHOLD", "NormalizedPosting",
    "RawPosting", "cluster", "content_similarity", "normalize",
    "normalize_employer", "normalize_title", "pick_canonical", "run_fixture_ingest",
    "PermissionError_", "SourceRecord", "assert_fetchable", "audit", "get",
]
