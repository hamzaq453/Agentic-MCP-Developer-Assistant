from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# GitHub Schemas
class CreateIssueRequest(BaseModel):
    """Request model for creating a GitHub issue."""
    repo_name: str = Field(..., description="Repository name in format 'owner/repo'")
    title: str = Field(..., min_length=1, max_length=256, description="Issue title")
    body: Optional[str] = Field(None, description="Issue body/description")
    labels: Optional[List[str]] = Field(default=None, description="List of labels to add")


class IssueResponse(BaseModel):
    """Response model for a GitHub issue."""
    number: int
    title: str
    state: str
    url: str
    created_at: datetime
    body: Optional[str] = None


class RepositoryInfo(BaseModel):
    """Repository information model."""
    name: str
    full_name: str
    description: Optional[str]
    stars: int
    forks: int
    open_issues: int
    language: Optional[str]
    url: str
    created_at: datetime
    updated_at: datetime


class RepositorySearchResult(BaseModel):
    """Search result for a repository."""
    name: str
    full_name: str
    description: Optional[str]
    stars: int
    forks: int
    language: Optional[str]
    url: str


class FileContentResponse(BaseModel):
    """Response model for file content."""
    path: str
    content: str
    size: int
    encoding: str
    url: str


class GitHubOperationResponse(BaseModel):
    """Generic response for GitHub operations."""
    status: str
    message: str
    data: Optional[dict] = None


# Docker Schemas
class ContainerInfo(BaseModel):
    """Docker container information."""
    id: str
    name: str
    status: str
    image: str
    created: Optional[str] = None
    ports: Optional[Dict[str, Any]] = None


class ContainerStats(BaseModel):
    """Docker container statistics."""
    container_id: str
    container_name: str
    cpu_percent: Optional[float] = None
    memory_usage: Optional[str] = None
    memory_limit: Optional[str] = None
    memory_percent: Optional[float] = None
    network_io: Optional[Dict[str, Any]] = None


class DeployServiceRequest(BaseModel):
    """Request to deploy a new container."""
    image: str = Field(..., description="Docker image name (e.g., 'nginx:latest')")
    name: Optional[str] = Field(None, description="Container name")
    ports: Optional[Dict[str, int]] = Field(None, description="Port mappings (e.g., {'80/tcp': 8080})")
    environment: Optional[Dict[str, str]] = Field(None, description="Environment variables")
    detach: bool = Field(True, description="Run container in background")


class DockerOperationResponse(BaseModel):
    """Generic response for Docker operations."""
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None


# Filesystem Schemas
class WriteFileRequest(BaseModel):
    """Request to write content to a file."""
    path: str = Field(..., description="File path")
    content: str = Field(..., description="File content")
    create_dirs: bool = Field(True, description="Create parent directories if they don't exist")


class FileInfo(BaseModel):
    """File information model."""
    name: str
    path: str
    size: int
    is_dir: bool
    is_file: bool
    modified: datetime
    created: Optional[datetime] = None
    permissions: Optional[str] = None


class DirectoryItem(BaseModel):
    """Directory item model."""
    name: str
    path: str
    is_dir: bool
    size: Optional[int] = None


class FileSystemOperationResponse(BaseModel):
    """Generic response for filesystem operations."""
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None


