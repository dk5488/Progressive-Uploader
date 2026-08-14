from typing import Dict, Any
from src.llm.provider import LLMProvider

class ComplexityEstimator:
    # We can rely on the LLMProvider to estimate complexity during feature identification,
    # but we may need to re-estimate or split specific increments.
    def __init__(self, llm: LLMProvider):
        self.llm = llm
        
    def needs_split(self, complexity: str) -> bool:
        return complexity in ["L", "XL"]

class IncrementSplitter:
    def __init__(self, llm: LLMProvider):
        self.llm = llm
        
    def split_increment(self, release: Dict[str, Any]) -> list[Dict[str, Any]]:
        # TODO: call LLM to split a large release into smaller ones
        # For MVP, we just return it as is or do a basic split in llm provider.
        return [release]
