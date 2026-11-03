"""Load the on-disk index back without rebuilding it from the corpus."""
import json
import struct

from search_engine.index.posting import Posting
from search_engine.storage.writer import RECORD_FORMAT, RECORD_SIZE


class IndexReader:
    def __init__(self, postings_path: str, dict_path: str, meta_path: str | None = None):
        with open(dict_path) as f:
            self.dictionary: dict[str, tuple[int, int]] = json.load(f)
        self._postings_path = postings_path

        self.num_docs = 0
        self.avg_doc_len = 0.0
        self.doc_lengths: dict[int, int] = {}
        self.doc_metadata: dict[int, dict] = {}

        if meta_path is not None:
            with open(meta_path) as f:
                meta = json.load(f)
            self.num_docs = meta["num_docs"]
            self.avg_doc_len = meta["avg_doc_len"]
            self.doc_lengths = {int(k): v for k, v in meta["doc_lengths"].items()}
            self.doc_metadata = {int(k): v for k, v in meta["doc_metadata"].items()}

    def get_postings(self, term: str) -> list[Posting]:
        if term not in self.dictionary:
            return []
        offset, length = self.dictionary[term]
        with open(self._postings_path, "rb") as f:
            f.seek(offset)
            raw = f.read(length)
        postings = []
        for i in range(0, len(raw), RECORD_SIZE):
            doc_id, term_freq = struct.unpack(RECORD_FORMAT, raw[i : i + RECORD_SIZE])
            postings.append(Posting(doc_id=doc_id, term_freq=term_freq))
        return postings
