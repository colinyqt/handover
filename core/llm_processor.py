# core/llm_processor.py
import json
import re
import asyncio
from typing import Dict, Any, Optional

class LLMProcessor:
    """Handle LLM interactions using ollama"""
    
    def __init__(self, model: str = "qwen2.5-coder:7b-instruct"):
        self.model = model
    
    async def process_prompt(self, prompt: str, timeout: int = 120, breakdown: bool = False) -> Dict[str, Any]:
        """Process a prompt with the LLM and return structured result. If breakdown=True, condense to a single queriable requirement."""
        import os
        import datetime
        try:
            import ollama
        except ImportError:
            print("[LLM] Ollama not available, using mock response")
            return {
                'raw_response': f"Mock response for prompt: {prompt[:100]}...",
                'parsed_result': {"mock": True, "message": "Ollama not available"},
                'success': True
            }
        try:
            orig_feature = None
            if breakdown:
                feature_text = prompt.strip()
                orig_feature = feature_text
                print(f"[LLM DEBUG] Feature text for breakdown: {feature_text!r}")
                prompt = (
                    "You are an expert requirements engineer. "
                    "Condense the following feature or requirement into a single, short, queriable requirement. "
                    "The result should be a concise phrase (2-8 words) that best represents the core of the feature for database search. "
                    "If the feature includes any accuracy, measurement, or tolerance values (such as ±0.5%), include them in the phrase. "
                    "Output ONLY valid JSON in the format: {\"atomic_requirement\": \"...\"}. "
                    "If the input is already atomic, return it as is.\n"
                    "\nExample:\n"
                    "Feature:\nTrue RMS Volts: all phase-to-phase & phase-to-neutral ±0.5%\n"
                    "Output:\n{\"atomic_requirement\": \"RMS voltage measurement ±0.5%\"}\n"
                ) + f"\nFeature:\n{feature_text}"
            # [LLM DEBUG] Prompt print removed as requested
            client = ollama.Client()
            response = client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                options={
                    "temperature": 0.1,
                    "timeout": timeout,
                    "num_ctx": 32768,
                    "num_predict": 4096
                }
            )
            print(f"[LLM DEBUG] ollama.Client().chat response: {response}")
            ai_content = response['message']['content']
            ai_content_clean = ai_content.strip()
            if ai_content_clean.startswith("```"):
                lines = ai_content_clean.splitlines()
                if lines[0].startswith("```json"):
                    lines = lines[1:]
                elif lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip().startswith("```"):
                    lines = lines[:-1]
                ai_content_clean = "\n".join(lines).strip()
            json_result = self._extract_json_from_response(ai_content_clean)
            # No post-processing: trust the LLM to return a single short phrase
            if breakdown and json_result and isinstance(json_result, dict):
                atomic = json_result.get("atomic_requirement")
                if not (isinstance(atomic, str) and 2 <= len(atomic.split()) <= 8):
                    # If the LLM did not return a valid short phrase, set to empty string
                    json_result["atomic_requirement"] = ""
            # Debug file writing removed as requested
            return {
                'raw_response': ai_content,
                'parsed_result': json_result,
                'success': True
            }
        except Exception as e:
            print(f"[LLM] Error: {e}")
            return {
                'error': str(e),
                'success': False
            }
    
    def _extract_json_from_response(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from LLM response"""
        
        # Try to find JSON in the response
        json_pattern = re.compile(r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}', re.DOTALL)
        matches = json_pattern.findall(text)
        
        # Try each match, from longest to shortest
        if matches:
            matches.sort(key=len, reverse=True)
            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
        
        # If no JSON found, return the text as a message
        return {"message": text}