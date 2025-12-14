from fastapi import FastAPI
from typing import List, Dict, Any


def get_mcp_tools_info() -> List[Dict[str, Any]]:
    """
    Return information about available MCP tools.
    Useful for debugging and documentation.
    """
    return [
        {
            "category": "GitHub",
            "tools": [
                "search_repositories",
                "get_repository_info",
                "create_issue",
                "list_issues",
                "get_file_content"
            ]
        },
        {
            "category": "Docker",
            "tools": [
                "list_containers",
                "start_container",
                "stop_container",
                "get_container_logs",
                "get_container_stats"
            ]
        },
        {
            "category": "Filesystem",
            "tools": [
                "read_file",
                "write_file",
                "list_directory",
                "search_files",
                "get_file_stats"
            ]
        }
    ]

