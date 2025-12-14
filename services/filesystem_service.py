from fastapi import APIRouter, HTTPException, Query
from typing import List
import os
import pathlib
from datetime import datetime
import glob
import stat
from schemas.models import (
    WriteFileRequest,
    FileInfo,
    DirectoryItem,
    FileSystemOperationResponse
)

router = APIRouter()

# Security: Define allowed base directories (for production, make this configurable)
ALLOWED_BASE_PATHS = [
    os.getcwd(),  # Current working directory
    os.path.expanduser("~")  # User home directory
]


def is_path_safe(path: str) -> bool:
    """Check if the path is within allowed directories."""
    abs_path = os.path.abspath(path)
    return any(abs_path.startswith(os.path.abspath(base)) for base in ALLOWED_BASE_PATHS)


def validate_path(path: str) -> str:
    """Validate and return absolute path."""
    abs_path = os.path.abspath(path)
    if not is_path_safe(abs_path):
        raise HTTPException(
            status_code=403,
            detail="Access to this path is forbidden. Path must be within allowed directories."
        )
    return abs_path


@router.get(
    "/read",
    response_model=FileSystemOperationResponse,
    summary="Read File",
    description="Read content from a file"
)
async def read_file(
    path: str = Query(..., description="Path to the file to read")
) -> FileSystemOperationResponse:
    """Read file content."""
    try:
        file_path = validate_path(path)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"File not found: {path}")
        
        if not os.path.isfile(file_path):
            raise HTTPException(status_code=400, detail=f"Path is not a file: {path}")
        
        # Try to read as text
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=400,
                detail="File is not a text file or uses unsupported encoding"
            )
        
        file_stats = os.stat(file_path)
        
        return FileSystemOperationResponse(
            status="success",
            message=f"File read successfully: {path}",
            data={
                "path": path,
                "content": content,
                "size": file_stats.st_size,
                "modified": datetime.fromtimestamp(file_stats.st_mtime).isoformat()
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")


@router.post(
    "/write",
    response_model=FileSystemOperationResponse,
    summary="Write File",
    description="Create or update a file with content"
)
async def write_file(request: WriteFileRequest) -> FileSystemOperationResponse:
    """Write content to a file."""
    try:
        file_path = validate_path(request.path)
        
        # Create parent directories if requested
        if request.create_dirs:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Write file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(request.content)
        
        file_stats = os.stat(file_path)
        
        return FileSystemOperationResponse(
            status="success",
            message=f"File written successfully: {request.path}",
            data={
                "path": request.path,
                "size": file_stats.st_size,
                "bytes_written": len(request.content.encode('utf-8'))
            }
        )
    
    except HTTPException:
        raise
    except PermissionError:
        raise HTTPException(status_code=403, detail=f"Permission denied: {request.path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error writing file: {str(e)}")


@router.get(
    "/list",
    response_model=List[DirectoryItem],
    summary="List Directory",
    description="List contents of a directory"
)
async def list_directory(
    path: str = Query(".", description="Path to the directory to list"),
    show_hidden: bool = Query(False, description="Show hidden files (starting with .)")
) -> List[DirectoryItem]:
    """List directory contents."""
    try:
        dir_path = validate_path(path)
        
        if not os.path.exists(dir_path):
            raise HTTPException(status_code=404, detail=f"Directory not found: {path}")
        
        if not os.path.isdir(dir_path):
            raise HTTPException(status_code=400, detail=f"Path is not a directory: {path}")
        
        items = []
        for item_name in os.listdir(dir_path):
            # Skip hidden files if not requested
            if not show_hidden and item_name.startswith('.'):
                continue
            
            item_path = os.path.join(dir_path, item_name)
            is_dir = os.path.isdir(item_path)
            
            size = None
            if not is_dir:
                try:
                    size = os.path.getsize(item_path)
                except:
                    pass
            
            items.append(DirectoryItem(
                name=item_name,
                path=item_path,
                is_dir=is_dir,
                size=size
            ))
        
        # Sort: directories first, then files, both alphabetically
        items.sort(key=lambda x: (not x.is_dir, x.name.lower()))
        
        return items
    
    except HTTPException:
        raise
    except PermissionError:
        raise HTTPException(status_code=403, detail=f"Permission denied: {path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing directory: {str(e)}")


@router.get(
    "/search",
    response_model=List[DirectoryItem],
    summary="Search Files",
    description="Search for files by pattern (supports wildcards)"
)
async def search_files(
    pattern: str = Query(..., description="Search pattern (supports * and ? wildcards)"),
    directory: str = Query(".", description="Directory to search in"),
    recursive: bool = Query(False, description="Search recursively in subdirectories")
) -> List[DirectoryItem]:
    """Search for files matching a pattern."""
    try:
        dir_path = validate_path(directory)
        
        if not os.path.exists(dir_path):
            raise HTTPException(status_code=404, detail=f"Directory not found: {directory}")
        
        if not os.path.isdir(dir_path):
            raise HTTPException(status_code=400, detail=f"Path is not a directory: {directory}")
        
        # Build search pattern
        if recursive:
            search_pattern = os.path.join(dir_path, "**", pattern)
        else:
            search_pattern = os.path.join(dir_path, pattern)
        
        # Find matching files
        matches = glob.glob(search_pattern, recursive=recursive)
        
        items = []
        for match_path in matches:
            # Validate each match is still in allowed paths
            if not is_path_safe(match_path):
                continue
            
            is_dir = os.path.isdir(match_path)
            size = None
            
            if not is_dir:
                try:
                    size = os.path.getsize(match_path)
                except:
                    pass
            
            items.append(DirectoryItem(
                name=os.path.basename(match_path),
                path=match_path,
                is_dir=is_dir,
                size=size
            ))
        
        return items
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching files: {str(e)}")


@router.get(
    "/stats",
    response_model=FileInfo,
    summary="Get File Statistics",
    description="Get detailed information about a file or directory"
)
async def get_file_stats(
    path: str = Query(..., description="Path to the file or directory")
) -> FileInfo:
    """Get file or directory statistics."""
    try:
        file_path = validate_path(path)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"Path not found: {path}")
        
        stats = os.stat(file_path)
        
        # Get permissions in octal format
        permissions = oct(stat.S_IMODE(stats.st_mode))
        
        return FileInfo(
            name=os.path.basename(file_path),
            path=file_path,
            size=stats.st_size,
            is_dir=os.path.isdir(file_path),
            is_file=os.path.isfile(file_path),
            modified=datetime.fromtimestamp(stats.st_mtime),
            created=datetime.fromtimestamp(stats.st_ctime),
            permissions=permissions
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting file stats: {str(e)}")

