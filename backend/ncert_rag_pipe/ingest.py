import os
import faiss
import pickle
import glob
import json
from pathlib import Path
from typing import Optional
from pypdf import PdfReader
import pypdf.filters as _pypdf_filters
from sentence_transformers import SentenceTransformer

# Raise pypdf decompression limit for large NCERT PDFs (default 75 MB). Trusted ingest only.
_DECOMPRESS_LIMIT = 500 * 1024 * 1024  # 500 MB
_pypdf_filters.ZLIB_MAX_OUTPUT_LENGTH = _DECOMPRESS_LIMIT
_pypdf_filters.LZW_MAX_OUTPUT_LENGTH = _DECOMPRESS_LIMIT

# -----------------------------
# CONFIG
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))  # Go up two levels: ncert_rag_pipe -> backend -> root

INDEXES_DIR = os.path.join(PROJECT_ROOT, "indexes")
CHUNK_SIZE = 1000 
MODEL_NAME = "all-MiniLM-L6-v2"

# Prefer BharatGen multilingual books repo layout:
# <BHARATGEN_BOOKS_PATH>/
#   English/<Subject>/*.(pdf|txt|md)
#   Hindi/<Subject>/*.(pdf|txt|md)
#
# Or alternatively:
# <BHARATGEN_BOOKS_PATH>/
#   en/<Subject>/...
#   hi/<Subject>/...
#
# If BHARATGEN_BOOKS_PATH is not set, fallback to <PROJECT_ROOT>/data.
BOOKS_ROOT = os.getenv("BHARATGEN_BOOKS_PATH", os.path.join(PROJECT_ROOT, "data"))

LANG_DIR_ALIASES = {
    "en": ["English", "EN", "en"],
    "hi": ["Hindi", "HI", "hi"],
}

SUPPORTED_EXTS = (".pdf", ".txt", ".md")

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def read_pdf(path):
    """Extracts text from a single PDF file."""
    try:
        reader = PdfReader(path)
        text = ""
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text += content + " "
        return text
    except Exception as e:
        print(f"⚠️ Error reading {path}: {e}")
        return ""

def read_text_file(path: str) -> str:
    """Reads UTF-8 text files (txt/md)."""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        print(f"⚠️ Error reading {path}: {e}")
        return ""

def read_any(path: str) -> str:
    p = path.lower()
    if p.endswith(".pdf"):
        return read_pdf(path)
    if p.endswith(".txt") or p.endswith(".md"):
        return read_text_file(path)
    return ""

def chunk_text(text, chunk_size=1000):
    """Splits text into chunks of specified word count."""
    words = text.split()
    return [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]

def normalize_chapter_title(filename: str) -> str:
    """
    Best-effort chapter title extraction from a filename.
    Keeps it robust across naming conventions by:
    - stripping extension
    - replacing underscores/hyphens with spaces
    - collapsing whitespace
    """
    stem = Path(filename).stem
    s = stem.replace("_", " ").replace("-", " ")
    s = " ".join(s.split())
    return s.strip()

def find_language_root(lang_code: str) -> Optional[Path]:
    root = Path(BOOKS_ROOT)
    for candidate in LANG_DIR_ALIASES.get(lang_code, []):
        p = root / candidate
        if p.exists() and p.is_dir():
            return p
    return None

def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

# -----------------------------
# MAIN INGESTION LOGIC
# -----------------------------
def run_ingestion_for_language(lang_code: str) -> None:
    """
    Build a language-specific FAISS index and a chapters manifest.
    Output:
      indexes/<lang_code>/vector_db.index
      indexes/<lang_code>/chunks_metadata.pkl
      indexes/<lang_code>/chapters_manifest.json
    """
    lang_root = find_language_root(lang_code)
    if lang_root is None:
        print(f"⚠️ Language folder not found for '{lang_code}' under {BOOKS_ROOT}. Skipping.")
        return

    out_dir = Path(INDEXES_DIR) / lang_code
    ensure_dir(out_dir)
    index_path = out_dir / "vector_db.index"
    chunks_path = out_dir / "chunks_metadata.pkl"
    chapters_manifest_path = out_dir / "chapters_manifest.json"

    print(f"\n🚀 Ingesting language='{lang_code}' from: {lang_root}")

    subjects = [p for p in lang_root.iterdir() if p.is_dir()]
    if not subjects:
        print(f"❌ No subject folders found in {lang_root}.")
        return

    chapters_manifest: dict[str, list[str]] = {}
    all_chunks: list[str] = []

    for subject_dir in sorted(subjects, key=lambda p: p.name.lower()):
        subject = subject_dir.name
        files: list[str] = []
        for ext in SUPPORTED_EXTS:
            # Include nested dirs (e.g. Subject/Class-11/*.pdf)
            files.extend(glob.glob(str(subject_dir / "**" / f"*{ext}")))
        if not files:
            continue

        chapters_manifest.setdefault(subject, [])

        for fp in sorted(files):
            fname = os.path.basename(fp)
            chapter_title = normalize_chapter_title(fname)
            if chapter_title not in chapters_manifest[subject]:
                chapters_manifest[subject].append(chapter_title)

            print(f"📖 [{lang_code}] {subject}: {fname}")
            text = read_any(fp)
            if not text.strip():
                continue
            file_chunks = chunk_text(text, CHUNK_SIZE)
            all_chunks.extend(file_chunks)

    if not all_chunks:
        print(f"❌ No chunks created for language='{lang_code}'.")
        return

    print(f"📦 [{lang_code}] Total chunks created: {len(all_chunks)}")
    print("🧠 Generating embeddings (this may take a moment)...")
    model = SentenceTransformer(MODEL_NAME)
    embeddings = model.encode(all_chunks, show_progress_bar=True)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    faiss.write_index(index, str(index_path))

    with open(chunks_path, "wb") as f:
        pickle.dump(all_chunks, f)

    with open(chapters_manifest_path, "w", encoding="utf-8") as f:
        json.dump(chapters_manifest, f, ensure_ascii=False, indent=2)

    print(f"✅ [{lang_code}] Index saved to {index_path}")
    print(f"✅ [{lang_code}] Chapters manifest saved to {chapters_manifest_path}")


def run_ingestion():
    print("🚀 Starting Multilingual Ingestion...")
    print(f"📌 Books root: {BOOKS_ROOT}")
    ensure_dir(Path(INDEXES_DIR))
    run_ingestion_for_language("en")
    run_ingestion_for_language("hi")

if __name__ == "__main__":
    run_ingestion()