# utils/helpers.py
from crewai import Task
from typing import List, Dict

def create_research_task(agent, query: str, context: List[Dict] = None) -> Task:
    """Create research task for the researcher agent"""
    return Task(
        description=f"""
        Conduct comprehensive research on: {query}
        
        Requirements:
        - Gather information from multiple credible sources
        - Focus on recent and relevant information
        - Document sources and key findings
        - Identify main themes and sub-topics
        - Provide detailed analysis with supporting evidence
        
        Context from previous research: {context or 'No previous context'}
        """,
        agent=agent,
        expected_output="""Comprehensive research report containing:
        - Executive summary
        - Key findings with supporting evidence
        - Source references
        - Main themes and patterns
        - Credibility assessment of sources"""
    )

def create_summarization_task(agent, research_data: str) -> Task:
    """Create summarization task for the summarizer agent"""
    return Task(
        description=f"""
        Summarize the following research findings:
        
        {research_data}
        
        Create a concise summary that:
        - Highlights key insights and findings
        - Preserves important details and context
        - Organizes information logically
        - Uses clear, accessible language
        - Maintains factual accuracy
        - Identifies the most important takeaways
        
        Structure your summary with:
        1. Main conclusion
        2. Key supporting points
        3. Important context or limitations
        """,
        agent=agent,
        expected_output="Well-structured summary with key insights, main points, and clear organization"
    )

def create_critique_task(agent, summary: str, original_research: str) -> Task:
    """Create critique task for the critic agent"""
    return Task(
        description=f"""
        Critique the following research summary:
        
        SUMMARY:
        {summary}
        
        ORIGINAL RESEARCH:
        {original_research}
        
        Provide a thorough quality assessment that evaluates:
        
        1. **Factual Accuracy**: Check if the summary accurately represents the original research
        2. **Completeness**: Identify any important information missing from the summary
        3. **Clarity**: Assess how clear and understandable the summary is
        4. **Bias Detection**: Look for any potential biases or unbalanced representation
        5. **Logical Flow**: Evaluate the organization and logical progression
        6. **Actionable Feedback**: Provide specific suggestions for improvement
        
        Format your critique with:
        - Strengths of the summary
        - Areas for improvement
        - Specific recommendations
        - Overall quality rating (1-5 stars)
        """,
        agent=agent,
        expected_output="Comprehensive critique with specific feedback, improvement suggestions, and quality rating"
    )