# simple_test.py
import streamlit as st
from crewai import Agent, Task, Crew, Process
from crewai.llm import LLM
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    st.title("Simple CrewAI Test with Gemini")
    
    # Configure Gemini LLM
    gemini_llm = LLM(
        model="gemini/gemini-2.0-flash",  # or "gemini/gemini-1.5-pro"
        api_key=os.getenv("GOOGLE_API_KEY")
    )
    
    query = st.text_input("Enter query:", "latest developments in renewable energy")
    
    if st.button("Run Test"):
        # Create a simple agent with Gemini
        researcher = Agent(
            role="Research Assistant",
            goal="Provide information and analysis on various topics",
            backstory="You are a knowledgeable assistant who can provide detailed information.",
            verbose=True,
            llm=gemini_llm  # Explicitly set Gemini LLM
        )
        
        task = Task(
            description=f"Provide a comprehensive overview of: {query}",
            agent=researcher,
            expected_output="Detailed report with analysis"
        )
        
        crew = Crew(
            agents=[researcher],
            tasks=[task],
            verbose=True
        )
        
        with st.spinner("Processing with Gemini..."):
            try:
                result = crew.kickoff()
                st.success("Done!")
                st.write(result)
            except Exception as e:
                st.error(f"Error: {e}")
                st.info("Make sure your GOOGLE_API_KEY is set in the .env file")

if __name__ == "__main__":
    main()