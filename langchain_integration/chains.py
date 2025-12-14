from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import Dict, Any, Optional
from config.settings import settings
import requests


class CodeAnalysisChain:
    """LangChain chain for analyzing code from GitHub repositories."""
    
    def __init__(self, temperature: float = 0.3):
        """
        Initialize the code analysis chain.
        
        Args:
            temperature: LLM temperature for code analysis
        """
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY not configured")
        
        self.llm = ChatOpenAI(
            temperature=temperature,
            model="gpt-4",
            openai_api_key=settings.openai_api_key
        )
        
        # Code analysis prompt
        self.analysis_prompt = PromptTemplate(
            input_variables=["code", "file_path", "language"],
            template="""You are an expert code reviewer. Analyze the following code and provide:

1. Code Quality Assessment (1-10)
2. Key Issues or Problems
3. Security Concerns (if any)
4. Performance Considerations
5. Best Practices Violations
6. Suggestions for Improvement

File: {file_path}
Language: {language}

Code:
```
{code}
```

Provide a detailed analysis:"""
        )
        
        # Create the chain
        self.chain = self.analysis_prompt | self.llm | StrOutputParser()
    
    def analyze_file(self, owner: str, repo: str, file_path: str, branch: str = "main") -> Dict[str, Any]:
        """
        Analyze a file from a GitHub repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            file_path: Path to the file in the repository
            branch: Branch name (default: main)
            
        Returns:
            Dict with analysis results
        """
        try:
            # Fetch file from GitHub
            file_content = self._fetch_github_file(owner, repo, file_path, branch)
            
            if "error" in file_content:
                return {
                    "status": "error",
                    "message": file_content["error"]
                }
            
            # Detect language from file extension
            language = self._detect_language(file_path)
            
            # Run analysis
            analysis = self.chain.invoke({
                "code": file_content["content"],
                "file_path": file_path,
                "language": language
            })
            
            return {
                "status": "success",
                "repository": f"{owner}/{repo}",
                "file_path": file_path,
                "language": language,
                "file_size": file_content.get("size", 0),
                "analysis": analysis
            }
        
        except Exception as e:
            return {
                "status": "error",
                "message": f"Analysis failed: {str(e)}"
            }
    
    def _fetch_github_file(self, owner: str, repo: str, file_path: str, branch: str) -> Dict[str, Any]:
        """Fetch file content from GitHub via the MCP server."""
        try:
            url = f"http://localhost:8000/github/file/{owner}/{repo}"
            params = {"path": file_path, "branch": branch}
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return {
                "content": data.get("content", ""),
                "size": data.get("size", 0)
            }
        
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to fetch file: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        extension_map = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".jsx": "React JSX",
            ".tsx": "React TSX",
            ".java": "Java",
            ".go": "Go",
            ".rs": "Rust",
            ".cpp": "C++",
            ".c": "C",
            ".cs": "C#",
            ".rb": "Ruby",
            ".php": "PHP",
            ".swift": "Swift",
            ".kt": "Kotlin",
            ".sh": "Shell",
            ".sql": "SQL",
            ".html": "HTML",
            ".css": "CSS",
            ".json": "JSON",
            ".yaml": "YAML",
            ".yml": "YAML",
            ".md": "Markdown"
        }
        
        for ext, lang in extension_map.items():
            if file_path.lower().endswith(ext):
                return lang
        
        return "Unknown"


class RepositoryAnalysisChain:
    """Chain for analyzing entire repositories."""
    
    def __init__(self, temperature: float = 0.3):
        """Initialize repository analysis chain."""
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY not configured")
        
        self.llm = ChatOpenAI(
            temperature=temperature,
            model="gpt-4",
            openai_api_key=settings.openai_api_key
        )
        
        self.analysis_prompt = PromptTemplate(
            input_variables=["repo_info", "readme_content"],
            template="""Analyze the following GitHub repository and provide insights:

Repository Information:
{repo_info}

README Content:
{readme_content}

Provide:
1. Project Purpose and Use Case
2. Technology Stack
3. Code Quality Indicators (based on metadata)
4. Community Health (stars, forks, issues)
5. Potential Use Cases
6. Recommendations for Contributors

Analysis:"""
        )
        
        self.chain = self.analysis_prompt | self.llm | StrOutputParser()
    
    def analyze_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Analyze a GitHub repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Dict with repository analysis
        """
        try:
            # Fetch repository info
            repo_info = self._fetch_repo_info(owner, repo)
            
            if "error" in repo_info:
                return {
                    "status": "error",
                    "message": repo_info["error"]
                }
            
            # Try to fetch README
            readme_content = self._fetch_readme(owner, repo)
            
            # Run analysis
            analysis = self.chain.invoke({
                "repo_info": str(repo_info),
                "readme_content": readme_content
            })
            
            return {
                "status": "success",
                "repository": f"{owner}/{repo}",
                "analysis": analysis
            }
        
        except Exception as e:
            return {
                "status": "error",
                "message": f"Repository analysis failed: {str(e)}"
            }
    
    def _fetch_repo_info(self, owner: str, repo: str) -> Dict[str, Any]:
        """Fetch repository information via MCP server."""
        try:
            url = f"http://localhost:8000/github/repo/{owner}/{repo}"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": f"Failed to fetch repository info: {str(e)}"}
    
    def _fetch_readme(self, owner: str, repo: str) -> str:
        """Fetch README content."""
        readme_files = ["README.md", "readme.md", "README.MD", "Readme.md"]
        
        for readme_file in readme_files:
            try:
                url = f"http://localhost:8000/github/file/{owner}/{repo}"
                params = {"path": readme_file}
                response = requests.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("content", "No README content available")
            except:
                continue
        
        return "No README file found"


# Singleton instances
_code_analysis_chain: Optional[CodeAnalysisChain] = None
_repo_analysis_chain: Optional[RepositoryAnalysisChain] = None


def get_code_analysis_chain() -> CodeAnalysisChain:
    """Get or create code analysis chain instance."""
    global _code_analysis_chain
    if _code_analysis_chain is None:
        _code_analysis_chain = CodeAnalysisChain()
    return _code_analysis_chain


def get_repo_analysis_chain() -> RepositoryAnalysisChain:
    """Get or create repository analysis chain instance."""
    global _repo_analysis_chain
    if _repo_analysis_chain is None:
        _repo_analysis_chain = RepositoryAnalysisChain()
    return _repo_analysis_chain

