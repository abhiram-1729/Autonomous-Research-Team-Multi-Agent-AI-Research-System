# tools/research_tools.py
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, List, Dict
try:
    from ddgs import DDGS  # Use the new package name
except ImportError:
    from duckduckgo_search import DDGS  # Fallback to old name

# Define input schema for search tool
class SearchInput(BaseModel):
    query: str = Field(..., description="Search query to look up")
    max_results: int = Field(default=5, description="Maximum number of search results")

class WebSearchTool(BaseTool):
    name: str = "web_search"
    description: str = "Search the web for current information and news"
    args_schema: Type[BaseModel] = SearchInput

    def _run(self, query: str, max_results: int = 5) -> str:
        """Perform web search and return formatted results"""
        try:
            search_client = DDGS()
            results = search_client.text(query, max_results=max_results)
            
            if not results:
                return f"No results found for query: {query}"
            
            # Format results as string for the agent
            result_text = f"Search results for '{query}':\n\n"
            for i, result in enumerate(results, 1):
                result_text += f"--- Result {i} ---\n"
                result_text += f"Title: {result.get('title', 'N/A')}\n"
                result_text += f"URL: {result.get('href', 'N/A')}\n"
                result_text += f"Snippet: {result.get('body', 'N/A')}\n\n"
            
            return result_text
            
        except Exception as e:
            return f"Search error: {str(e)}"

class ResearchTools:
    def __init__(self):
        self.web_search_tool = WebSearchTool()
    
    def get_search_tool(self) -> WebSearchTool:
        return self.web_search_tool