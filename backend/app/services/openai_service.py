import os
import requests
from dotenv import load_dotenv

class OpenAIService:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.url = "https://api.openai.com/v1/chat/completions"

    def chat_expert(self, query, history=None):
        if not self.api_key:
            return "Error: OpenAI API Key not found in .env file."

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        system_prompt = (
            "You are an expert mentor for CSS (Central Superior Services) and PMS (Provincial Management Service) exams in Pakistan. "
            "Your goal is to provide high-level academic guidance, solve complex queries, evaluate arguments, and offer reasoning grounded in the official syllabus. "
            "CRITICAL: Do NOT use Markdown formatting (no **, ##, ###, or markdown lists). "
            "INSTEAD: Use basic HTML tags for organization. Use <b> for bolding, <br> for new lines, and <ul>/<li> for lists. "
            "Ensure the response is well-organized, clean, and professional for a high-end SaaS portal. "
            "Only answer queries related to CSS/PMS exams, Pakistani history, current affairs, international relations, and general knowledge."
        )

        messages = [{"role": "system", "content": system_prompt}]
        
        if history:
            messages.extend(history)
            
        messages.append({"role": "user", "content": query})

        payload = {
            "model": "gpt-4o-mini",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000
        }

        try:
            response = requests.post(self.url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            return f"Error connecting to OpenAI: {str(e)}"
