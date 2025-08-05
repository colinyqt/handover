#!/usr/bin/env python3
"""
Direct test of Qwen LLM with extraction prompts
"""

import asyncio
import sys
import os
sys.path.append("c:/Users/cyqt2/Database/overhaul/core")

from llm_processor import LLMProcessor

async def test_qwen_extraction():
    """Test Qwen with a simple extraction prompt"""
    print("🧪 TESTING QWEN LLM EXTRACTION")
    print("=" * 50)
    
    # Test document content
    test_content = """
TECHNICAL SPECIFICATION – ELECTRICAL SERVICES
1.20 METERS AND INSTRUMENTS
The contestable customer meter scheme shall be implemented.
Meters, instruments and relays for external panel mounting shall be of flush pattern, with square
escutcheon plates finished matt black. Indicating instruments shall comply with IEC 60051, IEC
61010, IEC 60529. They shall be of accuracy Class 0.5. Scale shall be of length 90 degree with
external zero adjustment. Integrating meters shall comply with BS 5685.
"""
    
    # Create LLM processor
    llm = LLMProcessor()
    
    # Test 1: Simple extraction prompt
    print("\n🔍 Test 1: Simple Extraction")
    simple_prompt = f"""
You are testing requirements extraction. 

From the following text, extract ANY technical requirements, measurements, or specifications you can find.

Return ONLY valid JSON in this exact format:
{{
  "clause": "name or section found",
  "features": ["requirement 1", "requirement 2"],
  "text": "original text snippet"
}}

If you find nothing technical, return:
{{
  "clause": "No technical content",
  "features": [],
  "text": "No technical requirements found"
}}

Text to analyze:
{test_content}
"""
    
    try:
        result1 = await llm.process_prompt(simple_prompt, timeout=60)
        print(f"✅ LLM Response: {result1['raw_response']}")
        print(f"📊 Parsed Result: {result1['parsed_result']}")
        print(f"🎯 Success: {result1['success']}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Feature condensation
    print("\n🔍 Test 2: Feature Condensation")
    condensation_prompt = """
Test condensing these sample features:
- "True RMS current per phase & neutral ±0.5%"
- "Operating voltage 400V/230V, 50Hz"
- "Built-in memory >= 36 months"

Return ONLY valid JSON mapping original to condensed:
{
  "True RMS current per phase & neutral ±0.5%": "RMS current ±0.5%",
  "Operating voltage 400V/230V, 50Hz": "voltage 400V/230V 50Hz",
  "Built-in memory >= 36 months": "memory >=36 months"
}
"""
    
    try:
        result2 = await llm.process_prompt(condensation_prompt, timeout=60)
        print(f"✅ LLM Response: {result2['raw_response']}")
        print(f"📊 Parsed Result: {result2['parsed_result']}")
        print(f"🎯 Success: {result2['success']}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Generic prompt (should work)
    print("\n🔍 Test 3: Generic Prompt")
    generic_prompt = "What is 2 + 2? Answer with just the number."
    
    try:
        result3 = await llm.process_prompt(generic_prompt, timeout=30)
        print(f"✅ LLM Response: {result3['raw_response']}")
        print(f"📊 Parsed Result: {result3['parsed_result']}")
        print(f"🎯 Success: {result3['success']}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_qwen_extraction())
