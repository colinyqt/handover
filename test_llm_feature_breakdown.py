import asyncio
from core.llm_processor import LLMProcessor

async def test_llm_feature_breakdown():
    features = [
        "True RMS Volts: all phase-to-phase & phase-to-neutral ±0.5%",
        "Real Power (kW): per phase & three phase total ±0.5%",
        "Frequency (Hz) ±0.5%"
    ]
    print(f"[DEBUG] Features list ({len(features)}): {features}")
    llm = LLMProcessor(model="qwen2.5-coder:7b-instruct")
    for idx, feature in enumerate(features):
        print(f"[DEBUG] Iteration {idx+1}/{len(features)}: Sending feature: {feature!r}")
        result = await llm.process_prompt(feature, timeout=30, breakdown=True)
        print(f"[TEST] LLM result for feature: {feature!r}\n{result}\n{'-'*40}")

if __name__ == "__main__":
    asyncio.run(test_llm_feature_breakdown())
