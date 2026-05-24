import requests
import json
import os
from .vector_store import VectorStore

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "mistral:7b-instruct"

class AnswerEvaluator:
    def __init__(self):
        # Determine the root directory (4 levels up from e:\...\backend\app\services\evaluator_service.py)
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self.vs = VectorStore(db_path=os.path.join(self.base_dir, "chroma_db_v2"))

    def evaluate(self, question, user_answer):
        """Evaluate using local Mistral with chunking for large inputs."""
        # Use chunking if answer is very long (to avoid Mistral context limits)
        if len(user_answer) > 5000:
            return self.evaluate_long_essay(question, user_answer)
        
        return self._evaluate_chunk(question, user_answer, "Full Paper")

    def evaluate_long_essay(self, question, user_answer):
        """Split large text into parts, evaluate, and synthesize using Mistral."""
        chunk_size = 4000
        parts = [user_answer[i:i+chunk_size] for i in range(0, len(user_answer), chunk_size)]
        
        feedbacks = []
        for i, part in enumerate(parts):
            print(f"[Mistral] Processing Segment {i+1}/{len(parts)}...")
            res = self._evaluate_chunk(question, part, f"Segment {i+1}")
            feedbacks.append(res)
            
        synthesis_prompt = (
            "You are a Senior CSS Head Examiner. Based on these partial evaluations of a long paper, "
            "provide a single holistic grade and a final structured report using the premium HTML format.\n\n"
            "PARTIAL EVALUATIONS:\n" + "\n---\n".join(feedbacks)
        )
        return self._call_llm("Senior CSS Examiner Synthesizer", synthesis_prompt)

    def _evaluate_chunk(self, question, user_answer, context_label):
        """Internal helper to call Mistral for a specific text segment."""
        results = self.vs.search(question, n_results=2)
        ground_truth = "\n\n".join(results.get('documents', [[]])[0])

        system_prompt = "You are a senior CSS/PPSC examiner. Evaluate the provided text professionally using HTML."
        user_prompt = (
            f"EVALUATION TASK: Grade the following subjective answer segment ({context_label}) against the question and study material.\n\n"
            f"QUESTION: {question}\n"
            f"OFFICIAL STUDY MATERIAL:\n{ground_truth[:1500]}\n"
            f"CANDIDATE'S ANSWER:\n{user_answer}\n\n"
            f"OUTPUT FORMAT (Strictly use HTML):\n"
            f"<div style='border-left: 4px solid #2563eb; padding-left: 15px; margin-bottom: 20px;'>"
            f"  <h2 style='color: #1e40af; margin-top: 0;'>Official Examiner's Report</h2>"
            f"  <p style='font-size: 1.2em;'><b>PREDICTED MARKS:</b> <span style='color: #2563eb;'>[X]/20</span></p>"
            f"</div>"
            f"<table style='width: 100%; border-collapse: collapse; margin-bottom: 20px;'>"
            f"  <tr style='background: #f1f5f9;'><th style='padding: 10px; border: 1px solid #cbd5e1;'>Criterion</th><th style='padding: 10px; border: 1px solid #cbd5e1;'>Score</th><th style='padding: 10px; border: 1px solid #cbd5e1;'>Examiner's Remarks</th></tr>"
            f"  <tr><td style='padding: 10px; border: 1px solid #cbd5e1;'>Factual Accuracy</td><td style='padding: 10px; border: 1px solid #cbd5e1;'>[X]/10</td><td style='padding: 10px; border: 1px solid #cbd5e1;'>[Detailed feedback based on official facts]</td></tr>"
            f"  <tr><td style='padding: 10px; border: 1px solid #cbd5e1;'>Analytical Depth</td><td style='padding: 10px; border: 1px solid #cbd5e1;'>[X]/5</td><td style='padding: 10px; border: 1px solid #cbd5e1;'>[Feedback on critical thinking]</td></tr>"
            f"  <tr><td style='padding: 10px; border: 1px solid #cbd5e1;'>Structure & Language</td><td style='padding: 10px; border: 1px solid #cbd5e1;'>[X]/5</td><td style='padding: 10px; border: 1px solid #cbd5e1;'>[Feedback on presentation]</td></tr>"
            f"</table>"
            f"<h3 style='color: #1e40af;'>Strategic Advice for Improvement</h3>"
            f"<p style='background: #f0fdf4; padding: 15px; border-radius: 8px; border: 1px solid #dcfce7;'>[Specific actionable advice]</p>"
        )

        return self._call_llm(system_prompt, user_prompt)

    def _call_llm(self, sys_msg, user_msg):
        try:
            payload = {
                "model": OLLAMA_MODEL,
                "messages": [{"role": "system", "content": sys_msg}, {"role": "user", "content": user_msg}],
                "stream": False,
                "options": {"temperature": 0.1, "num_ctx": 4096}
            }
            res = requests.post(OLLAMA_URL, json=payload, timeout=300)
            if res.ok:
                return res.json().get("message", {}).get("content", "[No Response]")
            return f"[Ollama Error: {res.status_code} - {res.text}]"
        except Exception as e:
            return f"[Mistral Error: {str(e)}]"
