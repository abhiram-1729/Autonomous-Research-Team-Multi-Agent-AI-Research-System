# agents/researcher.py
from crewai import Agent
from tools.research_tools import ResearchTools

class ResearcherAgent:
    def __init__(self):
        self.tools = ResearchTools()
    
    def create_agent(self) -> Agent:
        return Agent(
            role="Senior Research Analyst",
            goal="Gather comprehensive, accurate, and up-to-date information on research topics",
            backstory="""You are an expert research analyst with years of experience in 
            gathering and synthesizing information from diverse sources. You have a keen 
            eye for credible sources and can quickly identify relevant information.""",
            tools=[self.tools.get_search_tool()],
            verbose=True,
            allow_delegation=False
        )