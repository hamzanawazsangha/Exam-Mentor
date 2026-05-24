import requests
import json
import os
from .vector_store import VectorStore

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "mistral:7b-instruct"


class EssayGenerator:
    def __init__(self):
        # Determine the root directory (4 levels up from e:\...\backend\app\services\essay_service.py)
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self.vs = VectorStore(db_path=os.path.join(self.base_dir, "chroma_db_v2"))

    def get_context(self, topic):
        results = self.vs.search(topic, n_results=5)
        docs = results.get('documents', [[]])[0]
        return "\n\n".join(docs)

    def generate_essay(self, topic):
        print(f"[Essay] Generating structured essay for: {topic}")
        context = self.get_context(topic)

        # Step 1: Generate a structured outline
        outline_prompt = (
            f"You are an expert CSS/PMS exam coach.\n"
            f"Topic: {topic}\n"
            f"Context from study material:\n{context[:1500]}\n\n"
            f"Write a numbered 10-section outline for a professional academic essay. "
            f"Include: Introduction with thesis, 7 analytical body sections with sub-arguments, "
            f"and a Conclusion. Output ONLY the numbered outline, one section per line."
        )
        outline_raw = self._call_llm(outline_prompt)
        sections = [s.strip() for s in outline_raw.split('\n') if s.strip()]

        # Step 2: Generate content section by section
        full_essay = f"# {topic}\n\n"
        for section in sections:
            print(f"  → Section: {section[:60]}...")
            section_prompt = (
                f"You are writing a formal CSS exam essay.\n"
                f"Section heading: {section}\n"
                f"Relevant context:\n{context[:1200]}\n\n"
                f"Write approximately 250 words of formal, analytical academic prose for this section. "
                f"Use facts from the context. Do NOT use bullet points."
            )
            content = self._call_llm(section_prompt)
            full_essay += f"## {section}\n\n{content}\n\n"

        word_count = len(full_essay.split())
        print(f"[Essay] Complete. Approx. {word_count} words.")
        return full_essay

    def _call_llm(self, prompt):
        """Call local model via Ollama Chat API with Mistral optimization."""
        try:
            payload = {
                "model": OLLAMA_MODEL,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_ctx": 2048,
                    "num_predict": 512
                }
            }
            response = requests.post(OLLAMA_URL, json=payload, timeout=300)
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content", "[No response from model]")
        except requests.exceptions.ConnectionError:
            return "[Error: Ollama is not running. Please start it with: ollama serve]"
        except Exception as e:
            return f"[Error generating content: {e}]"


if __name__ == "__main__":
    eg = EssayGenerator()
    essay = eg.generate_essay("Climate Change and Pakistan's Agricultural Crisis")
    print(essay[:500])
