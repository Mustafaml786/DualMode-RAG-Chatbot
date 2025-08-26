#!/usr/bin/env python3
"""
Performance test script for PDF processing optimizations
"""
import os
import time
import asyncio
from pathlib import Path

# Add the backend directory to Python path
import sys
sys.path.append(str(Path(__file__).parent))

from services.rag_service import process_and_embed_file
import uuid

def test_pdf_processing():
    """Test PDF processing performance with different file sizes"""

    # Test files in uploaded_files directory
    test_dir = Path("uploaded_files")
    test_files = list(test_dir.glob("*.pdf"))

    if not test_files:
        print("No PDF files found in uploaded_files directory")
        return

    print("=== PDF Processing Performance Test ===\n")

    for pdf_file in test_files:
        print(f"Testing file: {pdf_file.name}")
        print(f"File size: {pdf_file.stat().st_size / (1024*1024):.2f} MB")

        # Start timing
        start_time = time.time()

        try:
            # Test the processing function
            user_id = uuid.uuid4()
            file_id = uuid.uuid4()

            chunks_created = process_and_embed_file(
                str(pdf_file),
                user_id,
                file_id
            )

            # Calculate processing time
            end_time = time.time()
            processing_time = end_time - start_time

            print(f"Chunks created: {chunks_created}")
            print(".2f")
            print(".2f")
            print(".2f")
            print("Status: ✅ SUCCESS\n")

        except Exception as e:
            end_time = time.time()
            processing_time = end_time - start_time
            print(f"Status: ❌ FAILED - {str(e)}")
            print(".2f")
            print()

if __name__ == "__main__":
    test_pdf_processing()
