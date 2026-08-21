import os
import json
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from google import genai
from google.genai import types
from google.genai.errors import ClientError

class LLMProvider(ABC):
    """Abstract interface for LLM operations."""
    
    @abstractmethod
    def analyze_repository(self, file_tree: str) -> Dict[str, Any]:
        """Analyzes repository structure."""
        pass

    @abstractmethod
    def identify_features(self, repo_structure: Dict[str, Any], file_contents: Dict[str, str], file_tree: str = "") -> Dict[str, Any]:
        """Identifies logical features and dependencies."""
        pass
        
    @abstractmethod
    def generate_roadmap(self, features: Dict[str, Any], file_tree: str = "") -> List[Dict[str, Any]]:
        """Generates the release roadmap."""
        pass

    @abstractmethod
    def evaluate_diff(self, diff: str, release_description: str) -> Dict[str, Any]:
        """Evaluates a diff against a proposed release to ensure safety and coherence."""
        pass

class GeminiProvider(LLMProvider):
    MAX_RETRIES = 5
    BASE_DELAY = 5  # seconds

    def __init__(self, api_key: Optional[str] = None):
        key = api_key or os.environ.get("GEMINI_API_KEY")
        if not key:
            raise ValueError("GEMINI_API_KEY is not set.")
        self.client = genai.Client(api_key=key)
        # Using flash model for higher free-tier quota
        self.model_name = "gemini-2.0-flash" 
        
    # Fallback model chain — if primary model quota is exhausted, try the next
    FALLBACK_MODELS = ["gemini-2.0-flash", "gemini-2.0-flash-lite"]

    def _call(self, prompt: str, schema: Optional[Any] = None) -> Dict[str, Any]:
        config = types.GenerateContentConfig(
            temperature=0.2,
        )
        if schema:
            config.response_mime_type = "application/json"
            config.response_schema = schema

        models_to_try = [self.model_name] + [m for m in self.FALLBACK_MODELS if m != self.model_name]
        last_error = None

        for model in models_to_try:
            for attempt in range(self.MAX_RETRIES):
                try:
                    response = self.client.models.generate_content(
                        model=model,
                        contents=prompt,
                        config=config,
                    )
                    if schema:
                        return json.loads(response.text)
                    return {"text": response.text}
                except ClientError as e:
                    last_error = e
                    if e.code == 429:
                        # Check if this is a daily quota exhaustion (limit: 0) vs temporary rate limit
                        error_msg = str(e)
                        if "limit: 0" in error_msg or "PerDay" in error_msg:
                            print(f"  Daily quota exhausted for {model}. Trying next model...")
                            break  # Skip retries, move to next model
                        elif attempt < self.MAX_RETRIES - 1:
                            delay = self.BASE_DELAY * (2 ** attempt)
                            print(f"  Rate limited. Retrying in {delay}s (attempt {attempt + 1}/{self.MAX_RETRIES})...")
                            time.sleep(delay)
                        else:
                            break  # Move to next model
                    else:
                        raise

        # All models exhausted
        raise RuntimeError(
            "All Gemini model quotas are exhausted for today.\n"
            "Options:\n"
            "  1. Wait until your daily quota resets (usually midnight Pacific Time)\n"
            "  2. Enable billing at https://ai.google.dev to get higher limits\n"
            "  3. Use a different API key\n"
            f"\nLast error: {last_error}"
        )

    def analyze_repository(self, file_tree: str) -> Dict[str, Any]:
        prompt = f"""
You are an expert software architect. Analyze the following project structure.
Identify the primary language, framework, build system, and general application architecture (e.g., MVC, Microservices, SPA, etc.).

Project Structure:
{file_tree}
"""
        schema = {
            "type": "OBJECT",
            "properties": {
                "language": {"type": "STRING"},
                "framework": {"type": "STRING"},
                "build_system": {"type": "STRING"},
                "architecture_type": {"type": "STRING"},
                "description": {"type": "STRING"}
            },
            "required": ["language", "framework", "build_system", "architecture_type", "description"]
        }
        return self._call(prompt, schema)

    def identify_features(self, repo_structure: Dict[str, Any], file_contents: Dict[str, str], file_tree: str = "") -> Dict[str, Any]:
        # file_contents should be a summary, not entire codebase, to fit context.
        content_summary = "\n".join([f"File: {k}\n{v[:1000]}..." for k, v in file_contents.items()])
        
        file_tree_section = ""
        if file_tree:
            file_tree_section = f"\nComplete File Tree (EVERY file listed here MUST appear in at least one feature's files_involved):\n{file_tree}\n"
        
        prompt = f"""
Identify the logical features in this codebase. For each feature, estimate complexity (XS, S, M, L, XL) and list any dependencies on other features.

CRITICAL REQUIREMENT: EVERY single file in the file tree below MUST be assigned to at least one feature's "files_involved" list.
This includes:
- Configuration files (composer.json, package.json, docker-compose.yml, .gitignore, etc.)
- DevOps files (Dockerfile, CI/CD configs, etc.)
- Documentation (README.md, LICENSE, SECURITY.md, etc.)
- Utility/helper files
- Model files
- Framework/core files
- Route files
- View/template files
- Frontend build configs (tsconfig.json, vite.config.ts, etc.)

Create a "Project Setup & Configuration" feature for config/DevOps/documentation files.
Do NOT use glob patterns like "frontend/src/components/*". List each file individually.

Architecture:
{json.dumps(repo_structure, indent=2)}
{file_tree_section}
File samples:
{content_summary}
"""
        schema = {
            "type": "OBJECT",
            "properties": {
                "features": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "name": {"type": "STRING"},
                            "description": {"type": "STRING"},
                            "complexity": {"type": "STRING"},
                            "dependencies": {
                                "type": "ARRAY",
                                "items": {"type": "STRING"}
                            },
                            "files_involved": {
                                "type": "ARRAY",
                                "items": {"type": "STRING"}
                            }
                        },
                        "required": ["name", "description", "complexity", "dependencies", "files_involved"]
                    }
                }
            },
            "required": ["features"]
        }
        return self._call(prompt, schema)

    def generate_roadmap(self, features: Dict[str, Any], file_tree: str = "") -> List[Dict[str, Any]]:
        file_tree_section = ""
        if file_tree:
            file_tree_section = f"\nComplete File Tree (every file here MUST appear in exactly one release's files_involved):\n{file_tree}\n"
        
        prompt = f"""
Given these features and dependencies, create an ordered list of logically coherent releases.
Remember:
- Do not release a feature until its dependencies are released.
- Break down L or XL features into smaller releases (XS, S, M).
- Do not make a release too large.
- CRITICAL: EVERY file in the project MUST belong to EXACTLY ONE release's "files_involved".
- Do NOT assign the same file to multiple releases. Duplicate file assignments across releases are strictly prohibited.
- Do NOT use glob patterns like "*". List each file individually by its relative path.
- Include a release for project setup/config files (README, LICENSE, .gitignore, Dockerfiles, composer.json, package.json, etc.) — these should be among the earliest releases.
{file_tree_section}
Features:
{json.dumps(features, indent=2)}
"""
        schema = {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "release_id": {"type": "STRING"},
                    "feature": {"type": "STRING"},
                    "description": {"type": "STRING"},
                    "complexity": {"type": "STRING"},
                    "dependencies": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"}
                    },
                    "files_involved": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"}
                    },
                    "validation_requirements": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"}
                    }
                },
                "required": ["release_id", "feature", "description", "complexity", "dependencies", "files_involved", "validation_requirements"]
            }
        }
        return self._call(prompt, schema)

    def evaluate_diff(self, diff: str, release_description: str) -> Dict[str, Any]:
        prompt = f"""
You are a release safety guard.
We are proposing to commit files for the following release: "{release_description}"

Does this diff contain destructive or unsafe changes (such as deleting critical code or exposing secrets)?
Are there changes that are completely unrelated to the proposed release?

Important rules:
1. For setup, configuration, DevOps, or project setup releases (e.g., "Project Setup & Configuration"), configuration files (.gitignore, composer.json, package.json, docker-compose.yml, Dockerfile, README, LICENSE, GitHub workflows, templates, app-info.json) ARE expected and valid.
2. For initialization files (init.php, bootstrap.php), setting up core services together is normal and safe.
3. Adding new setup or configuration files for a proposed release is safe.

Diff:
{diff}
"""
        schema = {
            "type": "OBJECT",
            "properties": {
                "is_safe": {"type": "BOOLEAN"},
                "unrelated_changes_detected": {"type": "BOOLEAN"},
                "reasoning": {"type": "STRING"}
            },
            "required": ["is_safe", "unrelated_changes_detected", "reasoning"]
        }
        return self._call(prompt, schema)


class GroqProvider(LLMProvider):
    """Alternative LLM provider using Groq's API."""
    MAX_RETRIES = 5
    BASE_DELAY = 3  # seconds
    # Groq free-tier TPM limits are strict; estimate ~4 chars per token
    CHARS_PER_TOKEN = 4
    MAX_INPUT_TOKENS = 10000  # Leave headroom below 12K TPM limit

    # Fallback model chain — try smaller or alternative models if the primary fails/is unavailable
    FALLBACK_MODELS = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "llama3-70b-8192",
        "llama3-8b-8192",
        "gemma2-9b-it",
        "mixtral-8x7b-32768"
    ]

    def __init__(self, api_key: Optional[str] = None):
        try:
            from groq import Groq
        except ImportError:
            raise ImportError("groq package not installed. Run: pip install groq")
        
        key = api_key or os.environ.get("GROQ_API_KEY")
        if not key:
            raise ValueError("GROQ_API_KEY is not set.")
        self.client = Groq(api_key=key)
        self.model_name = "llama-3.3-70b-versatile"

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimate: ~4 chars per token."""
        return len(text) // self.CHARS_PER_TOKEN

    def _call(self, prompt: str, response_format: Optional[Dict] = None) -> Dict[str, Any]:
        models_to_try = [self.model_name] + [m for m in self.FALLBACK_MODELS if m != self.model_name]
        last_error = None

        for model in models_to_try:
            messages = [{"role": "user", "content": prompt}]
            
            # Use smaller max_tokens for smaller models
            max_tokens = 4096 if ("70b" in model or "mixtral" in model) else 2048
            
            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": 0.2,
                "max_tokens": max_tokens,
            }
            if response_format:
                kwargs["response_format"] = {"type": "json_object"}
            
            for attempt in range(self.MAX_RETRIES):
                try:
                    response = self.client.chat.completions.create(**kwargs)
                    text = response.choices[0].message.content
                    if response_format:
                        return json.loads(text)
                    return {"text": text}
                except Exception as e:
                    last_error = e
                    error_str = str(e).lower()
                    
                    # Handle 404 / Model Not Found or Access errors — skip immediately to next model
                    if "404" in str(e) or "does not exist" in error_str or "model_not_found" in error_str:
                        print(f"  Model {model} not found or inaccessible. Trying next model...")
                        break  # Move to next model
                    
                    # Handle 413 Request Too Large — skip to smaller model
                    if "413" in str(e) or "request too large" in error_str:
                        print(f"  Prompt too large for {model}. Trying smaller model...")
                        break  # Move to next model
                    
                    if "rate_limit" in error_str or "429" in str(e):
                        # Check for daily quota exhaustion
                        if "limit: 0" in str(e) or "per day" in error_str:
                            print(f"  Daily quota exhausted for {model}. Trying next model...")
                            break
                        elif attempt < self.MAX_RETRIES - 1:
                            delay = self.BASE_DELAY * (2 ** attempt)
                            print(f"  Rate limited. Retrying in {delay}s (attempt {attempt + 1}/{self.MAX_RETRIES})...")
                            time.sleep(delay)
                        else:
                            break  # Move to next model
                    else:
                        raise

        # All models exhausted
        raise RuntimeError(
            "All Groq model options exhausted.\n"
            "The prompt may be too large for Groq's free tier (12K TPM limit).\n"
            "Options:\n"
            "  1. Set GEMINI_API_KEY instead (higher free-tier limits)\n"
            "  2. Upgrade Groq to Dev Tier at https://console.groq.com/settings/billing\n"
            f"\nLast error: {last_error}"
        )

    def _truncate_content_for_prompt(self, file_contents: Dict[str, str], file_tree: str, 
                                       base_prompt_chars: int, max_chars_per_file: int = 500) -> str:
        """Build content summary that fits within token limits."""
        # Budget: total chars available for content after base prompt and file tree
        tree_chars = len(file_tree) if file_tree else 0
        available_chars = (self.MAX_INPUT_TOKENS * self.CHARS_PER_TOKEN) - base_prompt_chars - tree_chars
        
        if available_chars < 1000:
            # Very tight budget — just use file names
            return "\n".join([f"File: {k}" for k in file_contents.keys()])
        
        # Determine per-file truncation
        num_files = max(len(file_contents), 1)
        per_file_budget = min(max_chars_per_file, available_chars // num_files)
        per_file_budget = max(per_file_budget, 100)  # Minimum 100 chars per file
        
        parts = []
        total_chars = 0
        for k, v in file_contents.items():
            entry = f"File: {k}\n{v[:per_file_budget]}..."
            if total_chars + len(entry) > available_chars:
                parts.append(f"... and {len(file_contents) - len(parts)} more files (truncated for token limits)")
                break
            parts.append(entry)
            total_chars += len(entry)
        
        return "\n".join(parts)

    def analyze_repository(self, file_tree: str) -> Dict[str, Any]:
        prompt = f"""
You are an expert software architect. Analyze the following project structure.
Identify the primary language, framework, build system, and general application architecture (e.g., MVC, Microservices, SPA, etc.).

Respond ONLY with a JSON object with these exact keys: "language", "framework", "build_system", "architecture_type", "description".

Project Structure:
{file_tree}
"""
        return self._call(prompt, response_format=True)

    def identify_features(self, repo_structure: Dict[str, Any], file_contents: Dict[str, str], file_tree: str = "") -> Dict[str, Any]:
        file_tree_section = ""
        if file_tree:
            file_tree_section = f"\nComplete File Tree (EVERY file listed here MUST appear in at least one feature's files_involved):\n{file_tree}\n"
        
        # Estimate base prompt size (without content) to budget content truncation
        base_prompt = f"""
Identify the logical features in this codebase. For each feature, estimate complexity (XS, S, M, L, XL) and list any dependencies on other features.

CRITICAL REQUIREMENT: EVERY single file in the file tree below MUST be assigned to at least one feature's "files_involved" list.
This includes config files, DevOps files, documentation, utilities, models, framework files, routes, views, and frontend build configs.
Create a "Project Setup & Configuration" feature for config/DevOps/documentation files.
Do NOT use glob patterns. List each file individually.

Respond ONLY with a JSON object with key "features" containing an array. Each feature object must have: "name", "description", "complexity", "dependencies" (array of strings), "files_involved" (array of strings).

Architecture:
{json.dumps(repo_structure, indent=2)}
{file_tree_section}
File samples:
"""
        content_summary = self._truncate_content_for_prompt(
            file_contents, file_tree, base_prompt_chars=len(base_prompt)
        )
        
        prompt = base_prompt + content_summary
        return self._call(prompt, response_format=True)

    def generate_roadmap(self, features: Dict[str, Any], file_tree: str = "") -> List[Dict[str, Any]]:
        file_tree_section = ""
        if file_tree:
            file_tree_section = f"\nComplete File Tree (every file here MUST appear in exactly one release's files_involved):\n{file_tree}\n"
        
        prompt = f"""
Given these features and dependencies, create an ordered list of logically coherent releases.
Remember:
- Do not release a feature until its dependencies are released.
- Break down L or XL features into smaller releases (XS, S, M).
- Do not make a release too large.
- CRITICAL: EVERY file in the project MUST belong to EXACTLY ONE release's "files_involved".
- Do NOT assign the same file to multiple releases. Duplicate file assignments across releases are strictly prohibited.
- Do NOT use glob patterns. List each file individually by its relative path.
- Include a release for project setup/config files early on.

Respond ONLY with a JSON array. Each release object must have: "release_id", "feature", "description", "complexity", "dependencies" (array), "files_involved" (array), "validation_requirements" (array).
{file_tree_section}
Features:
{json.dumps(features, indent=2)}
"""
        # Check if prompt is too large and trim if needed
        estimated_tokens = self._estimate_tokens(prompt)
        if estimated_tokens > self.MAX_INPUT_TOKENS:
            print(f"  generate_roadmap prompt estimated at {estimated_tokens} tokens, trimming file tree...")
            # Remove file tree from generate_roadmap since features already contain file lists
            # The coverage validation in roadmap_generator.py will catch any gaps
            prompt = f"""
Given these features and dependencies, create an ordered list of logically coherent releases.
Remember:
- Do not release a feature until its dependencies are released.
- Break down L or XL features into smaller releases (XS, S, M).
- Do not make a release too large.
- CRITICAL: EVERY file listed in the features MUST belong to EXACTLY ONE release's "files_involved".
- Do NOT assign the same file to multiple releases. Duplicate file assignments across releases are strictly prohibited.
- Do NOT use glob patterns. List each file individually.
- Include a release for project setup/config files early on.

Respond ONLY with a JSON array. Each release object must have: "release_id", "feature", "description", "complexity", "dependencies" (array), "files_involved" (array), "validation_requirements" (array).

Features:
{json.dumps(features, indent=2)}
"""

        result = self._call(prompt, response_format=True)
        # The response might be wrapped in an object or be a direct array
        if isinstance(result, list):
            return result
        if isinstance(result, dict) and "releases" in result:
            return result["releases"]
        return result

    def evaluate_diff(self, diff: str, release_description: str) -> Dict[str, Any]:
        prompt = f"""
You are a release safety guard.
We are proposing to commit files for the following release: "{release_description}"

Does this diff contain destructive or unsafe changes (such as deleting critical code or exposing secrets)?
Are there changes that are completely unrelated to the proposed release?

Important rules:
1. For setup, configuration, DevOps, or project setup releases (e.g., "Project Setup & Configuration"), configuration files (.gitignore, composer.json, package.json, docker-compose.yml, Dockerfile, README, LICENSE, GitHub workflows, templates, app-info.json) ARE expected and valid.
2. For initialization files (init.php, bootstrap.php), setting up core services together is normal and safe.
3. Adding new setup or configuration files for a proposed release is safe.

Respond ONLY with a JSON object with these exact keys: "is_safe" (boolean), "unrelated_changes_detected" (boolean), "reasoning" (string).

Diff:
{diff}
"""
        return self._call(prompt, response_format=True)


def create_llm_provider(api_key: Optional[str] = None) -> LLMProvider:
    """Factory function that picks the right provider based on available keys.
    
    Priority: explicit key > GROQ_API_KEY > GEMINI_API_KEY
    """
    from src.utils.env_loader import load_env
    load_env()

    # If a key is explicitly passed, detect its type
    if api_key:
        if api_key.startswith("gsk_"):
            return GroqProvider(api_key=api_key)
        else:
            return GeminiProvider(api_key=api_key)
    
    # Auto-detect from environment
    groq_key = os.environ.get("GROQ_API_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    
    if groq_key:
        print("Using Groq provider.")
        return GroqProvider(api_key=groq_key)
    elif gemini_key:
        print("Using Gemini provider.")
        return GeminiProvider(api_key=gemini_key)
    else:
        raise ValueError(
            "No LLM API key found. Set one of:\n"
            "  - GROQ_API_KEY (for Groq/Llama)\n"
            "  - GEMINI_API_KEY (for Google Gemini)"
        )

