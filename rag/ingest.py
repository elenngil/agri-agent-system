"""
Indexa documentos Markdown en ChromaDB.
Ejecutar una vez (o cuando se añadan documentos nuevos):
    python -m rag.ingest
"""

import re
from pathlib import Path

import yaml
import chromadb
from sentence_transformers import SentenceTransformer

DOCUMENTS_DIR = Path(__file__).parent / "documents"
CHROMA_DIR    = Path(__file__).parent.parent / "chroma_db"
COLLECTION    = "agri_knowledge"
MODEL_NAME    = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
CHUNK_SIZE    = 600
OVERLAP       = 80


def parse_frontmatter(text: str) -> tuple[dict, str]:
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not match:
        return {}, text
    return yaml.safe_load(match.group(1)) or {}, text[match.end():]


def split_chunks(text: str) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks, current = [], ""
    for p in paragraphs:
        if len(p) > CHUNK_SIZE:
            if current:
                chunks.append(current.strip())
                current = ""
            chunks.append(p[:CHUNK_SIZE])
            continue
        if len(current) + len(p) > CHUNK_SIZE:
            chunks.append(current.strip())
            current = current[-OVERLAP:] + "\n\n" + p
        else:
            current = current + "\n\n" + p if current else p
    if current.strip():
        chunks.append(current.strip())
    return chunks


def ingest(reset: bool = False) -> int:
    encoder = SentenceTransformer(MODEL_NAME)
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    if reset:
        try:
            client.delete_collection(COLLECTION)
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )

    ids, docs, embeddings, metas = [], [], [], []

    for md_file in sorted(DOCUMENTS_DIR.glob("*.md")):
        raw = md_file.read_text(encoding="utf-8")
        metadata, content = parse_frontmatter(raw)
        metadata["filename"] = md_file.name

        for i, chunk in enumerate(split_chunks(content)):
            chunk_id = f"{md_file.stem}__chunk_{i}"
            clean_meta = {
                k: str(v) for k, v in metadata.items()
                if isinstance(v, (str, int, float, bool))
            }
            clean_meta["chunk_index"] = i
            ids.append(chunk_id)
            docs.append(chunk)
            metas.append(clean_meta)

        print(f"  {md_file.name}: {len(split_chunks(content))} chunks")

    if not ids:
        print("No se encontraron documentos.")
        return 0

    embeddings = SentenceTransformer(MODEL_NAME).encode(docs, show_progress_bar=True).tolist()
    collection.upsert(ids=ids, documents=docs, embeddings=embeddings, metadatas=metas)
    print(f"\n✓ {len(ids)} chunks indexados en '{COLLECTION}'")
    return len(ids)


if __name__ == "__main__":
    ingest(reset=True)
