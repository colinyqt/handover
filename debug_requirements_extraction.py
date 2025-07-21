import json
import re

# Path to your analysis file
analysis_file = r"c:\Users\cyqt2\Database\overhaul\outputs\_meter_clauses_20250710_064928.txt"

with open(analysis_file, 'r', encoding='utf-8') as f:
    content = f.read()

print("\n=== FILE PREVIEW (first 1000 chars) ===\n")
print(content[:1000])

# Try to extract requirements as a list of clause objects or bullet points
requirements = None

# Try to find a JSON block with 'requirements' (simulate LLM output)
json_blocks = re.findall(r'\{(?:[^{}]|\{[^{}]*\})*\}', content, re.DOTALL)
for block in json_blocks:
    try:
        parsed = json.loads(block)
        if 'requirements' in parsed and isinstance(parsed['requirements'], list):
            requirements = parsed['requirements']
            print("[DEBUG] Found requirements in JSON block.")
            break
    except Exception:
        continue

# Fallback: extract bullet points from '**Key Specifications Identified:**' sections
if not requirements:
    print("[DEBUG] Trying fallback extraction from Key Specifications sections...")
    requirements = []
    for match in re.finditer(r'\*\*Key Specifications Identified:\*\*([\s\S]+?)(?:\n\n|END OF EXTRACTION|$)', content):
        section = match.group(1)
        bullets = re.findall(r'- ([^\n]*)', section)
        requirements.extend([b.strip() for b in bullets if b.strip()])

print(f"\n[DEBUG] Extracted requirements (count={len(requirements)}):\n")
for req in requirements:
    print(f"- {req}")

if not requirements:
    print("[ERROR] No requirements extracted!")
else:
    print("\n[OK] Requirements extraction logic is working.")
