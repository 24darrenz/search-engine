"""Boolean AND/OR query processing over sorted posting lists.

Sorted doc IDs let us do this as a linear merge-walk instead of a nested
loop. For multi-term AND queries, intersect shortest-list-first for a free
constant-factor speedup.
"""
from search_engine.index.posting import Posting


def intersect(list_a: list[Posting], list_b: list[Posting]) -> list[int]:
    """AND: doc IDs present in both posting lists."""
    i = j = 0
    result = []
    while i < len(list_a) and j < len(list_b):
        if list_a[i].doc_id == list_b[j].doc_id:
            result.append(list_a[i].doc_id)
            i += 1
            j += 1
        elif list_a[i].doc_id < list_b[j].doc_id:
            i += 1
        else:
            j += 1
    return result


def union(list_a: list[Posting], list_b: list[Posting]) -> list[int]:
    """OR: doc IDs present in either posting list, deduplicated."""
    i = j = 0
    result = []
    while i < len(list_a) and j < len(list_b):
        if list_a[i].doc_id == list_b[j].doc_id:
            result.append(list_a[i].doc_id)
            i += 1
            j += 1
        elif list_a[i].doc_id < list_b[j].doc_id:
            result.append(list_a[i].doc_id)
            i += 1
        else:
            result.append(list_b[j].doc_id)
            j += 1
    result.extend(p.doc_id for p in list_a[i:])
    result.extend(p.doc_id for p in list_b[j:])
    return result


def and_query(index: dict[str, list[Posting]], terms: list[str]) -> list[int]:
    """Multi-term AND: intersect shortest posting lists first."""
    lists = [index.get(t, []) for t in terms]
    if not lists or any(len(l) == 0 for l in lists):
        return []
    lists.sort(key=len)
    result = lists[0]
    result_ids = {p.doc_id for p in result}
    for lst in lists[1:]:
        # Re-wrap doc_id set as pseudo postings for intersect(); simplest
        # correct version first, optimize representation later if needed.
        result_ids &= {p.doc_id for p in lst}
    return sorted(result_ids)


def or_query(index: dict[str, list[Posting]], terms: list[str]) -> list[int]:
    """Multi-term OR: union of all posting lists."""
    doc_ids: set[int] = set()
    for t in terms:
        doc_ids.update(p.doc_id for p in index.get(t, []))
    return sorted(doc_ids)
