from sentence_transformers import CrossEncoder

# Download and cache the model locally if not already present
model_name = 'cross-encoder/ms-marco-MiniLM-L-6-v2'
reranker = CrossEncoder(model_name)

requirement = "Accuracy class 0.5 or better"
candidates = [
    "Accuracy class 0.2S, supports advanced metering.",
    "Accuracy class 1.0, basic metering only.",
    "Accuracy class 0.5, supports all required features.",
    "No accuracy class specified."
]

# Prepare pairs for reranking
pairs = [(requirement, c) for c in candidates]
scores = reranker.predict(pairs)

print("\nCross-Encoder Reranker results:")
for cand, score in sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True):
    print(f"Candidate: {cand}\n  Score: {score:.4f}")
