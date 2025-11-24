# database/supabase_client.py
import supabase
import os
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

class SupabaseClient:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")
        
        if not self.url or not self.key:
            raise ValueError("Supabase URL and Key must be set in environment variables")
        
        self.client = supabase.create_client(self.url, self.key)
    
    def create_tables(self):
        """Create necessary tables if they don't exist"""
        # Tables will be created via SQL in Supabase dashboard
        # This is just a placeholder to show what tables we need
        pass
    
    async def save_research_session(self, session_data: Dict[str, Any]) -> str:
        """Save research session to database"""
        try:
            data = {
                "query": session_data["query"],
                "research_output": session_data.get("research", ""),
                "summary_output": session_data.get("summary", ""),
                "critique_output": session_data.get("critique", ""),
                "status": session_data.get("status", "completed"),
                "session_id": session_data["session_id"]
            }
            
            response = self.client.table('research_sessions').insert(data).execute()
            
            if response.data:
                return response.data[0]['id']
            else:
                raise Exception("No data returned from insert")
                
        except Exception as e:
            print(f"Error saving research session: {e}")
            return None
    
    async def update_research_session(self, session_id: str, updates: Dict[str, Any]):
        """Update research session with new data"""
        try:
            self.client.table('research_sessions').update(updates).eq('session_id', session_id).execute()
        except Exception as e:
            print(f"Error updating research session: {e}")
    
    async def get_research_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve research session by session_id"""
        try:
            response = self.client.table('research_sessions').select('*').eq('session_id', session_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error getting research session: {e}")
            return None
    
    async def get_all_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all research sessions"""
        try:
            response = self.client.table('research_sessions').select('*').order('created_at', desc=True).limit(limit).execute()
            return response.data
        except Exception as e:
            print(f"Error getting all sessions: {e}")
            return []
    
    async def save_agent_output(self, agent_data: Dict[str, Any]):
        """Save individual agent output (optional - for detailed tracking)"""
        try:
            self.client.table('agent_outputs').insert(agent_data).execute()
        except Exception as e:
            print(f"Error saving agent output: {e}")
    
    async def delete_research_session(self, session_id: str):
        """Delete a research session"""
        try:
            self.client.table('research_sessions').delete().eq('session_id', session_id).execute()
        except Exception as e:
            print(f"Error deleting research session: {e}")