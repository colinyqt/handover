# core/file_processor.py
import os
from pathlib import Path
from typing import Dict, Any

class FileProcessor:
    """Handle different file types for input processing"""
    
    def process_file(self, file_path: str) -> Dict[str, Any]:
        """Process a file and return its content with metadata"""
        
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        content = ""
        # Read content based on file type
        if path.suffix.lower() in ['.txt', '.md']:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
        elif path.suffix.lower() == '.pdf':
            try:
                import pdfplumber
                
                print(f"🔍 PDF Processing: {path.name}")
                content_parts = []
                
                with pdfplumber.open(str(path)) as pdf:
                    print(f"🔍 Found {len(pdf.pages)} pages")
                    
                    for page_num, page in enumerate(pdf.pages, 1):
                        # Extract text from page
                        page_text = page.extract_text()
                        
                        if page_text:
                            content_parts.append(page_text)
                            print(f"🔍 Page {page_num}: {len(page_text)} characters extracted")
                        else:
                            print(f"⚠️ Page {page_num}: No text extracted")
                        
                        # Also extract tables if present
                        tables = page.extract_tables()
                        if tables:
                            print(f"🔍 Page {page_num}: {len(tables)} tables found")
                            for table_num, table in enumerate(tables, 1):
                                # Convert table to text
                                table_text = "\n".join([
                                    " | ".join([cell or "" for cell in row]) 
                                    for row in table
                                ])
                                content_parts.append(f"\n[TABLE {table_num}]\n{table_text}\n[/TABLE {table_num}]\n")
                
                # With YaRN: No need to truncate large PDFs
                content = "\n".join(content_parts)
                
                # Debug: Show preview of extracted content
                if content:
                    print(f"🔍 Content preview (first 200 chars): {content[:200]}...")
                    print(f"🔍 Content preview (last 200 chars): ...{content[-200:]}")
                
            except ImportError:
                print("❌ pdfplumber not installed. Install with: pip install pdfplumber")
                content = f"[PDF processing failed: pdfplumber not installed]"
            except Exception as e:
                print(f"❌ PDF extraction failed: {e}")
                content = f"[PDF extraction failed: {str(e)}]"
        else:
            # For now, treat everything else as text
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(path, 'rb') as f:
                    content = f"[Binary file: {path.name}]"
        
        # Add metadata for context optimization
        return {
            'name': path.name,
            'content': content,  # Full content, no truncation
            'content_length': len(content),
            'estimated_tokens': len(content) // 4,  # Rough estimate
            'requires_yarn': len(content) > 32000  # Flag for YaRN usage
        }