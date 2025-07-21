import json
import re

def clean_json_file(input_path, output_path=None):
    with open(input_path, 'r', encoding='utf-8') as f:
        raw = f.read()

    # Remove Markdown code block markers if present
    raw = re.sub(r"^```json\s*|```$", "", raw.strip(), flags=re.MULTILINE)

    # Remove trailing commas before closing brackets/braces
    raw = re.sub(r",\s*([\]}])", r"\1", raw)

    # Try to find the largest valid JSON prefix by trimming from the end, skipping whitespace
    raw_bytes = raw.encode('utf-8')
    for end in range(len(raw_bytes), 0, -1):
        candidate = raw_bytes[:end].decode('utf-8', errors='ignore').rstrip()
        try:
            data = json.loads(candidate)
            print("Recovered valid JSON prefix.")
            break
        except Exception:
            continue
    else:
        print("Could not recover any valid JSON.")
        return

    out_path = output_path if output_path else input_path
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Cleaned JSON written to {out_path}")

if __name__ == "__main__":
    input_path = input("Enter the path to the JSON file to clean: ").strip()
    clean_json_file(input_path)