# app.py
import streamlit as st
import asyncio
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import uuid
from typing import Dict, Any, Type
import os
from dotenv import load_dotenv
import time

# Import the Supabase client
from database.supabase_client import SupabaseClient

load_dotenv()

# Configure Gemini LLM
try:
    from crewai.llm import LLM
    gemini_llm = LLM(
        model="gemini/gemini-2.0-flash",
        api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.1
    )
except Exception as e:
    st.error(f"Gemini LLM setup failed: {e}")
    gemini_llm = None

# Web Search Tool (same as before)
class WebSearchInput(BaseModel):
    query: str = Field(..., description="Search query")
    max_results: int = Field(default=3, description="Maximum number of results")

class WebSearchTool(BaseTool):
    name: str = "web_search"
    description: str = "Search the web for current information and news"
    args_schema: Type[BaseModel] = WebSearchInput

    def _run(self, query: str, max_results: int = 3) -> str:
        try:
            from ddgs import DDGS
            search_client = DDGS()
            results = search_client.text(query, max_results=max_results)
            
            if not results:
                return f"No results found for query: {query}"
            
            result_text = f"Search results for: {query}\n\n"
            for i, result in enumerate(results, 1):
                result_text += f"[{i}] {result.get('title', 'N/A')}\n"
                result_text += f"   URL: {result.get('href', 'N/A')}\n"
                snippet = result.get('body', 'N/A')
                if len(snippet) > 200:
                    snippet = snippet[:200] + "..."
                result_text += f"   Info: {snippet}\n\n"
            
            return result_text
            
        except Exception as e:
            return f"Search error: {str(e)}"

class ResearchOrchestrator:
    def __init__(self):
        self.search_tool = WebSearchTool()
        self.llm = gemini_llm
        self.db = SupabaseClient()  # Initialize database client
        
        if not self.llm:
            raise ValueError("Gemini LLM not properly initialized. Check your GOOGLE_API_KEY.")
    
    # ... (all your agent creation methods remain the same)
    def create_researcher_agent(self) -> Agent:
        return Agent(
            role="Senior Research Analyst",
            goal="Gather comprehensive, accurate, and up-to-date information on research topics. Be concise and focus on key insights.",
            backstory="""You are an expert research analyst with years of experience in 
            gathering and synthesizing information from diverse sources. You excel at 
            identifying credible sources, extracting key insights, and providing 
            well-structured research reports. You are particularly good at being concise.""",
            tools=[self.search_tool],
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            max_iter=5,
            max_rpm=10
        )
    
    def create_summarizer_agent(self) -> Agent:
        return Agent(
            role="Content Summarizer",
            goal="Condense research findings into clear, concise summaries while preserving key insights. Be very concise.",
            backstory="""You are a skilled technical writer and editor who excels at 
            distilling complex information into easily understandable formats. You have 
            a talent for identifying core concepts and presenting them logically in a concise manner.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            max_iter=3
        )
    
    def create_critic_agent(self) -> Agent:
        return Agent(
            role="Quality Assurance Critic",
            goal="Validate research quality, identify gaps, and ensure factual accuracy. Provide concise feedback.",
            backstory="""You are a meticulous quality assurance expert with a background 
            in academic research and fact-checking. You have zero tolerance for 
            inaccuracies and always push for comprehensive coverage while being concise.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            max_iter=3
        )
    
    # ... (all your task creation methods remain the same)
    def create_research_task(self, agent, query: str) -> Task:
        return Task(
            description=f"""
            Conduct focused research on: {query}
            
            IMPORTANT: Be concise and focus on the most important information.
            
            Requirements:
            - Use the web search tool to gather current information (max 2-3 searches)
            - Focus on recent and credible sources
            - Extract only key facts, trends, and insights
            - Organize information logically but concisely
            - Provide source references
            
            Provide a concise research report with:
            1. Brief executive summary
            2. Key findings with evidence
            3. Important trends
            4. Source credibility assessment
            5. Potential implications
            
            Keep your response under 500 words.
            """,
            agent=agent,
            expected_output="Concise research report with key insights (under 500 words)"
        )
    
    def create_summarization_task(self, agent, research_data: str) -> Task:
        if len(research_data) > 2000:
            research_data = research_data[:2000] + "... [content truncated for length]"
            
        return Task(
            description=f"""
            Summarize the following research findings CONCISELY:
            
            {research_data}
            
            Create a very concise summary that:
            - Highlights only the most important insights
            - Preserves key details but be brief
            - Uses clear, accessible language
            - Maintains factual accuracy
            
            Structure your summary with:
            - Main conclusion (1-2 sentences)
            - Key supporting points (3-4 bullet points)
            - Important implications
            
            Keep your entire response under 200 words.
            """,
            agent=agent,
            expected_output="Very concise summary (under 200 words)"
        )
    
    def create_critique_task(self, agent, summary: str, original_research: str) -> Task:
        if len(summary) > 1000:
            summary = summary[:1000] + "..."
        if len(original_research) > 1500:
            original_research = original_research[:1500] + "..."
            
        return Task(
            description=f"""
            Provide CONCISE critique of this research summary:
            
            SUMMARY:
            {summary}
            
            ORIGINAL RESEARCH (excerpt):
            {original_research}
            
            Provide brief quality assessment evaluating:
            - Accuracy: Does summary match research?
            - Completeness: Any key points missing?
            - Clarity: Is it easy to understand?
            
            Give 1-2 specific improvement suggestions.
            Provide overall quality rating (1-5 stars).
            
            Keep your entire response under 150 words.
            """,
            agent=agent,
            expected_output="Concise critique with rating and suggestions (under 150 words)"
        )
    
    async def execute_research_flow(self, query: str) -> Dict[str, Any]:
        """Execute the complete research flow with all three agents"""
        
        session_id = str(uuid.uuid4())
        
        try:
            # Save initial session to database
            initial_session = {
                "session_id": session_id,
                "query": query,
                "research_output": "",
                "summary_output": "",
                "critique_output": "",
                "status": "in_progress"
            }
            await self.db.save_research_session(initial_session)
            
            # Initialize all agents
            researcher = self.create_researcher_agent()
            summarizer = self.create_summarizer_agent()
            critic = self.create_critic_agent()
            
            # Phase 1: Research
            st.info("🔍 **Phase 1/3: Research** - Gathering information...")
            research_task = self.create_research_task(researcher, query)
            
            research_crew = Crew(
                agents=[researcher],
                tasks=[research_task],
                process=Process.sequential,
                verbose=True
            )
            
            time.sleep(2)
            research_results = research_crew.kickoff()
            
            # Phase 2: Summarization
            st.info("📝 **Phase 2/3: Summarization** - Condensing findings...")
            summary_task = self.create_summarization_task(summarizer, str(research_results))
            
            summary_crew = Crew(
                agents=[summarizer],
                tasks=[summary_task],
                process=Process.sequential,
                verbose=True
            )
            
            time.sleep(2)
            summary_results = summary_crew.kickoff()
            
            # Phase 3: Critique
            st.info("✅ **Phase 3/3: Quality Assurance** - Validating results...")
            critique_task = self.create_critique_task(critic, str(summary_results), str(research_results))
            
            critique_crew = Crew(
                agents=[critic],
                tasks=[critique_task],
                process=Process.sequential,
                verbose=True
            )
            
            time.sleep(2)
            critique_results = critique_crew.kickoff()
            
            # Final result
            final_result = {
                "session_id": session_id,
                "query": query,
                "research": str(research_results),
                "summary": str(summary_results),
                "critique": str(critique_results),
                "status": "completed"
            }
            
            # Update session in database with final results
            await self.db.update_research_session(session_id, {
                "research_output": final_result["research"],
                "summary_output": final_result["summary"],
                "critique_output": final_result["critique"],
                "status": "completed"
            })
            
            return final_result
            
        except Exception as e:
            st.error(f"Research flow error: {e}")
            
            # Update session in database with error
            error_result = {
                "session_id": session_id,
                "query": query,
                "research": f"Research failed: {str(e)}",
                "summary": "Unable to generate summary due to research failure",
                "critique": "Unable to provide critique due to research failure",
                "status": "failed"
            }
            
            await self.db.update_research_session(session_id, {
                "research_output": error_result["research"],
                "summary_output": error_result["summary"],
                "critique_output": error_result["critique"],
                "status": "failed"
            })
            
            return error_result

def main():
    st.set_page_config(
        page_title="Autonomous Research Team - Gemini",
        page_icon="🔬",
        layout="wide"
    )
    
    st.title("🔬 Autonomous Research Team")
    st.markdown("Multi-agent collaborative research system powered by Google Gemini")
    
    # Check if API keys are available
    if not os.getenv("GOOGLE_API_KEY"):
        st.error("❌ GOOGLE_API_KEY not found in environment variables.")
        st.info("Please make sure your .env file contains: GOOGLE_API_KEY=your_actual_key_here")
        return
    
    # Initialize orchestrator and database
    try:
        orchestrator = ResearchOrchestrator()
        st.sidebar.success("✅ System Ready")
        
        # Test database connection
        db = SupabaseClient()
        st.sidebar.success("✅ Database Connected")
        
    except Exception as e:
        st.error(f"❌ System initialization failed: {e}")
        st.info("Please check your environment variables and try again.")
        return
    
    # Session state
    if 'research_history' not in st.session_state:
        st.session_state.research_history = []
    if 'current_session' not in st.session_state:
        st.session_state.current_session = None
    
    # Sidebar
    with st.sidebar:
        st.header("Settings")
        
        # Database operations
        st.subheader("Database Operations")
        if st.button("🔄 Load from Database", use_container_width=True):
            try:
                sessions = asyncio.run(orchestrator.db.get_all_sessions())
                if sessions:
                    st.session_state.research_history = [{
                        "session_id": session["session_id"],
                        "query": session["query"],
                        "research": session["research_output"],
                        "summary": session["summary_output"],
                        "critique": session["critique_output"],
                        "status": session["status"]
                    } for session in sessions]
                    st.success(f"Loaded {len(sessions)} sessions from database")
                else:
                    st.info("No sessions found in database")
            except Exception as e:
                st.error(f"Error loading from database: {e}")
        
        col1, col2 = st.columns(2)
        with col1:
            clear_history = st.button("🗑️ Clear Local", use_container_width=True)
        with col2:
            if st.button("🗑️ Clear Database", use_container_width=True):
                st.warning("This will delete all sessions from the database!")
                # You would implement a bulk delete method in the SupabaseClient
    
    # Main content area - TABS
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 Research", "📊 Results", "📚 History", "💾 Database"])
    
    with tab1:
        st.header("Start New Research")
        
        # MAIN INPUT AREA
        st.subheader("Enter Your Research Query")
        query = st.text_area(
            "What would you like to research?",
            placeholder="Example: 'AI trends 2024' or 'Renewable energy'...",
            height=80,
            key="main_query_input"
        )
        
        # Research button
        col1, col2 = st.columns([1, 3])
        with col1:
            start_research = st.button("🚀 Start Research", type="primary", use_container_width=True)
        
        # Simple example queries
        with st.expander("💡 Quick Test Queries"):
            st.write("Try these simple queries first:")
            
            simple_examples = [
                "AI in healthcare",
                "Renewable energy trends",
                "Space exploration updates",
                "Electric vehicles 2024"
            ]
            
            for example in simple_examples:
                if st.button(example, key=f"example_{example}", use_container_width=True):
                    st.session_state.main_query_input = example
                    st.rerun()
        
        # Research execution
        if start_research and query:
            with st.status("🧠 Orchestrating Research Team...", expanded=True) as status:
                try:
                    st.write("🤖 Starting research process...")
                    result = asyncio.run(orchestrator.execute_research_flow(query))
                    
                    # Update session state
                    st.session_state.research_history.append(result)
                    st.session_state.current_session = result
                    
                    if result['status'] == 'completed':
                        status.update(label="✅ Research Completed Successfully!", state="complete")
                        st.balloons()
                        st.success("Research completed! Switch to the **Results** tab to see the findings.")
                    else:
                        status.update(label="❌ Research Partially Failed", state="error")
                        st.warning("Research encountered issues. Check the Results tab for details.")
                    
                except Exception as e:
                    status.update(label="❌ Research Failed", state="error")
                    st.error(f"Research failed: {str(e)}")
                    st.info("This might be due to API rate limits. Please wait a minute and try again with a simpler query.")
        elif start_research and not query:
            st.warning("⚠️ Please enter a research query first.")
    
    with tab2:
        st.header("Research Results")
        
        if st.session_state.current_session or st.session_state.research_history:
            research_data = st.session_state.current_session or st.session_state.research_history[-1]
            
            # Display query at the top
            st.subheader(f"Research: {research_data['query']}")
            
            if research_data['status'] == 'completed':
                # Summary Section
                st.markdown("### 📋 Executive Summary")
                st.info(research_data['summary'])
                
                # Detailed Research
                with st.expander("🔍 View Detailed Research Report"):
                    st.markdown("### Detailed Research Findings")
                    st.write(research_data['research'])
                
                # Quality Assessment
                with st.expander("✅ View Quality Assessment"):
                    st.markdown("### Quality Review")
                    st.write(research_data['critique'])
                
                # Session Info
                with st.expander("📊 Session Information"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Query:** {research_data['query']}")
                        st.write(f"**Status:** {research_data['status']}")
                    with col2:
                        st.write(f"**Session ID:** {research_data['session_id']}")
                        st.write(f"**Model:** Gemini 1.5 Flash")
            else:
                st.error("❌ Research failed or partially completed")
                st.write("Research output:", research_data['research'])
                st.write("Summary:", research_data['summary'])
                st.write("Critique:", research_data['critique'])
        else:
            st.info("👆 Start a research session in the **Research** tab to see results here.")
    
    with tab3:
        st.header("Local Research History")
        
        if st.session_state.research_history:
            st.write(f"Total local sessions: {len(st.session_state.research_history)}")
            
            for i, research in enumerate(reversed(st.session_state.research_history)):
                with st.expander(f"Session #{len(st.session_state.research_history)-i}: {research['query'][:50]}...", expanded=i==0):
                    st.write(f"**Full Query:** {research['query']}")
                    st.write(f"**Status:** {research['status']}")
                    
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        if st.button(f"📖 Load", key=f"load_{i}", use_container_width=True):
                            st.session_state.current_session = research
                            st.rerun()
                    with col2:
                        if st.button(f"🗑️ Delete", key=f"delete_{i}", use_container_width=True):
                            st.session_state.research_history.pop(-(i+1))
                            st.rerun()
                    
                    if research['status'] == 'completed':
                        st.markdown("**Summary Preview:**")
                        preview = research['summary'][:200] + "..." if len(research['summary']) > 200 else research['summary']
                        st.write(preview)
                    else:
                        st.error("This research session failed.")
        else:
            st.info("No local research history yet.")
    
    with tab4:
        st.header("Database Sessions")
        
        try:
            sessions = asyncio.run(orchestrator.db.get_all_sessions(limit=20))
            
            if sessions:
                st.write(f"Total database sessions: {len(sessions)}")
                
                for i, session in enumerate(sessions):
                    with st.expander(f"DB Session #{i+1}: {session['query'][:50]}...", expanded=i==0):
                        st.write(f"**Full Query:** {session['query']}")
                        st.write(f"**Session ID:** {session['session_id']}")
                        st.write(f"**Status:** {session['status']}")
                        st.write(f"**Created:** {session['created_at']}")
                        
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            if st.button(f"📖 Load from DB", key=f"db_load_{i}", use_container_width=True):
                                st.session_state.current_session = {
                                    "session_id": session["session_id"],
                                    "query": session["query"],
                                    "research": session["research_output"],
                                    "summary": session["summary_output"],
                                    "critique": session["critique_output"],
                                    "status": session["status"]
                                }
                                st.rerun()
                        with col2:
                            if st.button(f"🗑️ Delete from DB", key=f"db_delete_{i}", use_container_width=True):
                                asyncio.run(orchestrator.db.delete_research_session(session['session_id']))
                                st.success("Session deleted from database")
                                st.rerun()
                        
                        if session['status'] == 'completed':
                            st.markdown("**Summary Preview:**")
                            preview = session['summary_output'][:200] + "..." if session['summary_output'] and len(session['summary_output']) > 200 else session['summary_output']
                            st.write(preview or "No summary available")
            else:
                st.info("No sessions found in database. Start some research first!")
                
        except Exception as e:
            st.error(f"Error accessing database: {e}")
    
    if clear_history:
        st.session_state.research_history = []
        st.session_state.current_session = None
        st.rerun()

if __name__ == "__main__":
    main()