"""Serialize the in-memory index to disk as three files:

  index.dict      -- term -> (offset, length) into index.postings
  index.postings  -- contiguous binary blob of fixed-width Posting records
  index.meta      -- doc_lengths, doc_metadata, num_docs, avg_doc_len
                     (needed for BM25 -- without this, a freshly loaded
                     index has no way to know document lengths)

v1 record format (no compression yet):
  struct Posting { uint32 doc_id; uint32 term_freq; }

Positions (for phrase search) are left out of v1 on-disk format to keep it
simple -- add them as a variable-length section later if you want phrase
queries to survive a reload.
"""
import json
import struct

from search_engine.index.posting import Posting

RECORD_FORMAT = "<II"  # doc_id, term_freq (little-endian, 2x uint32)
RECORD_SIZE = struct.calcsize(RECORD_FORMAT)


def write_index(
    index: dict[str, list[Posting]],
    postings_path: str,
    dict_path: str,
    doc_lengths: dict[int, int] | None = None,
    doc_metadata: dict[int, dict] | None = None,
    meta_path: str | None = None,
) -> None:
    dictionary: dict[str, tuple[int, int]] = {}
    with open(postings_path, "wb") as postings_file:
        offset = 0
        for term, postings in index.items():
            for p in postings:
                postings_file.write(struct.pack(RECORD_FORMAT, p.doc_id, p.term_freq))
            length = len(postings) * RECORD_SIZE
            dictionary[term] = (offset, length)
            offset += length

    with open(dict_path, "w") as f:
        json.dump(dictionary, f)

    if meta_path is not None:
        doc_lengths = doc_lengths or {}
        num_docs = len(doc_lengths)
        avg_doc_len = (sum(doc_lengths.values()) / num_docs) if num_docs else 0.0
        meta = {
            "num_docs": num_docs,
            "avg_doc_len": avg_doc_len,
            # JSON keys must be strings; reader converts back to int.
            "doc_lengths": {str(k): v for k, v in doc_lengths.items()},
            "doc_metadata": {str(k): v for k, v in (doc_metadata or {}).items()},
        }
        with open(meta_path, "w") as f:
            json.dump(meta, f)
