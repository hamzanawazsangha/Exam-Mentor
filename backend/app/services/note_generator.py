#!/usr/bin/env python3
"""
Comprehensive Note Generation Service using Mistral via Ollama.
Generates detailed study materials, solutions, and supplementary content.
"""

import requests
import json
import time

class NoteGenerator:
    def __init__(self):
        """
        Initialize Mistral client via Ollama.
        """
        self.ollama_url = "http://localhost:11434/api/chat"
        self.model = "mistral:7b-instruct"
        self.rate_limit_delay = 0.1  # seconds between API calls
        
        # Test connection
        try:
            test_payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": "test"}],
                "stream": False
            }
            response = requests.post(self.ollama_url, json=test_payload, timeout=5)
            if not response.ok:
                raise ValueError("Ollama server is not responding correctly")
        except requests.exceptions.ConnectionError:
            raise ValueError(
                "Ollama is not running. Please start it with: ollama serve\n"
                "And ensure Mistral is installed with: ollama pull mistral"
            )
        except Exception as e:
            raise ValueError(f"Failed to initialize Ollama client: {str(e)}")
        
    def _call_mistral(self, prompt, max_tokens=2000):
        """
        Internal method to call Mistral via Ollama.
        """
        time.sleep(self.rate_limit_delay)
        
        try:
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_ctx": 4096,
                    "num_predict": max_tokens
                }
            }
            response = requests.post(self.ollama_url, json=payload, timeout=300)
            response.raise_for_status()
            return response.json().get("message", {}).get("content", "[No response from model]")
        except Exception as e:
            return f"[Mistral Error: {str(e)}]"

    def generate_comprehensive_note(self, topic, subject, existing_content=None):
        """
        Generate comprehensive study notes for a topic.
        
        Args:
            topic: The topic/question to generate notes for
            subject: Subject area (e.g., "History", "English Essay", "Government")
            existing_content: Optional existing content to enhance
            
        Returns:
            dict with notes, key_points, examples, and additional resources
        """
        prompt = f"""You are an expert Pakistani educator preparing comprehensive study materials for CSS and PMS exams.

Generate detailed, well-structured study notes for the following:

**Subject**: {subject}
**Topic**: {topic}

{f"**Existing Content to Enhance**: {existing_content}" if existing_content else ""}

Please provide:

1. **Overview**: Brief but comprehensive overview of the topic
2. **Key Concepts**: Main concepts with clear definitions
3. **Key Points**: 5-7 essential points students must know
4. **Historical Context**: Relevant background/timeline (if applicable)
5. **Current Relevance**: How this relates to modern Pakistan/world
6. **Case Studies/Examples**: 2-3 relevant examples or case studies
7. **Common Misconceptions**: Address typical student errors
8. **Exam Tips**: Specific advice for CSS/PMS exam answers
9. **Related Topics**: Topics to study alongside this one
10. **Summary**: One-paragraph summary for quick revision

Ensure content is:
- Accurate and fact-based
- Suitable for CSS/PMS exam level
- Written in clear English
- Well-structured with clear formatting
"""
        
        content = self._call_mistral(prompt, max_tokens=2000)
        
        try:
            # Try to parse JSON response
            result = json.loads(content)
            return result
        except json.JSONDecodeError:
            # If not valid JSON, structure the response
            return {"generated_content": content}

    def generate_solution(self, question, subject, question_type="essay"):
        """
        Generate complete solution with step-by-step breakdown.
        
        Args:
            question: The question/problem to solve
            subject: Subject area
            question_type: "essay", "mcq", "short_answer", "problem"
            
        Returns:
            dict with full solution breakdown
        """
        prompt = f"""You are an expert Pakistani exam coach. A student cannot solve this problem. Provide a COMPLETE, FULL solution.

**Subject**: {subject}
**Question Type**: {question_type}
**Question**: {question}

Provide:
1. **Understanding**: What the question is asking
2. **Key Concepts**: Relevant concepts needed
3. **Step-by-Step Solution**: Detailed steps (no steps skipped)
4. **Reasoning**: Explanation for each step
5. **Answer**: Clear final answer
6. **Alternative Approaches**: Other ways to solve (if applicable)
7. **Common Mistakes**: Errors students make on this type of question
8. **Tips for Exam**: Time management and writing strategy
9. **Related Problems**: Similar questions to practice

For essays: Structure with intro, body paragraphs, conclusion.
For MCQs: Explain why correct answer is right, why others are wrong.
For problems: Show all working and calculations.

Ensure response is well-structured and comprehensive.
"""
        
        content = self._call_mistral(prompt, max_tokens=3000)
        
        try:
            result = json.loads(content)
            return result
        except json.JSONDecodeError:
            return {"generated_solution": content}

    def generate_study_plan(self, weak_topics, exam_type="CSS"):
        """
        Generate personalized study plan based on weak areas.
        
        Args:
            weak_topics: List of topics student struggles with
            exam_type: "CSS" or "PMS"
            
        Returns:
            dict with study plan and schedule
        """
        prompt = f"""Create a personalized study plan for a {exam_type} exam aspirant.

**Weak Topics**: {', '.join(weak_topics)}

Generate a focused study plan that:
1. Prioritizes difficult topics
2. Includes daily schedule (next 30 days)
3. Recommends resources and practice
4. Includes revision cycles
5. Includes mock test schedule

Ensure the plan is:
- Practical and achievable
- Well-structured with clear timelines
- Focused on exam success
"""
        
        content = self._call_mistral(prompt, max_tokens=2000)
        
        try:
            result = json.loads(content)
            return result
        except json.JSONDecodeError:
            return {"study_plan": content}

    def generate_supplementary_materials(self, topic, subject):
        """
        Generate additional study materials (MCQs, short answers, essay outlines).
        
        Args:
            topic: Topic to generate materials for
            subject: Subject area
            
        Returns:
            dict with MCQs, short answers, and essay outlines
        """
        prompt = f"""Generate supplementary study materials for revision.

**Subject**: {subject}
**Topic**: {topic}

Provide:
1. **5 Multiple Choice Questions**: With 4 options each (mark correct answer with *)
2. **5 Short Answer Questions**: With 2-3 line model answers
3. **2 Essay Outlines**: Detailed outlines with key points
4. **Key Definitions**: 10 important terms with definitions
5. **Memory Aids**: Mnemonics or memory tricks
6. **Quick Facts**: 10 bullet points for last-minute revision

Ensure all materials are:
- Exam-level appropriate
- Well-structured
- Clear and comprehensive
"""
        
        content = self._call_mistral(prompt, max_tokens=2500)
        
        try:
            result = json.loads(content)
            return result
        except json.JSONDecodeError:
            return {"supplementary_materials": content}


if __name__ == "__main__":
    # Test the note generator
    gen = NoteGenerator()
    
    # Test 1: Generate comprehensive notes
    print("Generating comprehensive notes...")
    notes = gen.generate_comprehensive_note(
        "What is Provincial Management Service (PMS)",
        "Government & Administration"
    )
    print(json.dumps(notes, indent=2))
    
    print("\n" + "="*80 + "\n")
    
    # Test 2: Generate solution for a question
    print("Generating solution...")
    solution = gen.generate_solution(
        "Analyze the role of the civil service in Pakistan's democratic system",
        "Government & Administration",
        "essay"
    )
    print(json.dumps(solution, indent=2))
