# app_debug.py
import streamlit as st
import asyncio
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from utils.gemini_setup import gemini_setup
import uuid
from typing import Dict, Any, Type

# Define input schema for the tool
class SearchInput(BaseModel):
    query: str = Field(..., description="Search query")
    max_results: int = Field(default=3, description="Maximum number of results")

# Create a CrewAI-compatible tool
class DebugSearchTool(BaseTool):
    name: str = "debug_web_search"
    description: str = "Search the web for current information (debug version)"
    args_schema: Type[BaseModel] = SearchInput

    def _run(self, query: str, max_results: int = 3) -> str:
        """Mock search for testing"""
        mock_results = [
            {
                "title": f"Test Result 1 for {query}",
                "url": "https://example.com/1",
                "snippet": f"This is a test snippet about {query}. It contains mock data for debugging purposes."
            },
            {
                "title": f"Test Result 2 for {query}",
                "url": "https://example.com/2", 
                "snippet": f"Another test result about {query}. This helps verify the agent workflow is working."
            }
        ]
        
        # Format results as string for the agent
        result_text = f"Search results for '{query}':\n\n"
        for i, result in enumerate(mock_results, 1):
            result_text += f"Result {i}:\n"
            result_text += f"Title: {result['title']}\n"
            result_text += f"URL: {result['url']}\n" 
            result_text += f"Snippet: {result['snippet']}\n\n"
        
        return result_text

class DebugResearchOrchestrator:
    def __init__(self):
        self.search_tool = DebugSearchTool()
        self.llm = gemini_setup.get_llm()
    
    def create_research_task(self, agent, query: str) -> Task:
        return Task(
            description=f"""
            Conduct comprehensive research on: {query}
            
            Use the search tool to find current information about this topic.
            Provide a detailed analysis with:
            - Key findings and insights
            - Important trends or developments
            - Relevant context and background
            - Potential implications or applications
            
            Be thorough and analytical in your research.
            """,
            agent=agent,
            expected_output="A comprehensive research report with detailed analysis, key findings, and insights"
        )
    
    def create_summary_task(self, agent, research_data: str) -> Task:
        return Task(
            description=f"""
            Summarize the following research findings:
            
            {research_data}
            
            Create a clear, concise summary that:
            - Highlights the most important points
            - Preserves key insights and conclusions
            - Organizes information logically
            - Uses accessible language
            
            Focus on making the information easy to understand while maintaining accuracy.
            """,
            agent=agent,
            expected_output="A well-structured summary that captures the essence of the research in an accessible format"
        )
    
    async def execute_research_flow(self, query: str) -> Dict[str, Any]:
        """Simplified research flow for debugging"""
        
        session_id = str(uuid.uuid4())
        
        # Create researcher agent with Gemini
        researcher = Agent(
            role="Senior Research Analyst",
            goal="Gather comprehensive and accurate information on various topics",
            backstory="""You are an experienced research analyst with expertise in 
            finding, analyzing, and synthesizing information from multiple sources. 
            You have a keen eye for detail and can identify the most relevant and 
            credible information quickly.""",
            tools=[self.search_tool],
            verbose=True,
            allow_delegation=False,
            llm=self.llm  # Explicitly set Gemini
        )
        
        # Create research task
        research_task = self.create_research_task(researcher, query)
        
        # Execute research
        st.info("🔍 Conducting research with Gemini...")
        research_crew = Crew(
            agents=[researcher],
            tasks=[research_task],
            process=Process.sequential,
            verbose=True
        )
        
        research_results = research_crew.kickoff()
        
        # Create summarizer agent with Gemini
        summarizer = Agent(
            role="Content Summarizer", 
            goal="Transform complex information into clear, concise summaries",
            backstory="""You are a skilled technical writer and editor who excels at 
            distilling complex information into easily understandable formats. 
            You have a talent for identifying core concepts and presenting them 
            in a logical, accessible manner.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm  # Explicitly set Gemini
        )
        
        # Create summary task
        st.info("📝 Creating summary with Gemini...")
        summary_task = self.create_summary_task(summarizer, str(research_results))
        
        summary_crew = Crew(
            agents=[summarizer],
            tasks=[summary_task], 
            process=Process.sequential,
            verbose=True
        )
        
        summary_results = summary_crew.kickoff()
        
        return {
            "session_id": session_id,
            "query": query, 
            "research": str(research_results),
            "summary": str(summary_results),
            "status": "completed"
        }

def main():
    st.set_page_config(
        page_title="Debug Research App - Gemini",
        page_icon="🐛",
        layout="wide"
    )
    
    st.title("🐛 Debug Research System with Gemini")
    st.markdown("Simplified version to test the basic workflow")
    
    # Check API key
    try:
        orchestrator = DebugResearchOrchestrator()
        st.success("✅ Gemini configured successfully")
    except Exception as e:
        st.error(f"❌ Gemini setup failed: {e}")
        st.info("Please check your GOOGLE_API_KEY in the .env file")
        return
    
    # Session state
    if 'research_history' not in st.session_state:
        st.session_state.research_history = []
    
    # Simple interface
    st.header("Test Research")
    query = st.text_input("Enter research query:", placeholder="e.g., Artificial Intelligence trends 2024")
    
    col1, col2 = st.columns(2)
    with col1:
        start_research = st.button("Start Test Research", type="primary")
    with col2:
        if st.button("Clear Results"):
            st.session_state.research_history = []
            st.rerun()
    
    if start_research and query:
        with st.spinner("Running debug research workflow with Gemini..."):
            try:
                result = asyncio.run(orchestrator.execute_research_flow(query))
                st.session_state.research_history.append(result)
                st.success("✅ Research completed successfully!")
            except Exception as e:
                st.error(f"❌ Research failed: {str(e)}")
                st.code(f"Error details: {e}", language="python")
    
    # Display results
    if st.session_state.research_history:
        st.header("Research Results")
        latest = st.session_state.research_history[-1]
        
        st.subheader("📋 Summary")
        st.write(latest['summary'])
        
        with st.expander("🔍 Detailed Research"):
            st.write(latest['research'])
        
        st.subheader("📊 Session Info")
        st.write(f"Query: {latest['query']}")
        st.write(f"Session ID: {latest['session_id']}")
        st.write(f"Status: {latest['status']}")

if __name__ == "__main__":
    main()