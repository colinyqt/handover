# core/prompt_engine.py
import os
import yaml
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from jinja2 import Environment, BaseLoader, Template
from dotenv import load_dotenv

from .database_autodiscovery import DatabaseAutoDiscovery, SmartDatabaseWrapper
from .function_registry import DatabaseFunctionRegistry  
from .template_analyzer import TemplateAnalyzer
from .file_processor import FileProcessor
from .llm_processor import LLMProcessor
from .excel_generator import ExcelGenerator

# Load environment variables from .env file
load_dotenv()

class PromptEngine:
    def discover_faiss_indexes(self, index_dir=None):
        """Return a list of FAISS index and metadata file pairs in the given directory."""
        import os
        if index_dir is None:
            index_dir = os.path.join(os.path.dirname(__file__), '..', 'faiss_indexes')
        index_dir = os.path.abspath(index_dir)
        index_files = []
        for fname in os.listdir(index_dir):
            if fname.endswith('.idx'):
                base = fname[:-4]
                meta = os.path.join(index_dir, base + '.pkl')
                idx = os.path.join(index_dir, fname)
                if os.path.exists(meta):
                    index_files.append((idx, meta))
        return index_files

    def load_faiss_index(self, index_path, meta_path):
        import faiss
        import pickle
        index = faiss.read_index(index_path)
        with open(meta_path, 'rb') as f:
            meta = pickle.load(f)
        return index, meta

    def query_all_faiss_indexes(self, query_text, index_dir=None, embedding_model_path=None, top_k=3):
        from sentence_transformers import SentenceTransformer
        import numpy as np
        if embedding_model_path is None:
            embedding_model_path = r"C:/Users/cyqt2/Database/overhaul/jina_reranker/minilm-embedding"
        model = SentenceTransformer(embedding_model_path)
        query_emb = model.encode([query_text], convert_to_numpy=True)
        results = []
        for idx_path, meta_path in self.discover_faiss_indexes(index_dir):
            index, meta = self.load_faiss_index(idx_path, meta_path)
            D, I = index.search(query_emb, top_k)
            for idx in I[0]:
                if idx < len(meta['metadatas']):
                    results.append({
                        'index': idx_path,
                        'metadata': meta['metadatas'][idx],
                        'document': meta['documents'][idx]
                    })
        return results
    def strip_code_fences(self, raw):
        """Remove code fences and Markdown from LLM output."""
        if not isinstance(raw, str):
            return raw
        import re
        # Remove code fences at the start and end, with or without language hints
        cleaned = re.sub(r'^```[a-zA-Z0-9]*\s*\n', '', raw.strip())
        cleaned = re.sub(r'```\s*$', '', cleaned)
        return cleaned.strip()
    def flatten_clause_requirements(self, clauses: list) -> list:
        """
        Given a list of clause texts, extract bullet points or feature-level requirements.
        """
        import re
        atomic_reqs = []
        for clause in clauses:
            # Extract bullet points (• or -) or numbered/lettered lists
            bullets = re.findall(r'(?:•|-|\d+\)|[a-z]\))\s*([^\n]+)', clause)
            if bullets:
                atomic_reqs.extend([b.strip() for b in bullets if b.strip()])
            else:
                # Fallback: split into sentences
                sentences = re.split(r'(?<=[.!?])\s+', clause)
                atomic_reqs.extend([s.strip() for s in sentences if len(s.strip()) > 10])
        return atomic_reqs
    def extract_requirements_from_analysis(self, content: str, mode: str = "clauses") -> list:
        """
        Extract requirements from tender analysis text.
        mode: "clauses" for full clause texts, "bullets" for key specification bullets.
        Returns a list of strings.
        """
        requirements = []
        import re
        if mode == "clauses":
            # Extract all clause sections under '**Complete Clause Text:**'
            for match in re.finditer(
                r'\*\*Complete Clause Text:\*\*\n([\s\S]+?)(?=\n\*\*Key Specifications Identified:|\n### |\nEND OF EXTRACTION|$)',
                content
            ):
                clause_text = match.group(1).strip()
                if clause_text:
                    requirements.append(clause_text)
        elif mode == "bullets":
            # Extract all bullet points under '**Key Specifications Identified:**'
            for match in re.finditer(
                r'\*\*Key Specifications Identified:\*\*([\s\S]+?)(?:\n\n|END OF EXTRACTION|$)',
                content
            ):
                section = match.group(1)
                bullets = re.findall(r'- ([^\n]*)', section)
                requirements.extend([b.strip() for b in bullets if b.strip()])
        return requirements
    """Main YAML prompt engine with auto-discovery database integration"""
    
    def __init__(self, 
                 databases_dir: str = "databases", 
                 prompts_dir: str = "prompts",
                 outputs_dir: str = "outputs"):
        self.databases_dir = Path(databases_dir)
        self.prompts_dir = Path(prompts_dir)
        self.outputs_dir = Path(outputs_dir)
        
        # Ensure output directory exists
        self.outputs_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.discovery_engine = DatabaseAutoDiscovery()
        self.function_registry = DatabaseFunctionRegistry()
        self.template_analyzer = TemplateAnalyzer(self.function_registry)
        self.file_processor = FileProcessor()
        self.llm_processor = LLMProcessor()
        
        # Initialize database schemas storage
        self._database_schemas = {}
        
        # Jinja2 environment for template rendering
        self.jinja_env = Environment(loader=BaseLoader())
        
        # New: Initialize LlamaIndex query engines
        self.llamaindex_engines = {}
        
        print("Prompt engine components initialized")
    
    async def run_prompt(self, prompt_config_path: str, **kwargs) -> Dict[str, Any]:
        """Run a prompt configuration with inputs and return results"""
        self.llm_model = kwargs.get('llm_model')
        # Use local MiniLM embedding model for all embedding steps
        self.embedding_model = None  # Set dynamically if needed
        config = self._load_yaml_config(prompt_config_path)

        # Remove ChromaDB support: FAISS only

        try:
            # config already loaded above, do not reload
            validation = self.template_analyzer.validate_template(config)
            if not validation['valid']:
                return {'success': False, 'error': f"Configuration errors: {validation['errors']}"}

            inputs_config = config.get('inputs', [])
            input_data = await self._process_inputs(inputs_config, **kwargs)

            # Always use local MiniLM embedding model for all embedding steps
            self.embedding_model = r"C:/Users/cyqt2/Database/overhaul/jina_reranker/minilm-embedding"
            llm_model = input_data.get('llm_model') or getattr(self, 'llm_model', None)
            if llm_model:
                self.llm_processor = LLMProcessor(model=llm_model)
            # print(f"Using embedding model: {self.embedding_model}")

            databases = await self._load_databases_smart(config.get('databases', {}))

            context = {
                'inputs': input_data,
                'databases': databases,
                'database_schemas': {name: db.get_schema_info() for name, db in databases.items()},
                'step_results': {},
                'timestamp': datetime.utcnow().strftime('%Y%m%d_%H%M%S'),
                'config': config
            }

            pipeline_results = await self._execute_pipeline(
                config.get('processing_steps', []),
                context
            )
            context['step_results'] = pipeline_results


            # NEW: If extract_clauses step returns structured requirements, pass them to context for downstream steps
            if 'extract_clauses' in pipeline_results:
                extract_result = pipeline_results['extract_clauses']
                # print(f"[DEBUG] extract_clauses result type: {type(extract_result)}")
                # Try to get the analysis file content from context['inputs']
                analysis_file_content = None
                if 'inputs' in context and 'analysis_file' in context['inputs']:
                    # If file_processor returns a dict with 'content', use it
                    af = context['inputs']['analysis_file']
                    if isinstance(af, dict) and 'content' in af:
                        analysis_file_content = af['content']
                    elif isinstance(af, str):
                        analysis_file_content = af
                # Prefer clause-based extraction, fallback to bullets if no clauses found
                requirements = []
                if analysis_file_content:
                    requirements = self.extract_requirements_from_analysis(analysis_file_content, mode="clauses")
                    if not requirements:
                        # print("[DEBUG] No clauses found, falling back to bullet extraction.")
                        requirements = self.extract_requirements_from_analysis(analysis_file_content, mode="bullets")
                # If still nothing, try legacy extraction from extract_result
                if not requirements:
                    # If already parsed as dict
                    if isinstance(extract_result, dict):
                        if 'requirements' in extract_result and isinstance(extract_result['requirements'], list):
                            requirements = extract_result['requirements']
                        elif 'raw_response' in extract_result:
                            try:
                                parsed = json.loads(extract_result['raw_response'])
                                if 'requirements' in parsed and isinstance(parsed['requirements'], list):
                                    requirements = parsed['requirements']
                            except Exception:
                                requirements = []
                    elif isinstance(extract_result, str):
                        try:
                            parsed = json.loads(extract_result)
                            if 'requirements' in parsed and isinstance(parsed['requirements'], list):
                                requirements = parsed['requirements']
                        except Exception:
                            requirements = []
                # If requirements is a list of long clause texts, flatten to atomic requirements
                if isinstance(requirements, list) and requirements and all(isinstance(r, str) and len(r) > 100 for r in requirements):
                    # print("[DEBUG] Detected list of clause texts, flattening to atomic requirements for FAISS...")
                    atomic_reqs = self.flatten_clause_requirements(requirements)
                    # print(f"[DEBUG] Flattened to {len(atomic_reqs)} atomic requirements.")
                    requirements = atomic_reqs



                # --- ALWAYS FLATTEN: Convert requirements to a flat list of strings for Chroma ---
                def flatten_requirements(reqs):
                    flat = []
                    if isinstance(reqs, dict) and 'requirements' in reqs:
                        reqs = reqs['requirements']
                    if isinstance(reqs, list):
                        for r in reqs:
                            if isinstance(r, dict):
                                if 'clause' in r and r['clause']:
                                    flat.append(str(r['clause']))
                                if 'features' in r and isinstance(r['features'], list):
                                    flat.extend([str(f) for f in r['features'] if f and str(f).strip()])
                                if 'text' in r and r['text']:
                                    flat.append(str(r['text']))
                            elif isinstance(r, str):
                                flat.append(r)
                    elif isinstance(reqs, str):
                        flat = [reqs]
                    return [s.strip() for s in flat if s and s.strip()]

                requirements = flatten_requirements(requirements)
                # print(f"[DEBUG] requirements after flattening: {type(requirements)}, {len(requirements) if isinstance(requirements, list) else 'N/A'} items")

                # --- FILTERING: Remove empty, short, or fragment requirements before passing to Chroma ---
                if isinstance(requirements, list):
                    filtered_requirements = []
                    for req in requirements:
                        if not isinstance(req, str):
                            continue
                        req_clean = req.strip()
                        # Remove empty, too short, or fragment-like requirements
                        if not req_clean:
                            continue
                        if len(req_clean) < 8:
                            continue
                        # Remove fragments (e.g., single words, or ending with a comma, or not a full sentence)
                        if req_clean.endswith((',', ';', ':')):
                            continue
                        if len(req_clean.split()) < 2:
                            continue
                        filtered_requirements.append(req_clean)
                    # print(f"[DEBUG] Filtered requirements: {len(filtered_requirements)} out of {len(requirements)}")
                    requirements = filtered_requirements

                # print(f"[DEBUG] requirements type: {type(requirements)}, length: {len(requirements) if isinstance(requirements, list) else 'N/A'}")
                # if isinstance(requirements, list):
                #     if len(requirements) == 0:
                #         print("[WARN] requirements list is empty!")
                #     elif len(requirements) < 5:
                #         print(f"[DEBUG] requirements (full): {requirements}")
                #     else:
                #         print(f"[DEBUG] requirements (preview): {requirements[:3]} ... (total {len(requirements)})")
                # else:
                #     print(f"[WARN] requirements is not a list: {requirements}")
                if requirements:
                    context['requirements'] = requirements
                    # print(f"[DEBUG] Requirements for FAISS step (first 1000 chars): {json.dumps(requirements, indent=2)[:1000]}")
                # else:
                #     print('[ERROR] No requirements extracted for FAISS step. FAISS search will fail.')

            # NEW: Pass reranked candidate meters to context for compliance report step
            if 'rerank_semantic_results' in pipeline_results:
                rerank_result = pipeline_results['rerank_semantic_results']
                if isinstance(rerank_result, dict) and 'results' in rerank_result:
                    context['reranked_candidates'] = rerank_result['results']

            output_files = await self._generate_outputs(
                config.get('outputs', []),
                context
            )

            return {
                'success': True,
                'pipeline_results': pipeline_results,
                'output_files': output_files
            }
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}

    
    def _load_yaml_config(self, prompt_file: str) -> Dict[str, Any]:
        """Load and parse YAML configuration"""
        
        prompt_path = Path(prompt_file)
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
        
        with open(prompt_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if not config:
            raise ValueError("Empty or invalid YAML configuration")
        
        print(f"Loaded configuration: {config.get('name', 'Unnamed')}")
        return config
    
    async def _process_inputs(self, inputs_config: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """Process input files and parameters (extended types and validation)"""
        input_data = {}
        for input_spec in inputs_config:
            input_name = input_spec['name']
            input_type = input_spec['type']
            required = input_spec.get('required', False)
            desc = input_spec.get('description', '')
            default = input_spec.get('default', None)
            value = None
            if input_type == 'file':
                # Use the file path from kwargs, matching the input name
                file_path = kwargs.get(input_name)
                if not file_path:
                    # Only prompt if not provided (should never happen in Streamlit)
                    file_path = input(f"Enter path for {input_name} ({desc}): ")
                if not file_path and required:
                    raise ValueError(f"Required input '{input_name}' not provided")
                if file_path and Path(file_path).exists():
                    file_data = self.file_processor.process_file(file_path)
                    # Always pass as dict with 'path' key for pipeline compatibility
                    file_data['path'] = str(file_path)
                    input_data[input_name] = file_data
                    print(f"Processed {input_name}: {len(file_data['content'])} characters")
                elif required:
                    raise FileNotFoundError(f"Input file not found: {file_path}")
            elif input_type == 'text':
                value = kwargs.get(input_name, default)
                if value is None:
                    value = input(f"📝 Enter {input_name} (default: {default}): ").strip() or default
                input_data[input_name] = value
            elif input_type == 'option':
                options = input_spec.get('options', [])
                value = kwargs.get(input_name, default)
                if value is None:
                    print(f"Select {input_name}:")
                    for i, option in enumerate(options, 1):
                        print(f"  {i}. {option}")
                    choice = input(f"Enter choice (1-{len(options)}, default: {default}): ").strip()
                    if choice and choice.isdigit():
                        choice_idx = int(choice) - 1
                        if 0 <= choice_idx < len(options):
                            value = options[choice_idx]
                        else:
                            value = default
                    else:
                        value = default
                input_data[input_name] = value
            elif input_type == 'number':
                value = kwargs.get(input_name, default)
                if value is None:
                    value = input(f"🔢 Enter {input_name} (default: {default}): ").strip()
                try:
                    if value:
                        input_data[input_name] = float(value)
                    elif default is not None:
                        input_data[input_name] = float(default)
                    else:
                        input_data[input_name] = 0.0
                except (ValueError, TypeError):
                    input_data[input_name] = float(default) if default is not None else 0.0
            elif input_type == 'boolean':
                value = kwargs.get(input_name, default)
                if value is None:
                    value = input(f"[y/n] {input_name} (default: {default}): ").strip().lower()
                if isinstance(value, str):
                    if value in ['y', 'yes', 'true', '1']:
                        input_data[input_name] = True
                    elif value in ['n', 'no', 'false', '0']:
                        input_data[input_name] = False
                    else:
                        input_data[input_name] = bool(default)
                else:
                    input_data[input_name] = bool(value)
            # Extend here for more types (date, list, etc.)
        return input_data
    
    async def _load_databases_smart(self, database_config: Dict[str, str]) -> Dict[str, SmartDatabaseWrapper]:
        """Load databases with auto-discovery and autodetect FAISS indexes."""
        import os
        smart_databases = {}
        # Load any explicit databases as before
        for db_name, db_path in database_config.items():
            if not Path(db_path).exists():
                print(f"Database not found: {db_path}, skipping {db_name}")
                continue
            wrapper = SmartDatabaseWrapper(db_path, self.discovery_engine)
            smart_databases[db_name] = wrapper
            self.function_registry.register_database(db_name, wrapper)
            available_functions = len(self.function_registry.get_available_functions(db_name))
            print(f"{db_name}: {available_functions} functions auto-discovered")
        # Autodetect FAISS indexes in faiss_indexes/
        faiss_index_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'faiss_indexes'))
        if os.path.exists(faiss_index_dir):
            autodetected = self.discover_faiss_indexes(faiss_index_dir)
            if autodetected:
                print(f"Autodetected {len(autodetected)} FAISS index(es) in {faiss_index_dir}")
                smart_databases['faiss_indexes'] = autodetected
        self._last_loaded_databases = smart_databases
        return smart_databases
    
    async def _execute_pipeline(self, steps: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the processing pipeline with unified context passing, including reranker support"""
        results = {}
        llm_model = getattr(self, 'llm_model', None)
        embedding_model = getattr(self, 'embedding_model', None)

        for step in steps:
            # Reduced debug output for clarity
            step_name = step['name']
            step_type = step.get('type', '')
            prompt_template = step.get('prompt_template', '')
            dependencies = step.get('dependencies', [])
            timeout = step.get('timeout', 120)
            if llm_model:
                step['llm_model'] = llm_model
            if embedding_model:
                step['embedding_model'] = embedding_model

            for dep in dependencies:
                if dep in results:
                    context[f"dep_{dep}"] = results[dep]

            step_context = context.copy()
            step_context['step_results'] = results.copy()
            for dep in dependencies:
                if dep in results:
                    step_context[f"dep_{dep}"] = results[dep]

            # For LLM steps, inject drawing_image_path from context if present and attach image for vision models
            image_bytes = None
            if step_type == "llm":
                if 'drawing_image_path' in context:
                    step_context['drawing_image_path'] = context['drawing_image_path']
                    llm_model_val = step.get('llm_model') or step_context.get('llm_model', '')
                    image_path = context['drawing_image_path']
                    if llm_model_val and 'moondream' in llm_model_val.lower() and image_path and Path(image_path).exists():
                        try:
                            with open(image_path, 'rb') as f:
                                image_bytes = f.read()
                        except Exception as e:
                            print(f"[ERROR] Could not read image for vision model: {e}")
            # Remove ChromaDB semantic search step: FAISS only

            # Force breakdown=True for any LLM step named 'llm_breakdown_features'
            if step_name == "llm_breakdown_features":
                print(f"[DEBUG] Forcing breakdown=True for step: {step_name}")
                # Patch: Flatten all features from all clauses for LLM breakdown
                features = []
                # Try to get clauses from dependencies (load_clauses step)
                dep_clauses = None
                if 'dep_load_clauses' in step_context and 'clauses' in step_context['dep_load_clauses']:
                    dep_clauses = step_context['dep_load_clauses']['clauses']
                elif 'clauses' in step_context:
                    dep_clauses = step_context['clauses']
                if dep_clauses and isinstance(dep_clauses, list):
                    for clause in dep_clauses:
                        if isinstance(clause, dict) and 'features' in clause and isinstance(clause['features'], list):
                            features.extend([f for f in clause['features'] if isinstance(f, str) and f.strip()])
                # Fallback: try requirements
                elif 'requirements' in step_context and isinstance(step_context['requirements'], list):
                    features = [f for f in step_context['requirements'] if isinstance(f, str) and f.strip()]
                print(f"[DEBUG] Features to send to LLM: {features[:3]} ... (total {len(features)})")
                atomic_map = {}
                for feature in features:
                    try:
                        # Directly send the feature string to the LLM for breakdown
                        print(f"[LLM TEST] Sending feature string to LLM: {feature!r}")
                        step_result = await self.llm_processor.process_prompt(feature, timeout, breakdown=True)
                        atomic_value = ""
                        if step_result and isinstance(step_result, dict):
                            parsed = step_result.get('parsed_result')
                            if parsed and isinstance(parsed, dict):
                                atomic_value = parsed.get('atomic_requirement', "")
                                if not (isinstance(atomic_value, str) and atomic_value.strip()):
                                    atomic_value = ""
                        atomic_map[feature] = atomic_value
                    except Exception as e:
                        print(f"[LLM TEST] Exception during LLM call for feature {feature!r}: {e}")
                        atomic_map[feature] = ""
                print(f"[DEBUG] LLM breakdown mapping: {atomic_map}")
                results[step_name] = atomic_map

                # PATCH: After LLM breakdown, set requirements to list of atomic requirement strings for downstream steps
                atomic_requirements = [v for v in atomic_map.values() if isinstance(v, str) and v.strip()]
                context['requirements'] = atomic_requirements
                print(f"[DEBUG] Patched requirements for downstream steps: {atomic_requirements}")
                continue

            # Native Python code execution step
            if step_type in ("python", "run"):
                print(f"[DEBUG] _execute_pipeline: calling process_step for python step: {step_name}")
                # Use a mutable dict for local_vars to capture context changes
                local_vars = step_context.copy()
                step_result = await self.process_step(step, local_vars)
                # Merge any new keys from local_vars back into main context
                for k, v in local_vars.items():
                    if k not in context or context[k] != v:
                        context[k] = v
                results[step_name] = step_result
                continue

            # Reranker step using cross-encoder
            if step_type == "reranker":
                try:
                    from sentence_transformers import CrossEncoder
                    # Use local model path for offline support
                    local_model_path = os.path.abspath('./jina_reranker/cross-encoder').replace('\\', '/')
                    if os.path.exists(local_model_path):
                        model_name = local_model_path
                        print(f"Executing reranker step: {step_name} using local CrossEncoder model at {model_name}")
                    else:
                        model_name = 'cross-encoder/ms-marco-MiniLM-L-6-v2'
                        print(f"[WARN] Local CrossEncoder model not found, falling back to HuggingFace: {model_name}")
                    reranker = CrossEncoder(model_name)
                    faiss_results = results[step['dependencies'][0]]
                    print(f"[DEBUG] FAISS results for reranker: {faiss_results}")
                    # PATCH: If faiss_results is a list, skip reranking and pass through
                    if isinstance(faiss_results, list):
                        print("[PATCH] FAISS results is a list, skipping reranking and passing through.")
                        step_result = {'success': True, 'results': faiss_results}
                        results[step_name] = step_result
                        continue
                    # If faiss_results is a dict with 'results', rerank as before
                    reranked_results = {}
                    for req, candidates in faiss_results.get('results', {}).items():
                        if not candidates:
                            reranked_results[req] = []
                            continue
                        pairs = [(req, c.get('text', '[NO TEXT]')) for c in candidates]
                        try:
                            scores = reranker.predict(pairs)
                        except Exception as rerank_e:
                            print(f"[ERROR] CrossEncoder reranker failed: {rerank_e}")
                            reranked_results[req] = []
                            continue
                        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:3]
                        top_candidates = [candidates[i] for i in top_indices]
                        reranked_results[req] = top_candidates
                        print(f"CrossEncoder reranked {len(candidates)} candidates for '{req}' -> {top_indices}")
                    step_result = {'success': True, 'results': reranked_results}
                except Exception as e:
                    print(f"Reranker step failed: {e}")
                    step_result = {'success': False, 'error': str(e)}
                results[step_name] = step_result
                continue

            # LlamaIndex step
            if step_name.startswith("llamaindex_"):
                template = self.jinja_env.from_string(prompt_template)
                rendered_prompt = template.render(**step_context)
                try:
                    db_config = context.get('databases', {})
                    if db_config:
                        db_name, db_wrapper = next(iter(db_config.items()))
                        if hasattr(db_wrapper, 'db_path'):
                            db_path = db_wrapper.db_path
                        elif hasattr(db_wrapper, 'database_path'):
                            db_path = db_wrapper.database_path
                        elif hasattr(db_wrapper, 'path'):
                            db_path = db_wrapper.path
                        else:
                            db_path = getattr(db_wrapper, '_db_path', None)
                            if not db_path:
                                if isinstance(db_wrapper, str):
                                    db_path = db_wrapper
                                else:
                                    raise ValueError(f"Could not extract database path from {type(db_wrapper)}")
                        llamaindex_engine = self.get_llamaindex_engine(db_path)
                        llamaindex_result = await llamaindex_engine.query(rendered_prompt)
                        step_result = {
                            'llamaindex_result': llamaindex_result,
                            'raw_response': llamaindex_result,
                            'success': True
                        }
                    else:
                        step_result = {
                            'error': 'No database configured for LlamaIndex',
                            'success': False
                        }
                except Exception as e:
                    step_result = {
                        'error': str(e),
                        'success': False
                    }
                results[step_name] = step_result
                continue

            # PATCH: foreach support for LLM steps
            if step_type == "llm" and 'foreach' in step and step['foreach']:
                print("[PATCH ACTIVE] Foreach logic for LLM step triggered.")
                foreach_expr = step['foreach']
                # Try to resolve context['...'] expressions manually
                foreach_items = None
                if isinstance(foreach_expr, str) and foreach_expr.startswith('context['):
                    import re
                    m = re.match(r"context\['([^']+)'\](?:\['([^']+)'\])?", foreach_expr)
                    foreach_items = None
                    if m:
                        key1 = m.group(1)
                        key2 = m.group(2)
                        val = None
                        # Direct, explicit resolution order
                        if key1 in step_context:
                            val = step_context[key1]
                        elif key1 in context:
                            val = context[key1]
                        elif 'inputs' in context and key1 in context['inputs']:
                            val = context['inputs'][key1]
                        elif key1 in results:
                            val = results[key1]
                        else:
                            raise KeyError(f"foreach: Could not resolve key '{key1}' in step_context, context, inputs, or results.")
                        print(f"[DEBUG] foreach key1: {key1}, resolved value type: {type(val)}")
                        if key2 and isinstance(val, dict):
                            foreach_items = val.get(key2)
                        else:
                            foreach_items = val
                    else:
                        foreach_items = eval(foreach_expr, {}, context)
                elif isinstance(foreach_expr, str):
                    foreach_items = eval(foreach_expr, {}, context)
                else:
                    foreach_items = foreach_expr
                if not isinstance(foreach_items, list):
                    print(f"[ERROR] foreach items is not a list: {type(foreach_items)}. Value: {repr(foreach_items)[:200]}")
                    foreach_items = []
                results_list = []
                for idx, item in enumerate(foreach_items):
                    # PATCH: Ensure passthrough logic matches test_prompt_engine_foreach.py
                    item_context = step_context.copy()
                    item_context['item'] = item
                    # If item is a dict, also inject its keys for template access
                    if isinstance(item, dict):
                        item_context.update(item)
                    print(f"[DEBUG] foreach item {idx}: type={type(item)}, value={repr(item)[:200]}")
                    prompt_template = step.get('input', '')
                    template = self.jinja_env.from_string(prompt_template)
                    rendered_prompt = template.render(**item_context)
                    print(f"[DEBUG] LLM foreach prompt for item {idx}: {repr(rendered_prompt)[:200]}")
                    if image_bytes:
                        step_result = await self.llm_processor.process_prompt(rendered_prompt, timeout, images=[image_bytes])
                    else:
                        step_result = await self.llm_processor.process_prompt(rendered_prompt, timeout)
                    print(f"[DEBUG] LLM response for chunk {idx}: {repr(step_result)[:200]}")
                    results_list.append(step_result)
                results[step_name] = results_list
                continue

            # Default: LLM step
            print(f"[DEBUG] _execute_pipeline: defaulting to LLM step for {step_name}")
            template = self.jinja_env.from_string(prompt_template)
            rendered_prompt = template.render(**step_context)
            # If image_bytes is set, pass it to the LLM processor
            if image_bytes:
                step_result = await self.llm_processor.process_prompt(rendered_prompt, timeout, images=[image_bytes])
            else:
                step_result = await self.llm_processor.process_prompt(rendered_prompt, timeout)
            results[step_name] = step_result

        return results
    
    async def _generate_outputs(self, outputs_config: List[Dict[str, Any]], context: Dict[str, Any]) -> List[str]:
        """Generate output files using unified context"""
        output_files = []

        for output_spec in outputs_config:
            output_type = output_spec['type']
            filename_template = output_spec['filename']

            # Check condition if specified
            condition = output_spec.get('condition')
            if condition:
                try:
                    template = self.jinja_env.from_string(f"{{{{ {condition} }}}}")
                    should_generate = template.render(**context).strip().lower() in ['true', '1', 'yes']
                    if not should_generate:
                        continue
                except:
                    print(f"Could not evaluate condition: {condition}")
                    continue

            # Render filename
            filename_tmpl = self.jinja_env.from_string(filename_template)
            filename = filename_tmpl.render(**context)
            output_path = self.outputs_dir / filename

            # Generate content based on type
            if output_type == 'json':
                data = output_spec.get('data', context['step_results'])
                if isinstance(data, str):
                    data_template = self.jinja_env.from_string(data)
                    data = data_template.render(**context)
                    # Strip code fences if present
                    data = self.strip_code_fences(data)
                    try:
                        data = json.loads(data)
                    except:
                        pass
                elif isinstance(data, dict):
                    data = self._render_template_dict(data, context)
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, default=str)

            elif output_type == 'excel':
                # Excel generation code here
                # Placeholder: Write an empty Excel file or log a message
                excel_generator = ExcelGenerator()
                try:
                    excel_generator.generate_empty_excel(str(output_path))
                    print(f"Excel file generated: {output_path}")
                except Exception as e:
                    print(f"Excel generation error: {e}")

            elif output_type == 'custom_excel':
                # Handle custom Excel generation with direct LLM processing
                llm_step = output_spec.get('llm_step')
                if llm_step and llm_step in context['step_results']:
                    llm_result = context['step_results'][llm_step]
                    raw_response = llm_result.get('raw_response', '')
                    # Strip code fences if present
                    raw_response = self.strip_code_fences(raw_response)
                    # Try to extract JSON from raw response
                    excel_data = self._extract_and_fix_json_from_raw_response(raw_response)
                    # Generate Excel file
                    if excel_data is not None:
                        excel_generator = ExcelGenerator()
                        try:
                            if excel_generator.generate_compliance_report(str(output_path), excel_data):
                                print(f"Custom Excel file generated: {output_path}")
                            else:
                                print(f"Failed to generate Excel file: {output_path}")
                        except Exception as e:
                            print(f"Excel generation error: {e}")
                    else:
                        print(f"Could not extract valid JSON from LLM response - check raw output file")
                else:
                    print(f"LLM step '{llm_step}' not found in pipeline results")

            elif output_type == 'markdown':
                template_file = output_spec.get('template')
                if template_file and Path(template_file).exists():
                    with open(template_file, 'r', encoding='utf-8') as f:
                        template_content = f.read()
                else:
                    template_content = output_spec.get('content', '# Results\n\n{{ step_results | tojson(indent=2) }}')

                template = self.jinja_env.from_string(template_content)
                content = template.render(**context)

                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)

            elif output_type == 'text':
                content_template = output_spec.get('content', '{{ step_results }}')
                template = self.jinja_env.from_string(content_template)
                content = template.render(**context)
                # Strip code fences if present
                content = self.strip_code_fences(content)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)

            output_files.append(str(output_path))
            # print(f"📄 Generated: {output_path}")
        return output_files
    
    def _render_template_dict(self, data: Any, context: Dict[str, Any]) -> Any:
        """Recursively render template strings in a dictionary"""
        
        if isinstance(data, dict):
            return {k: self._render_template_dict(v, context) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._render_template_dict(item, context) for item in data]
        elif isinstance(data, str) and '{{' in data:
            try:
                template = self.jinja_env.from_string(data)
                return template.render(**context)
            except:
                return data
        else:
            return data

    async def process_step(self, step, context):
        step_type = step.get('type', '')
        # Native Python code execution step
        if step_type in ("python", "run"):
            code = step.get('code') or step.get('run')
            if not code:
                raise ValueError("No code provided for python/run step")
            # Prepare local context for exec (use actual context, not a copy)
            local_vars = {'context': context}
            try:
                exec(code, {}, local_vars)
                # If 'result' is set in local_vars, return it; else return all locals except context
                if 'result' in local_vars:
                    return local_vars['result']
                # Remove 'context' from output if present
                output = {k: v for k, v in local_vars.items() if k != 'context'}
                return output if output else None
            except Exception as e:
                import traceback
                traceback.print_exc()
                return {'success': False, 'error': str(e)}
        if step_type == "chroma":
            if not self.chroma_processor:
                raise RuntimeError("ChromaProcessor not initialized")
            return await self.chroma_processor.process_chroma_step(step, context)
        # Add more custom step types as needed
        raise NotImplementedError(f"Step type '{step_type}' not implemented in process_step")

