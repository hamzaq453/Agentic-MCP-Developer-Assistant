from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from langchain_integration.agent import get_agent
from langchain_integration.chains import get_code_analysis_chain, get_repo_analysis_chain

router = APIRouter()


class AgentQueryRequest(BaseModel):
    """Request model for agent queries."""
    query: str = Field(..., description="Natural language query or task")
    clear_memory: bool = Field(False, description="Clear conversation history before running")


class CodeAnalysisRequest(BaseModel):
    """Request model for code analysis."""
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    file_path: str = Field(..., description="Path to file in repository")
    branch: str = Field("main", description="Branch name")


class RepositoryAnalysisRequest(BaseModel):
    """Request model for repository analysis."""
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")


@router.post(
    "/agent/query",
    summary="Run AI Agent Query",
    description="Execute a natural language query using the LangChain ReAct agent with access to all MCP tools"
)
async def run_agent_query(request: AgentQueryRequest):
    """
    Run an AI agent query that can use multiple tools.
    
    The agent has access to:
    - GitHub operations (search, get info, read files)
    - Docker operations (list containers, get logs)
    - Filesystem operations (read, list, search)
    """
    try:
        agent = get_agent()
        
        if request.clear_memory:
            agent.clear_memory()
        
        result = agent.run(request.query)
        
        return {
            "status": result["status"],
            "query": request.query,
            "answer": result["output"],
            "reasoning": result.get("intermediate_steps", "")
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")


@router.post(
    "/agent/clear-memory",
    summary="Clear Agent Memory",
    description="Clear the agent's conversation history"
)
async def clear_agent_memory():
    """Clear the conversation memory of the agent."""
    try:
        agent = get_agent()
        agent.clear_memory()
        return {"status": "success", "message": "Agent memory cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear memory: {str(e)}")


@router.post(
    "/analysis/code",
    summary="Analyze Code File",
    description="Use AI to analyze code quality, security, and best practices of a file from GitHub"
)
async def analyze_code(request: CodeAnalysisRequest):
    """
    Analyze a code file from a GitHub repository.
    
    Provides:
    - Code quality assessment
    - Security concerns
    - Performance considerations
    - Best practices violations
    - Improvement suggestions
    """
    try:
        chain = get_code_analysis_chain()
        result = chain.analyze_file(
            owner=request.owner,
            repo=request.repo,
            file_path=request.file_path,
            branch=request.branch
        )
        
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        
        return result
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Code analysis failed: {str(e)}")


@router.post(
    "/analysis/repository",
    summary="Analyze Repository",
    description="Use AI to analyze a GitHub repository's purpose, stack, and quality"
)
async def analyze_repository(request: RepositoryAnalysisRequest):
    """
    Analyze a GitHub repository.
    
    Provides:
    - Project purpose and use case
    - Technology stack
    - Code quality indicators
    - Community health metrics
    - Recommendations
    """
    try:
        chain = get_repo_analysis_chain()
        result = chain.analyze_repository(
            owner=request.owner,
            repo=request.repo
        )
        
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        
        return result
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Repository analysis failed: {str(e)}")

