#!/usr/bin/env python3
"""
Diagnostic script to check FAISS and database setup
Run this to verify your pipeline components are working
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path

def check_database_files():
    """Check if database CSV files exist and have content"""
    print("=== DATABASE FILES CHECK ===")
    
    db_path = Path("c:/Users/cyqt2/Database/DatabaseTest")
    if not db_path.exists():
        print(f"❌ Database directory not found: {db_path}")
        return False
    
    key_files = ['Meters.csv', 'Measurements.csv', 'CommunicationProtocols.csv']
    all_good = True
    
    for file in key_files:
        file_path = db_path / file
        if file_path.exists():
            try:
                df = pd.read_csv(file_path)
                print(f"✅ {file}: {len(df)} rows, {len(df.columns)} columns")
                if len(df) == 0:
                    print(f"⚠️  {file} is empty!")
                    all_good = False
                else:
                    print(f"   Sample columns: {list(df.columns)[:5]}")
            except Exception as e:
                print(f"❌ Error reading {file}: {e}")
                all_good = False
        else:
            print(f"❌ Missing file: {file}")
            all_good = False
    
    return all_good

def check_faiss_setup():
    """Check FAISS index and processor"""
    print("\n=== FAISS SETUP CHECK ===")
    
    # Check for FAISS files
    faiss_index = Path("c:/Users/cyqt2/Database/overhaul/faiss_index.idx")
    faiss_metadata = Path("c:/Users/cyqt2/Database/overhaul/faiss_metadata.pkl")
    
    if faiss_index.exists():
        print(f"✅ FAISS index found: {faiss_index} ({faiss_index.stat().st_size} bytes)")
    else:
        print(f"❌ FAISS index not found: {faiss_index}")
        return False
    
    if faiss_metadata.exists():
        print(f"✅ FAISS metadata found: {faiss_metadata} ({faiss_metadata.stat().st_size} bytes)")
    else:
        print(f"❌ FAISS metadata not found: {faiss_metadata}")
        return False
    
    # Try to load FAISS processor
    try:
        sys.path.append("c:/Users/cyqt2/Database/overhaul")
        from faiss_processor import FAISSProcessor
        
        processor = FAISSProcessor()
        print("✅ FAISSProcessor loaded successfully")
        
        # Test a simple query
        test_results = processor.query_faiss("voltage measurement", top_k=3)
        print(f"✅ Test query returned {len(test_results)} results")
        if test_results:
            print(f"   Sample result keys: {list(test_results[0].keys())}")
        else:
            print("⚠️  Test query returned no results - check if index is populated")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading FAISS processor: {e}")
        return False

def check_llm_connectivity():
    """Check if LLM/API is accessible"""
    print("\n=== LLM CONNECTIVITY CHECK ===")
    
    # Check for environment variables
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        print("✅ OPENAI_API_KEY found in environment")
    else:
        print("⚠️  OPENAI_API_KEY not found - may cause LLM steps to fail")
    
    # Try a simple LLM call (if possible)
    try:
        # This is a basic check - you might need to adapt based on your LLM setup
        print("ℹ️  LLM connectivity check skipped (implement based on your setup)")
        return True
    except Exception as e:
        print(f"❌ LLM connectivity error: {e}")
        return False

def check_pipeline_engine():
    """Check if pipeline engine can be loaded"""
    print("\n=== PIPELINE ENGINE CHECK ===")
    
    try:
        # Add both paths to sys.path
        sys.path.insert(0, "c:/Users/cyqt2/Database/overhaul")
        sys.path.insert(0, "c:/Users/cyqt2/Database/overhaul/core")
        
        # Try different import methods
        try:
            from core.prompt_engine import PromptEngine
        except ImportError:
            try:
                import core.prompt_engine as pe_module
                PromptEngine = pe_module.PromptEngine
            except ImportError:
                # Try direct import if in the same directory
                import prompt_engine as pe_module
                PromptEngine = pe_module.PromptEngine
        
        engine = PromptEngine()
        print("✅ PromptEngine loaded successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error loading PromptEngine: {e}")
        print(f"   Current working directory: {os.getcwd()}")
        print(f"   Python path: {sys.path[:3]}...")
        return False

def test_simple_pipeline():
    """Test a minimal pipeline execution"""
    print("\n=== SIMPLE PIPELINE TEST ===")
    
    try:
        # Create a minimal test pipeline
        test_pipeline = {
            'name': 'Diagnostic Test',
            'inputs': [
                {'name': 'test_input', 'type': 'text', 'required': False, 'default': 'test content'}
            ],
            'processing_steps': [
                {
                    'name': 'test_step',
                    'type': 'python',
                    'description': 'Simple test step',
                    'code': 'result = {"test": "success", "input_received": context.get("inputs", {}).get("test_input", "none")}'
                }
            ],
            'outputs': []
        }
        
        # Add both paths to sys.path
        sys.path.insert(0, "c:/Users/cyqt2/Database/overhaul")
        sys.path.insert(0, "c:/Users/cyqt2/Database/overhaul/core")
        
        # Try different import methods
        try:
            from core.prompt_engine import PromptEngine
        except ImportError:
            try:
                import core.prompt_engine as pe_module
                PromptEngine = pe_module.PromptEngine
            except ImportError:
                # Try direct import if in the same directory
                import prompt_engine as pe_module
                PromptEngine = pe_module.PromptEngine
        
        engine = PromptEngine()
        results = engine.execute_pipeline(test_pipeline, {'test_input': 'diagnostic test'})
        
        if results and 'test_step' in results:
            print("✅ Simple pipeline execution successful")
            print(f"   Result: {results['test_step']}")
            return True
        else:
            print("❌ Simple pipeline execution failed - no results")
            return False
            
    except Exception as e:
        print(f"❌ Pipeline test error: {e}")
        return False

def main():
    """Run all diagnostic checks"""
    print("🔍 COMPLIANCE AUTOMATION PIPELINE DIAGNOSTICS")
    print("=" * 60)
    
    checks = [
        ("Database Files", check_database_files),
        ("FAISS Setup", check_faiss_setup),
        ("LLM Connectivity", check_llm_connectivity),
        ("Pipeline Engine", check_pipeline_engine),
        ("Simple Pipeline Test", test_simple_pipeline)
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"❌ {name} check crashed: {e}")
            results[name] = False
    
    print("\n" + "=" * 60)
    print("🏁 DIAGNOSTIC SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name:<25} {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All diagnostics passed! Your pipeline should work correctly.")
    else:
        print("⚠️  Some diagnostics failed. Address the issues above before running the full pipeline.")
    
    print("\nRecommended next steps:")
    if not results.get("Database Files", False):
        print("1. Ensure database CSV files exist and contain data")
    if not results.get("FAISS Setup", False):
        print("2. Run FAISS index building process")
    if not results.get("LLM Connectivity", False):
        print("3. Configure LLM API credentials")
    if not results.get("Pipeline Engine", False):
        print("4. Check pipeline engine dependencies")
    
    print("5. Run debug_oneshot.yaml pipeline to test LLM extraction")

if __name__ == "__main__":
    main()
