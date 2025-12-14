from fastapi import APIRouter, HTTPException, Query
from github import Github, GithubException
from typing import List, Optional
import base64
from config.settings import settings
from schemas.models import (
    CreateIssueRequest,
    IssueResponse,
    RepositoryInfo,
    RepositorySearchResult,
    FileContentResponse,
    GitHubOperationResponse
)

router = APIRouter()


def get_github_client() -> Github:
    """Get authenticated GitHub client."""
    if not settings.github_token:
        raise HTTPException(
            status_code=401,
            detail="GitHub token not configured. Set GITHUB_TOKEN environment variable."
        )
    return Github(settings.github_token)


@router.get(
    "/search-repos",
    response_model=List[RepositorySearchResult],
    summary="Search GitHub Repositories",
    description="Search for repositories on GitHub by keyword"
)
async def search_repositories(
    query: str = Query(..., description="Search query"),
    max_results: int = Query(5, ge=1, le=20, description="Maximum number of results to return")
) -> List[RepositorySearchResult]:
    """Search GitHub repositories by keyword."""
    try:
        g = get_github_client()
        repos = g.search_repositories(query=query, sort="stars", order="desc")
        
        results = []
        for repo in repos[:max_results]:
            results.append(RepositorySearchResult(
                name=repo.name,
                full_name=repo.full_name,
                description=repo.description,
                stars=repo.stargazers_count,
                forks=repo.forks_count,
                language=repo.language,
                url=repo.html_url
            ))
        
        return results
    
    except GithubException as e:
        raise HTTPException(status_code=e.status, detail=f"GitHub API error: {e.data.get('message', str(e))}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching repositories: {str(e)}")


@router.get(
    "/repo/{owner}/{repo}",
    response_model=RepositoryInfo,
    summary="Get Repository Information",
    description="Get detailed information about a specific repository"
)
async def get_repository_info(
    owner: str,
    repo: str
) -> RepositoryInfo:
    """Get detailed repository information."""
    try:
        g = get_github_client()
        repository = g.get_repo(f"{owner}/{repo}")
        
        return RepositoryInfo(
            name=repository.name,
            full_name=repository.full_name,
            description=repository.description,
            stars=repository.stargazers_count,
            forks=repository.forks_count,
            open_issues=repository.open_issues_count,
            language=repository.language,
            url=repository.html_url,
            created_at=repository.created_at,
            updated_at=repository.updated_at
        )
    
    except GithubException as e:
        if e.status == 404:
            raise HTTPException(status_code=404, detail=f"Repository {owner}/{repo} not found")
        raise HTTPException(status_code=e.status, detail=f"GitHub API error: {e.data.get('message', str(e))}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching repository info: {str(e)}")


@router.post(
    "/issues",
    response_model=GitHubOperationResponse,
    summary="Create GitHub Issue",
    description="Create a new issue in a repository"
)
async def create_issue(request: CreateIssueRequest) -> GitHubOperationResponse:
    """Create a new issue in a repository."""
    try:
        g = get_github_client()
        repo = g.get_repo(request.repo_name)
        
        issue = repo.create_issue(
            title=request.title,
            body=request.body,
            labels=request.labels or []
        )
        
        return GitHubOperationResponse(
            status="success",
            message=f"Issue #{issue.number} created successfully",
            data={
                "issue_number": issue.number,
                "issue_url": issue.html_url,
                "state": issue.state
            }
        )
    
    except GithubException as e:
        if e.status == 404:
            raise HTTPException(status_code=404, detail=f"Repository {request.repo_name} not found")
        raise HTTPException(status_code=e.status, detail=f"GitHub API error: {e.data.get('message', str(e))}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating issue: {str(e)}")


@router.get(
    "/issues/{owner}/{repo}",
    response_model=List[IssueResponse],
    summary="List Repository Issues",
    description="Get a list of issues from a repository"
)
async def list_issues(
    owner: str,
    repo: str,
    state: str = Query("open", regex="^(open|closed|all)$", description="Issue state filter"),
    max_results: int = Query(10, ge=1, le=50, description="Maximum number of issues to return")
) -> List[IssueResponse]:
    """List issues from a repository."""
    try:
        g = get_github_client()
        repository = g.get_repo(f"{owner}/{repo}")
        
        issues = repository.get_issues(state=state)
        
        results = []
        for issue in issues[:max_results]:
            # Skip pull requests (they appear in issues API)
            if issue.pull_request:
                continue
                
            results.append(IssueResponse(
                number=issue.number,
                title=issue.title,
                state=issue.state,
                url=issue.html_url,
                created_at=issue.created_at,
                body=issue.body
            ))
        
        return results
    
    except GithubException as e:
        if e.status == 404:
            raise HTTPException(status_code=404, detail=f"Repository {owner}/{repo} not found")
        raise HTTPException(status_code=e.status, detail=f"GitHub API error: {e.data.get('message', str(e))}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing issues: {str(e)}")


@router.get(
    "/file/{owner}/{repo}",
    response_model=FileContentResponse,
    summary="Get File Content",
    description="Get the content of a file from a repository"
)
async def get_file_content(
    owner: str,
    repo: str,
    path: str = Query(..., description="File path in the repository"),
    branch: str = Query("main", description="Branch name (default: main)")
) -> FileContentResponse:
    """Get file content from a repository."""
    try:
        g = get_github_client()
        repository = g.get_repo(f"{owner}/{repo}")
        
        try:
            file_content = repository.get_contents(path, ref=branch)
        except GithubException as e:
            if e.status == 404:
                # Try 'master' branch if 'main' fails
                if branch == "main":
                    try:
                        file_content = repository.get_contents(path, ref="master")
                        branch = "master"
                    except:
                        raise HTTPException(
                            status_code=404,
                            detail=f"File '{path}' not found in repository"
                        )
                else:
                    raise HTTPException(
                        status_code=404,
                        detail=f"File '{path}' not found in branch '{branch}'"
                    )
            else:
                raise
        
        # Decode content
        if file_content.encoding == "base64":
            content = base64.b64decode(file_content.content).decode('utf-8')
        else:
            content = file_content.decoded_content.decode('utf-8')
        
        return FileContentResponse(
            path=file_content.path,
            content=content,
            size=file_content.size,
            encoding=file_content.encoding,
            url=file_content.html_url
        )
    
    except GithubException as e:
        if e.status == 404:
            raise HTTPException(status_code=404, detail=f"Repository {owner}/{repo} not found")
        raise HTTPException(status_code=e.status, detail=f"GitHub API error: {e.data.get('message', str(e))}")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File is not a text file or uses unsupported encoding")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching file content: {str(e)}")

