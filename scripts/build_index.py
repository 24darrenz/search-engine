#!/usr/bin/env python
"""Usage: python scripts/build_index.py ./data/raw

Reads every .txt file in the given directory as one document, builds the
index, and writes it to data/index/.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from search_engine.index.builder import IndexBuilder
from search_engine.storage.writer import write_index


def main(corpus_dir: str):
    corpus_path = Path(corpus_dir)
    files = sorted(corpus_path.glob("*.txt"))
    print(f"Found {len(files)} documents in {corpus_dir}")

    builder = IndexBuilder()
    start = time.time()
    for doc_id, path in enumerate(files):
        text = path.read_text(errors="ignore")
        builder.add_document(doc_id, text, metadata={"title": path.stem, "path": str(path)})

    index = builder.finalize()
    elapsed = time.time() - start

    out_dir = Path("data/index")
    out_dir.mkdir(parents=True, exist_ok=True)
    write_index(
        index,
        str(out_dir / "index.postings"),
        str(out_dir / "index.dict"),
        doc_lengths=builder.doc_lengths,
        doc_metadata=builder.doc_metadata,
        meta_path=str(out_dir / "index.meta"),
    )

    print(f"Indexed: {len(files)} documents")
    print(f"Vocabulary: {len(index)} terms")
    print(f"Time: {elapsed:.2f}s")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/build_index.py <corpus_dir>")
        sys.exit(1)
    main(sys.argv[1])
