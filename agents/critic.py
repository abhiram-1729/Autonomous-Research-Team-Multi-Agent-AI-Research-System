# agents/critic.py
from crewai import Agent
from utils.gemini_setup import gemini_setup

class CriticAgent:
    def __init__(self):
        self.llm = gemini_setup.get_llm()
    
    def create_agent(self) -> Agent:
        return Agent(
            role="Quality Assurance Critic",
            goal="Validate research quality, identify gaps, and ensure factual accuracy",
            backstory="""You are a meticulous quality assurance expert with a background 
            in academic research and fact-checking. You have zero tolerance for 
            inaccuracies and always push for comprehensive coverage.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )