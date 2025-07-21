import os
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer

# Try local model path first, then remote
local_model_path = os.path.abspath('./jina_reranker').replace('\\', '/')

print(f"Trying to load local reranker from: {local_model_path}")
model = None
tokenizer = None
reranker = None
try:
    model = AutoModelForSequenceClassification.from_pretrained(local_model_path, trust_remote_code=True)
    tokenizer = AutoTokenizer.from_pretrained(local_model_path, trust_remote_code=True)
    reranker = pipeline("text-classification", model=model, tokenizer=tokenizer, trust_remote_code=True)
    print(f"✅ Loaded local reranker from {local_model_path}")
except Exception as e:
    print(f"[WARN] Local reranker load failed: {e}. Trying remote HuggingFace hub...")
    try:
        model = AutoModelForSequenceClassification.from_pretrained('jinaai/jina-reranker-v2-base-multilingual', trust_remote_code=True)
        tokenizer = AutoTokenizer.from_pretrained('jinaai/jina-reranker-v2-base-multilingual', trust_remote_code=True)
        reranker = pipeline("text-classification", model=model, tokenizer=tokenizer, trust_remote_code=True)
        print(f"✅ Loaded remote jinaai/jina-reranker-v2-base-multilingual from HuggingFace hub")
    except Exception as e2:
        print(f"❌ Remote reranker load failed: {e2}")
        exit(1)

# Example test data
requirement = "Accuracy class 0.5 or better"
candidates = [
    "Accuracy class 0.2S, supports advanced metering.",
    "Accuracy class 1.0, basic metering only.",
    "Accuracy class 0.5, supports all required features.",
    "No accuracy class specified."
]

rerank_inputs = [{"text": requirement, "text_target": c} for c in candidates]
outputs = reranker(rerank_inputs)

print("\nReranker results:")
for cand, out in zip(candidates, outputs):
    print(f"Candidate: {cand}\n  Score: {out['score']:.4f}  Label: {out['label']}")
