import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
MODEL_NAME = os.getenv("RAG_EMBED_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
DEFAULT_K = 5
MIN_CHUNK_WORDS = 5
MAX_CHUNK_WORDS = 5000


def _extract_block_label_from_text(text: str) -> Optional[str]:
    """Extract `Block <name>` label from arbitrary text/path segment."""
    if not text:
        return None

    normalized = re.sub(r"\s+", " ", str(text)).strip()
    match = re.search(r"(?i)\bblock\b[\s:\-]*([a-z0-9]+(?:[\s\-]+[a-z0-9]+){0,6})\b", normalized)
    if not match:
        return None

    captured = re.split(r"(?i)\b(unit|chapter|structure|objectives|introduction)\b", match.group(1))[0].strip()
    if not captured:
        return None

    first_token = captured.split()[0].lower()
    if first_token in {"here", "there", "this", "that", "the", "a", "an", "of", "for", "to", "in"}:
        return None

    return f"Block {captured}"


class MinimalRAGRetriever:
    def __init__(self, store_dir: Path):
        if not store_dir.exists():
            raise FileNotFoundError(f"RAG store not found: {store_dir}")

        self.store_dir = store_dir
        self.model = SentenceTransformer(MODEL_NAME)
        self.master = self._load_master()
        self.records = self._build_records()
        self.cache: Dict[str, Dict[str, Any]] = {}

    def _load_master(self) -> Dict[str, Any]:
        master_path = self.store_dir / "master_index.json"
        if not master_path.exists():
            raise FileNotFoundError(f"master_index.json not found in: {self.store_dir}")
        with open(master_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _resolve_doc_path(self, doc_id: str, metadata: Dict[str, Any]) -> Optional[Path]:
        store_path = str(metadata.get("store_path", "")).strip()
        if store_path:
            p = Path(store_path)
            if not p.is_absolute():
                p = (PROJECT_ROOT / p).resolve()
            if p.exists():
                return p

        matches = list(self.store_dir.rglob(doc_id))
        return matches[0] if matches else None


    def _extract_subject_and_block(self, store_path: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract subject (course name) and block label from store_path."""
        if not store_path:
            return None, None

        normalized = str(store_path).replace("\\", "/")
        parts = [p for p in normalized.split("/") if p and p.lower() != "egyankosh"]

        subject = None
        block = None

        # Iterate through path segments. If a folder has "block X", it's the block.
        # The folder immediately before it is the course/subject.
        for idx, part in enumerate(parts):
            if re.search(r"(?i)\bblock\s+\d+", part):
                block = part  # Keep full name (e.g., "BLOCK 1 KALIDASA") for precise metadata
                if idx > 0 and not parts[idx - 1].startswith("rag_store"):
                    subject = parts[idx - 1]
                break

        # Fallback if no block keyword is found
        if not subject and len(parts) >= 2:
            subject = parts[-2]

        return subject, block

    def _build_records(self) -> List[Dict[str, Any]]:
        docs = self.master.get("documents", {})
        records: List[Dict[str, Any]] = []

        for doc_id, meta in docs.items():
            doc_dir = self._resolve_doc_path(doc_id, meta)
            if not doc_dir:
                continue

            chunks_path = doc_dir / "chunks.json"
            embeddings_path = doc_dir / "embeddings.npy"
            metadata_path = doc_dir / "metadata.json"
            if not (chunks_path.exists() and embeddings_path.exists() and metadata_path.exists()):
                continue

            searchable = " ".join(
                [
                    doc_id,
                    str(meta.get("file_name", "")),
                    str(meta.get("store_path", "")),
                    doc_dir.as_posix(),
                ]
            ).lower()

            store_path = str(meta.get("store_path", ""))
            subject, block = self._extract_subject_and_block(store_path)

            records.append(
                {
                    "doc_id": doc_id,
                    "doc_dir": doc_dir,
                    "meta": meta,
                    "search_text": searchable,
                    "extracted_subject": subject,
                    "extracted_block": block,
                }
            )

        if not records:
            raise FileNotFoundError(
                f"No usable unit folders found under {self.store_dir}. "
                "Expected chunks.json + embeddings.npy + metadata.json per document."
            )

        return records

    def _candidate_records(
        self,
        query: str,
        subject: Optional[str],
        chapter: Optional[str],
        standard: Optional[str],
        block: Optional[str],
        max_candidates: int = 40,
    ) -> List[Dict[str, Any]]:
        filtered_records = self.records

        effective_block = block
        if not effective_block and chapter:
            # Check if chapter string passed from UI holds the block
            if re.search(r"(?i)\bblock\s+\d+", chapter):
                effective_block = chapter

        had_explicit_filters = bool(subject or effective_block)

        if subject:
            subject_lower = subject.lower()
            filtered_records = [
                r for r in filtered_records
                if r["extracted_subject"] and subject_lower in r["extracted_subject"].lower()
            ]

        if effective_block:
            # Ensure exact matching so "Block 1" doesn't retrieve "Block 10"
            target_match = re.search(r"(?i)\bblock\s*(\d+)", effective_block)
            if target_match:
                b_num = target_match.group(1)
                # Regex boundary \b ensures it matches exactly the number
                pattern = rf"(?i)\bblock\s*0*{b_num}\b"
                filtered_records = [
                    r for r in filtered_records
                    if r["extracted_block"] and re.search(pattern, r["extracted_block"])
                ]
            else:
                block_lower = effective_block.lower()
                filtered_records = [
                    r for r in filtered_records
                    if r["extracted_block"] and block_lower in r["extracted_block"].lower()
                ]

        if not filtered_records and had_explicit_filters:
            return []

        if not filtered_records:
            filtered_records = self.records

        return filtered_records[:max_candidates]

    def _load_doc_payload(self, record: Dict[str, Any]) -> Dict[str, Any]:
        doc_id = record["doc_id"]
        if doc_id in self.cache:
            return self.cache[doc_id]

        doc_dir: Path = record["doc_dir"]
        with open(doc_dir / "chunks.json", "r", encoding="utf-8") as f:
            chunks = json.load(f)
        embeddings = np.load(doc_dir / "embeddings.npy")

        if not isinstance(chunks, list):
            raise ValueError(f"chunks.json in {doc_dir} must be a list")
        if embeddings.ndim == 1:
            embeddings = embeddings.reshape(1, -1)
        if embeddings.shape[0] != len(chunks):
            raise ValueError(
                f"Chunk/embedding mismatch in {doc_dir}: chunks={len(chunks)}, embeddings={embeddings.shape[0]}"
            )

        payload = {"chunks": chunks, "embeddings": embeddings}
        self.cache[doc_id] = payload
        return payload

    def _chunk_text(self, chunk: Any) -> str:
        if isinstance(chunk, dict):
            return str(chunk.get("text", ""))
        if isinstance(chunk, str):
            return chunk
        return ""

    def _word_count(self, text: str) -> int:
        return len((text or "").split())

    def retrieve(
        self,
        query: str,
        subject: Optional[str],
        chapter: Optional[str],
        standard: Optional[str],
        block: Optional[str],
        k: int = DEFAULT_K,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        query = (query or "").strip()
        if not query:
            return "", []

        query_vec = self.model.encode([query], normalize_embeddings=True)[0]
        candidates = self._candidate_records(query, subject, chapter, standard, block)

        ranked: List[Tuple[float, str, Dict[str, Any]]] = []

        for record in candidates:
            payload = self._load_doc_payload(record)
            embeddings = payload["embeddings"]

            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            normalized = embeddings / norms
            sims = normalized @ query_vec

            if sims.size == 0:
                continue

            local_top_n = min(max(10, k * 10), sims.shape[0])
            local_top = np.argsort(sims)[-local_top_n:][::-1]
            for idx in local_top:
                chunk = payload["chunks"][int(idx)]
                text = self._chunk_text(chunk).strip()
                wc = self._word_count(text)
                if wc <= MIN_CHUNK_WORDS or wc >= MAX_CHUNK_WORDS:
                    continue

                meta = {
                    "doc_id": record["doc_id"],
                    "file_name": record["meta"].get("file_name"),
                    "source_path": record["meta"].get("store_path"),
                    "title": chunk.get("title") if isinstance(chunk, dict) else None,
                    "page": chunk.get("page") if isinstance(chunk, dict) else None,
                    "similarity": float(sims[int(idx)]),
                    "word_count": wc,
                }
                ranked.append((float(sims[int(idx)]), text, meta))

        if not ranked:
            return "", []

        ranked.sort(key=lambda item: item[0], reverse=True)
        chosen = ranked[: max(1, k)]
        texts = [x[1] for x in chosen]
        metas = [x[2] for x in chosen]
        return "\n\n".join(texts), metas
