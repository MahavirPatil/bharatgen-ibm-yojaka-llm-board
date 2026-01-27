# BharatGen - NCERT Question Generator

BharatGen is an interactive study tool that generates NCERT/CBSE-aligned questions across Math, Physics, Chemistry, and Biology using multiple LLM backends and an optional RAG pipeline built on NCERT PDFs.

## Features

- Modern study UI with Tailwind CSS
- FastAPI backend with multiple LLM support
- RAG pipeline for context-aware question generation
- Support for cloud models (Gemini, GPT-4o) and local models (Llama, Qwen, Granite, Param)
- Configurable question types and cognitive depth levels

## Project Structure

```
bharatgen-ibm-yojaka-llmquestion-board/
├── backend/
│   ├── app.py              # FastAPI app entry point (debug mode)
│   ├── main.py             # FastAPI routes and LLM integration
│   ├── requirements.txt    # Python dependencies
│   └── ncert_rag_pipe/     # RAG pipeline module
│       ├── main.py         # RAG retriever
│       └── ingest.py       # PDF ingestion script
├── frontend/
│   └── index.html         # Single-page UI
├── data/                   # NCERT PDFs (gitignored)
├── vector_db.index        # FAISS index (gitignored)
└── chunks_metadata.pkl    # Chunk metadata (gitignored)
```

## Prerequisites

- Python 3.9+
- (Optional) CUDA-capable GPU for local models
- API keys for cloud models (Gemini, OpenAI)
- Ollama installed if using local Ollama models

## Installation

```bash
cd bharatgen-ibm-yojaka-llmquestion-board
pip install -r backend/requirements.txt
```

## Configuration

Create a `.env` file in the project root:

```bash
GEMINI_API_KEY_21=your_gemini_key_here
OPENAI_API_KEY=your_openai_key_here

# Path to frontend (relative to backend/)
FRONTEND_RELATIVE_PATH=../frontend/index.html

# Path to local HF model (relative to backend/ or absolute)
PARAM1_7B_RELATIVE_PATH=../transformer/models/param1-7b
```

## Running the Application

Start the backend in debug mode:

```bash
python backend/app.py
```

The application will be available at `http://localhost:8000/`

## RAG Pipeline Setup

1. Place NCERT PDFs in the `data/` folder at the project root
2. Run the ingestion script:

```bash
python backend/ncert_rag_pipe/ingest.py
```

This will:
- Extract text from all PDFs in `data/`
- Chunk and embed the content
- Create `vector_db.index` and `chunks_metadata.pkl` at the project root

## Available Models

- `gemini` - Google Gemini 3 Flash
- `chatgpt` - OpenAI GPT-4o
- `local-llama` - Local Llama 3 (via Ollama)
- `qwen` - Qwen 2.5 (via Ollama)
- `granite3.3:8b` - IBM Granite 3 (via Ollama)
- `rag-piped-llama` - Llama 3 with RAG context
- `param.1:7b` - Local Param 1 7B model
- `rag-piped-param` - Param 1 7B with RAG context

## Usage

1. Select a subject (Math, Physics, Chemistry, Biology)
2. Choose a chapter from the dropdown
3. Enter a topic
4. Set cognitive depth level (DOK 1-4)
5. Configure question distribution by type
6. Click "GENERATE SESSION" to create questions

## License

[Add your license here]
