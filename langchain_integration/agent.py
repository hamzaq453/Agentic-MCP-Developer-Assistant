from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import PromptTemplate
from typing import Optional, List, Dict, Any
from config.settings import settings
import requests


class MCPToolsAgent:
    """LangChain agent that uses MCP tools from the FastAPI server."""
    
    def __init__(self, server_url: str = "http://localhost:8000", temperature: float = 0):
        """
        Initialize the MCP Tools Agent.
        
        Args:
            server_url: Base URL of the FastAPI MCP server
            temperature: LLM temperature (0 = deterministic, 1 = creative)
        """
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY not configured. Set it in .env file.")
        
        self.server_url = server_url.rstrip('/')
        self.llm = ChatOpenAI(
            temperature=temperature,
            model="gpt-4",
            openai_api_key=settings.openai_api_key
        )
        
        # Initialize conversation memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Create tools from MCP endpoints
        self.tools = self._create_tools()
        
        # Create the ReAct agent
        self.agent = self._create_agent()
        
        # Create agent executor
        self.agent_executor = AgentExecutor.from_agent_and_tools(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=10
        )
    
    def _create_tools(self) -> List[Tool]:
        """Create LangChain tools from MCP endpoints."""
        tools = [
            Tool(
                name="search_github_repos",
                func=lambda query: self._call_api("GET", "/github/search-repos", params={"query": query, "max_results": 5}),
                description="Search for GitHub repositories by keyword. Input should be a search query string."
            ),
            Tool(
                name="get_repo_info",
                func=lambda repo: self._call_api("GET", f"/github/repo/{repo}"),
                description="Get detailed information about a GitHub repository. Input should be in format 'owner/repo'."
            ),
            Tool(
                name="get_github_file",
                func=lambda args: self._get_github_file(args),
                description="Get file content from a GitHub repository. Input should be JSON string: {\"owner\": \"owner\", \"repo\": \"repo\", \"path\": \"file/path.py\"}."
            ),
            Tool(
                name="list_docker_containers",
                func=lambda _: self._call_api("GET", "/docker/containers", params={"all": True}),
                description="List all Docker containers (running and stopped). No input needed."
            ),
            Tool(
                name="get_container_logs",
                func=lambda container_id: self._call_api("GET", f"/docker/containers/{container_id}/logs", params={"tail": 50}),
                description="Get logs from a Docker container. Input should be the container ID or name."
            ),
            Tool(
                name="read_file",
                func=lambda path: self._call_api("GET", "/filesystem/read", params={"path": path}),
                description="Read content from a local file. Input should be the file path."
            ),
            Tool(
                name="list_directory",
                func=lambda path: self._call_api("GET", "/filesystem/list", params={"path": path or "."}),
                description="List contents of a directory. Input should be the directory path (or empty for current directory)."
            ),
            Tool(
                name="search_files",
                func=lambda pattern: self._call_api("GET", "/filesystem/search", params={"pattern": pattern, "directory": ".", "recursive": True}),
                description="Search for files by pattern (supports wildcards like *.py). Input should be the search pattern."
            )
        ]
        return tools
    
    def _call_api(self, method: str, endpoint: str, params: Optional[Dict] = None, json: Optional[Dict] = None) -> str:
        """Make API call to the MCP server."""
        try:
            url = f"{self.server_url}{endpoint}"
            
            if method == "GET":
                response = requests.get(url, params=params, timeout=30)
            elif method == "POST":
                response = requests.post(url, json=json, timeout=30)
            else:
                return f"Error: Unsupported HTTP method {method}"
            
            response.raise_for_status()
            return str(response.json())
        
        except requests.exceptions.RequestException as e:
            return f"Error calling API: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
    
    def _get_github_file(self, args: str) -> str:
        """Helper to get GitHub file with JSON arguments."""
        try:
            import json
            params = json.loads(args)
            owner = params.get("owner")
            repo = params.get("repo")
            path = params.get("path")
            
            if not all([owner, repo, path]):
                return "Error: Missing required parameters (owner, repo, path)"
            
            return self._call_api("GET", f"/github/file/{owner}/{repo}", params={"path": path})
        except json.JSONDecodeError:
            return "Error: Invalid JSON input. Expected format: {\"owner\": \"owner\", \"repo\": \"repo\", \"path\": \"file/path\"}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _create_agent(self):
        """Create the ReAct agent with custom prompt."""
        template = """Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}"""

        prompt = PromptTemplate.from_template(template)
        
        return create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
    
    def run(self, query: str) -> Dict[str, Any]:
        """
        Run the agent with a natural language query.
        
        Args:
            query: Natural language question or task
            
        Returns:
            Dict with 'output' and 'intermediate_steps'
        """
        try:
            result = self.agent_executor.invoke({"input": query})
            return {
                "status": "success",
                "output": result.get("output"),
                "intermediate_steps": str(result.get("intermediate_steps", []))
            }
        except Exception as e:
            return {
                "status": "error",
                "output": f"Agent execution failed: {str(e)}",
                "intermediate_steps": []
            }
    
    def clear_memory(self):
        """Clear conversation history."""
        self.memory.clear()


# Singleton instance
_agent_instance: Optional[MCPToolsAgent] = None


def get_agent() -> MCPToolsAgent:
    """Get or create the agent instance."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = MCPToolsAgent()
    return _agent_instance

