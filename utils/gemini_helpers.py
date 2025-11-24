# utils/gemini_helpers.py
import google.generativeai as genai
from config.settings import settings
from typing import List, Dict

class GeminiHelpers:
    def __init__(self):
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')
    
    def generate_content(self, prompt: str) -> str:
        """Generate content using Gemini"""
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating content: {str(e)}"
    
    def batch_process(self, prompts: List[str]) -> List[str]:
        """Process multiple prompts in sequence"""
        results = []
        for prompt in prompts:
            results.append(self.generate_content(prompt))
        return results
    
    def structured_analysis(self, content: str, analysis_type: str) -> Dict:
        """Perform structured analysis on content"""
        prompts = {
            "summary": f"Summarize the following content concisely: {content}",
            "key_points": f"Extract key points from: {content}",
            "critique": f"Provide constructive criticism for: {content}"
        }
        
        if analysis_type not in prompts:
            return {"error": "Invalid analysis type"}
        
        result = self.generate_content(prompts[analysis_type])
        return {"type": analysis_type, "result": result}