# agents/summarizer.py
from crewai import Agent
from utils.gemini_setup import gemini_setup

class SummarizerAgent:
    def __init__(self):
        self.llm = gemini_setup.get_llm()
    
    def create_agent(self) -> Agent:
        return Agent(
            role="Content Summarizer",
            goal="Condense research findings into clear, concise summaries while preserving key insights",
            backstory="""You are a skilled technical writer and summarizer who can 
            transform complex information into easily digestible formats. You excel 
            at identifying core concepts and presenting them clearly.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )