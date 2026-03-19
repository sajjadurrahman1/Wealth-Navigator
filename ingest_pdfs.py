import os
import json
import re
import time
from pathlib import Path

import numpy as np
import faiss
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer


PDF_DIR = Path("rag/data/pdfs")
INDEX_PATH = Path("rag/data/faiss.index")
META_PATH = Path("rag/data/metadata.jsonl")

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE = 900      # characters per chunk (tune)
CHUNK_OVERLAP = 150   # overlap to preserve context


def clean_text(t: str) -> str:
    t = t.replace("\x00", " ")
    t = re.sub(r"\s+", " ", t).strip()
    return t


def chunk_text(text: str, chunk_size: int, overlap: int):
    """
    Split text into overlapping chunks.
    Added safety checks to prevent infinite loops and memory issues.
    """
    chunks = []
    start = 0
    n = len(text)
    max_chunks = (n // (chunk_size - overlap)) + 10  # Safety limit
    chunk_count = 0
    
    while start < n and chunk_count < max_chunks:
        end = min(start + chunk_size, n)
        chunk = text[start:end]
        chunk = clean_text(chunk)
        if len(chunk) > 50:  # ignore tiny junk chunks
            chunks.append(chunk)
            chunk_count += 1
        start = end - overlap
        if start < 0:
            start = 0
        if start >= n:
            break
        # Safety check: ensure we're making progress
        if end == start:
            break
    return chunks


def extract_pdf_pages(pdf_path: Path, show_progress: bool = True):
    """Extract text from all pages of a PDF file."""
    try:
        reader = PdfReader(str(pdf_path))
        total_pages = len(reader.pages)
        if show_progress:
            print(f"    Extracting {total_pages} pages...", end="", flush=True)
    except Exception as e:
        print(f"\nWarning: Could not read PDF {pdf_path.name}: {e}")
        return
    
    extracted = 0
    skipped = 0
    last_progress_time = time.time()
    
    for i, page in enumerate(reader.pages):
        page_start = time.time()
        text = ""
        
        try:
            # Show progress every 10 pages, or every 5 seconds if extraction is slow
            current_time = time.time()
            should_show_progress = False
            if show_progress:
                if total_pages > 10 and (i + 1) % 10 == 0:
                    should_show_progress = True
                elif current_time - last_progress_time > 5.0:  # Every 5 seconds
                    should_show_progress = True
                
                if should_show_progress:
                    print(f" {i+1}/{total_pages}", end="", flush=True)
                    last_progress_time = current_time
            
            # Direct extraction - try multiple methods
            text = ""
            try:
                # Method 1: Standard extraction
                text = page.extract_text() or ""
                
                # Method 2: Try with layout preservation if first method fails
                if not text or len(text.strip()) < 10:
                    try:
                        text = page.extract_text(extraction_mode="layout") or ""
                    except:
                        pass
                
                # Method 3: Try alternative extraction (removed - not useful)
                # If standard extraction fails, text remains empty
                
                # Check if extraction took too long (warn but don't skip)
                page_time = time.time() - page_start
                if page_time > 10.0 and show_progress:
                    print(f"\n⚠️  Page {i+1} took {page_time:.1f}s", end="", flush=True)
                    
            except Exception as extract_error:
                if show_progress and i == 0:  # Only show error for first page to avoid spam
                    print(f"\n⚠️  Extraction error (showing first page only): {extract_error}", end="", flush=True)
                text = ""
            
            # Debug: Show what we got for first few pages
            if i < 3 and show_progress:
                text_len = len(text.strip()) if text else 0
                preview = text[:100].replace('\n', ' ').replace('\r', ' ') if text else "EMPTY"
                print(f"\n    [Page {i+1}] Length: {text_len}, Preview: '{preview[:60]}...'", end="", flush=True)
            
            # Only count as extracted if we got meaningful text
            # Lowered threshold from 10 to 5 characters to be less strict
            cleaned_text = text.strip() if text else ""
            if cleaned_text and len(cleaned_text) > 5:  # At least 5 characters
                extracted += 1
            else:
                skipped += 1
                if i < 3 and show_progress:
                    print(f" → SKIPPED (too short: {len(cleaned_text)} chars)", end="", flush=True)
                text = ""  # Empty or too short
                
        except Exception as e:
            if show_progress:
                print(f"\n⚠️  Error on page {i+1}: {e}", end="", flush=True)
            text = ""
            skipped += 1
        
        yield i + 1, clean_text(text)
    
    if show_progress:
        status = f" ✓ ({extracted}/{total_pages} pages extracted"
        if skipped > 0:
            status += f", {skipped} skipped"
        status += ")"
        print(status)


def main():
    if not PDF_DIR.exists():
        raise FileNotFoundError(f"PDF folder not found: {PDF_DIR.resolve()}")

    print("Loading embedding model...")
    model = SentenceTransformer(MODEL_NAME)
    
    # Get embedding dimension from a test encoding
    test_dim = model.get_sentence_embedding_dimension()
    print(f"Embedding dimension: {test_dim}")

    # Process in batches to avoid memory issues
    BATCH_SIZE = 32  # Reduced batch size for better memory management
    batch_chunks = []
    batch_meta = []
    total_chunks = 0
    faiss_index = None

    # Prepare output files
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Open metadata file in write mode (will overwrite if exists)
    meta_file = META_PATH.open("w", encoding="utf-8")

    pdf_files = sorted([p for p in PDF_DIR.glob("*.pdf")])
    if not pdf_files:
        raise ValueError(f"No PDFs found in {PDF_DIR.resolve()}")

    def process_batch():
        """Process accumulated chunks, add to FAISS index, and write metadata incrementally."""
        nonlocal batch_chunks, batch_meta, faiss_index, total_chunks
        if not batch_chunks:
            return
        
        try:
            batch_start = time.time()
            print(f"  Encoding {len(batch_chunks)} chunks...", end="", flush=True)
            
            # This is the slow part - encoding
            embeddings = model.encode(
                batch_chunks, 
                normalize_embeddings=True, 
                show_progress_bar=False,
                batch_size=32,  # Process embeddings in smaller batches
                convert_to_numpy=True
            )
            embeddings = np.array(embeddings, dtype="float32")
            
            encode_time = time.time() - batch_start
            print(f" ({encode_time:.1f}s)", end="", flush=True)
            
            # Initialize FAISS index on first batch
            if faiss_index is None:
                faiss_index = faiss.IndexFlatIP(test_dim)
                print(" [init index]", end="", flush=True)
            
            # Add vectors to FAISS index incrementally
            faiss_index.add(embeddings)
            
            # Write metadata incrementally to disk
            for meta in batch_meta:
                meta_file.write(json.dumps(meta, ensure_ascii=False) + "\n")
            
            total_chunks += len(batch_chunks)
            print(f" ✓ (total: {total_chunks})")
            
        except Exception as e:
            print(f"\n  ❌ Error processing batch: {e}")
            import traceback
            traceback.print_exc()
        finally:
            batch_chunks = []
            batch_meta = []

    try:
        for pdf_path in pdf_files:
            pdf_start = time.time()
            print(f"\n📄 Ingesting: {pdf_path.name}")
            page_count = 0
            chunk_count = 0
            last_progress = 0
            
            for page_num, page_text in extract_pdf_pages(pdf_path, show_progress=True):
                page_count += 1
                
                if not page_text:
                    continue

                chunks = chunk_text(page_text, CHUNK_SIZE, CHUNK_OVERLAP)
                if not chunks:
                    continue

                # Add chunks to batch
                for chunk in chunks:
                    batch_chunks.append(chunk)
                    batch_meta.append({
                        "source": pdf_path.name,
                        "page": page_num,
                        "text": chunk,
                    })
                    chunk_count += 1
                    
                    # Process batch when it reaches BATCH_SIZE
                    if len(batch_chunks) >= BATCH_SIZE:
                        process_batch()
                        last_progress = chunk_count
            
            # Process remaining chunks in batch
            if batch_chunks:
                process_batch()
            
            pdf_time = time.time() - pdf_start
            print(f"  ✓ Completed: {page_count} pages, {chunk_count} chunks ({pdf_time:.1f}s)")

        if faiss_index is None or total_chunks == 0:
            raise ValueError("No chunks were extracted from PDFs. Check if PDFs contain readable text.")

        print(f"\nFinalizing index with {total_chunks} total chunks...")
        
        # Save FAISS index
        print(f"Saving index to {INDEX_PATH.resolve()}...")
        faiss.write_index(faiss_index, str(INDEX_PATH))
        
        # Close metadata file
        meta_file.close()

        print(f"\n✅ Done!")
        print(f"   Total vectors: {total_chunks}")
        print(f"   Index saved: {INDEX_PATH.resolve()}")
        print(f"   Metadata saved: {META_PATH.resolve()}")
        
    except Exception as e:
        meta_file.close()
        raise


if __name__ == "__main__":
    main()
