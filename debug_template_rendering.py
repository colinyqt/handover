#!/usr/bin/env python3
"""
Debug prompt template rendering in YAML pipeline
"""

import asyncio
import yaml
from pathlib import Path
import sys
sys.path.append("c:/Users/cyqt2/Database/overhaul/core")

from prompt_engine import PromptEngine
from llm_processor import LLMProcessor

async def debug_prompt_rendering():
    """Debug why prompts aren't rendering correctly in the YAML pipeline"""
    print("🧪 DEBUGGING PROMPT TEMPLATE RENDERING")
    print("=" * 50)
    
    # Load debug pipeline
    debug_yaml_path = Path("c:/Users/cyqt2/Database/overhaul/debug_oneshot.yaml")
    
    if not debug_yaml_path.exists():
        print(f"❌ Debug YAML not found: {debug_yaml_path}")
        return
    
    with open(debug_yaml_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Find the first LLM step
    llm_step = None
    for step in config.get('steps', []):
        if step.get('type') == 'llm':
            llm_step = step
            break
    
    if not llm_step:
        print("❌ No LLM step found in debug pipeline")
        return
    
    print(f"🔍 Found LLM step: {llm_step['name']}")
    print(f"📝 Prompt template: {llm_step.get('prompt_template', 'MISSING')}")
    
    # Create test context similar to what the pipeline would have
    test_context = {
        'inputs': {
            'document_file': 'test.pdf',
            'analysis_file': {
                'content': '''
                TECHNICAL SPECIFICATION – ELECTRICAL SERVICES
                1.20 METERS AND INSTRUMENTS
                Meters shall be of accuracy Class 0.5. Operating voltage 400V/230V, 50Hz.
                Built-in memory >= 36 months. True RMS current per phase ±0.5%.
                '''
            }
        },
        'step_results': {},
        'document_content': '''
        TECHNICAL SPECIFICATION – ELECTRICAL SERVICES
        1.20 METERS AND INSTRUMENTS
        The contestable customer meter scheme shall be implemented.
        Meters, instruments and relays for external panel mounting shall be of flush pattern.
        Indicating instruments shall comply with IEC 60051, IEC 61010, IEC 60529.
        They shall be of accuracy Class 0.5. Scale shall be of length 90 degree.
        Operating voltage 400V/230V, 50Hz. Built-in memory >= 36 months.
        True RMS current per phase & neutral ±0.5%.
        '''
    }
    
    # Test Jinja2 template rendering
    from jinja2 import Environment, BaseLoader
    jinja_env = Environment(loader=BaseLoader())
    
    prompt_template = llm_step.get('prompt_template', '')
    
    print("\n🎯 TESTING TEMPLATE RENDERING")
    print(f"Template: {repr(prompt_template[:200])}...")
    
    try:
        template = jinja_env.from_string(prompt_template)
        rendered_prompt = template.render(**test_context)
        print(f"✅ Rendered prompt (first 500 chars): {repr(rendered_prompt[:500])}")
        
        if not rendered_prompt.strip():
            print("❌ PROBLEM: Rendered prompt is empty!")
        elif rendered_prompt == prompt_template:
            print("❌ PROBLEM: Template didn't render any variables!")
        else:
            print("✅ Template rendered successfully")
            
            # Test with LLM processor
            print("\n🤖 TESTING WITH LLM PROCESSOR")
            llm = LLMProcessor()
            result = await llm.process_prompt(rendered_prompt, timeout=60)
            print(f"✅ LLM result: {result['success']}")
            print(f"📄 Response: {result['raw_response'][:200]}...")
            
    except Exception as e:
        print(f"❌ Template rendering error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_prompt_rendering())
