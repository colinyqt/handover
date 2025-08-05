#!/usr/bin/env python3
"""
Quick pipeline test - minimal test to check if pipeline components work
"""

import os
import sys
from pathlib import Path

def test_basic_pipeline():
    """Test the basic pipeline functionality"""
    print("🧪 BASIC PIPELINE TEST")
    print("=" * 40)
    
    # Add the project root to Python path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(project_root / "core"))
    
    try:
        # Test if we can import the main runner
        import main
        print("✅ Main pipeline runner imported successfully")
        
        # Check if we have API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("⚠️  Setting temporary API key placeholder")
            os.environ['OPENAI_API_KEY'] = 'test-key'
        
        print("✅ Environment setup complete")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def create_test_document():
    """Create a simple test document for pipeline testing"""
    test_content = """
TECHNICAL SPECIFICATION - POWER METERS

Section 1: Multi-Function Electronic Meters
The meters shall provide the following measurements:
- True RMS current per phase & neutral ±0.5%
- True RMS voltage phase-to-phase & phase-to-neutral ±0.5%
- Real power (kW) per phase & three-phase total ±0.5%
- Apparent power (kVA) per phase & three-phase total ±0.5%
- Reactive power (kVAr) per phase & three-phase total ±0.5%
- Total power factor per phase & three-phase total ±0.5%
- Frequency ±0.5%

Section 2: Communication Requirements
- Front-panel communication port RS485/RJ45
- Protocol support for Modbus RTU
- Built-in memory >= 36 months

Section 3: Environmental Specifications
- Operating temperature up to 50 °C
- Operating voltage 400 V/230 V, 50 Hz
- CT secondary 5 A
- Overcurrent withstand 100 A for 1 s
- IP2X front face protection
"""
    
    test_file = Path("test_document.txt")
    test_file.write_text(test_content.strip(), encoding='utf-8')
    print(f"✅ Test document created: {test_file.absolute()}")
    return test_file

def main():
    """Run basic tests"""
    print("🚀 PIPELINE QUICK TEST")
    print("=" * 50)
    
    # Test 1: Basic imports
    if not test_basic_pipeline():
        print("❌ Basic pipeline test failed")
        return
    
    # Test 2: Create test document
    test_file = create_test_document()
    
    print("\n" + "=" * 50)
    print("✅ Quick test completed successfully!")
    print(f"📄 Test document: {test_file.absolute()}")
    
    print("\n🔧 NEXT STEPS:")
    print("1. Set your OpenAI API key:")
    print("   $env:OPENAI_API_KEY='your-api-key-here'")
    print("\n2. Test the debug pipeline:")
    print(f"   python main.py prompts/debug_oneshot.yaml --analysis_file {test_file}")
    print("\n3. Or test the full pipeline:")
    print(f"   python main.py prompts/oneshot.yaml --analysis_file {test_file}")

if __name__ == "__main__":
    main()
