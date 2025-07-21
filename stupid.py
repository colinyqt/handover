import json

# Path to your JSON file
json_path = r'c:\Users\cyqt2\Database\overhaul\outputs\_extracted_clauses_20250715_072223.json'

def main():
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    requirements = data.get('requirements', [])
    for req in requirements:
        clause = req.get('clause', 'No clause')
        features = req.get('features', [])
        print(f"Clause: {clause}")
        print("Features:")
        for feat in features:
            print(f"  - {feat}")
        print('-' * 40)

if __name__ == '__main__':
    main()