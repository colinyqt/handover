
import asyncio
from core.prompt_engine import PromptEngine
from pathlib import Path

def chunk_text(text, chunk_size=7999):
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

def extract_text_from_pdf(pdf_path):
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        print("PyPDF2 is required for PDF reading. Install with 'pip install PyPDF2'.")
        return ""
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

async def test_foreach_llm_step(chunks):
    engine = PromptEngine()
    steps = [
        {
            'name': 'extract_chunks',
            'type': 'python',
            'code': f"result = {repr(chunks)}"
        },
        {
            'name': 'llm_chunked',
            'type': 'llm',
            'prompt_template': 'Process: {{item}}',
            'foreach': "context['extract_chunks']",
            'llm_model': 'qwen2.5-coder:7b-instruct'
        }
    ]
    context = {}
    print("\nChunks to be processed:")
    for idx, chunk in enumerate(chunks):
        print(f"Chunk {idx}: {repr(chunk)[:100]}")
    results = await engine._execute_pipeline(steps, context)

    print("\nTest foreach LLM step results:")
    result = results.get('llm_chunked')
    print(f"Type of llm_chunked result: {type(result)}")
    if isinstance(result, list):
        for idx, res in enumerate(result):
            print(f"Chunk {idx} LLM response: {res}")
        assert len(result) == len(chunks), f"Should process all chunks: got {len(result)}, expected {len(chunks)}"
        print("Test passed!\n")
    else:
        print(f"llm_chunked result is not a list. Actual value:")
        print(result)
        print("Test failed: foreach logic did not return a list of results.")


if __name__ == "__main__":
    pdf_path = "C:/Users/cyqt2/Database/overhaul/examples/redacted_output.pdf"
    if not Path(pdf_path).exists():
        print(f"PDF file not found: {pdf_path}")
        exit(1)
    print(f"Reading and chunking PDF: {pdf_path}")
    text = extract_text_from_pdf(pdf_path)
    chunks = chunk_text(text, chunk_size=7999)
    print(f"Extracted {len(chunks)} chunks from PDF.")
    asyncio.run(test_foreach_llm_step(chunks))
