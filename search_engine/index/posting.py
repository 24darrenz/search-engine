"""Posting and posting-list primitives.

Doc IDs within a posting list must stay sorted ascending -- this is what
makes merge-based AND/OR intersection O(n+m) instead of O(n*m), and is a
prerequisite for delta/gap encoding later.
"""
from dataclasses import dataclass, field


@dataclass
class Posting:
    doc_id: int
    term_freq: int = 0
    positions: list[int] = field(default_factory=list)


def sort_postings(postings: list[Posting]) -> list[Posting]:
    return sorted(postings, key=lambda p: p.doc_id)
