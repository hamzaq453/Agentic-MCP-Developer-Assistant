from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import docker
from docker.errors import DockerException, NotFound, APIError
from schemas.models import (
    ContainerInfo,
    ContainerStats,
    DeployServiceRequest,
    DockerOperationResponse
)

router = APIRouter()


def get_docker_client():
    """Get Docker client with error handling."""
    try:
        client = docker.from_env()
        # Test connection
        client.ping()
        return client
    except DockerException as e:
        raise HTTPException(
            status_code=503,
            detail=f"Docker is not available or not running: {str(e)}"
        )


@router.get(
    "/containers",
    response_model=List[ContainerInfo],
    summary="List Docker Containers",
    description="List all Docker containers (running and stopped)"
)
async def list_containers(
    all: bool = Query(True, description="Show all containers (default: True). False shows only running containers")
) -> List[ContainerInfo]:
    """List all Docker containers."""
    try:
        client = get_docker_client()
        containers = client.containers.list(all=all)
        
        result = []
        for container in containers:
            result.append(ContainerInfo(
                id=container.short_id,
                name=container.name,
                status=container.status,
                image=container.image.tags[0] if container.image.tags else container.image.short_id,
                created=container.attrs.get('Created'),
                ports=container.attrs.get('NetworkSettings', {}).get('Ports')
            ))
        
        return result
    
    except DockerException as e:
        raise HTTPException(status_code=500, detail=f"Docker error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing containers: {str(e)}")


@router.post(
    "/containers/{container_id}/start",
    response_model=DockerOperationResponse,
    summary="Start Container",
    description="Start a stopped Docker container"
)
async def start_container(container_id: str) -> DockerOperationResponse:
    """Start a Docker container."""
    try:
        client = get_docker_client()
        container = client.containers.get(container_id)
        
        if container.status == "running":
            return DockerOperationResponse(
                status="info",
                message=f"Container {container_id} is already running",
                data={"container_id": container.short_id, "status": container.status}
            )
        
        container.start()
        container.reload()
        
        return DockerOperationResponse(
            status="success",
            message=f"Container {container_id} started successfully",
            data={"container_id": container.short_id, "status": container.status}
        )
    
    except NotFound:
        raise HTTPException(status_code=404, detail=f"Container {container_id} not found")
    except APIError as e:
        raise HTTPException(status_code=400, detail=f"Docker API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting container: {str(e)}")


@router.post(
    "/containers/{container_id}/stop",
    response_model=DockerOperationResponse,
    summary="Stop Container",
    description="Stop a running Docker container"
)
async def stop_container(
    container_id: str,
    timeout: int = Query(10, ge=0, le=60, description="Timeout in seconds to wait before killing the container")
) -> DockerOperationResponse:
    """Stop a Docker container."""
    try:
        client = get_docker_client()
        container = client.containers.get(container_id)
        
        if container.status != "running":
            return DockerOperationResponse(
                status="info",
                message=f"Container {container_id} is not running (status: {container.status})",
                data={"container_id": container.short_id, "status": container.status}
            )
        
        container.stop(timeout=timeout)
        container.reload()
        
        return DockerOperationResponse(
            status="success",
            message=f"Container {container_id} stopped successfully",
            data={"container_id": container.short_id, "status": container.status}
        )
    
    except NotFound:
        raise HTTPException(status_code=404, detail=f"Container {container_id} not found")
    except APIError as e:
        raise HTTPException(status_code=400, detail=f"Docker API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stopping container: {str(e)}")


@router.get(
    "/containers/{container_id}/logs",
    response_model=DockerOperationResponse,
    summary="Get Container Logs",
    description="Retrieve logs from a Docker container"
)
async def get_container_logs(
    container_id: str,
    tail: int = Query(100, ge=1, le=1000, description="Number of lines to show from the end of the logs"),
    timestamps: bool = Query(False, description="Show timestamps in logs")
) -> DockerOperationResponse:
    """Get logs from a Docker container."""
    try:
        client = get_docker_client()
        container = client.containers.get(container_id)
        
        logs = container.logs(
            tail=tail,
            timestamps=timestamps
        ).decode('utf-8', errors='replace')
        
        return DockerOperationResponse(
            status="success",
            message=f"Retrieved logs for container {container_id}",
            data={
                "container_id": container.short_id,
                "container_name": container.name,
                "logs": logs,
                "lines": len(logs.split('\n'))
            }
        )
    
    except NotFound:
        raise HTTPException(status_code=404, detail=f"Container {container_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting logs: {str(e)}")


@router.get(
    "/containers/{container_id}/stats",
    response_model=ContainerStats,
    summary="Get Container Statistics",
    description="Get CPU, memory, and network statistics for a container"
)
async def get_container_stats(container_id: str) -> ContainerStats:
    """Get container statistics."""
    try:
        client = get_docker_client()
        container = client.containers.get(container_id)
        
        if container.status != "running":
            raise HTTPException(
                status_code=400,
                detail=f"Container {container_id} is not running. Stats are only available for running containers."
            )
        
        # Get stats (stream=False for single snapshot)
        stats = container.stats(stream=False)
        
        # Calculate CPU percentage
        cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                   stats['precpu_stats']['cpu_usage']['total_usage']
        system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                      stats['precpu_stats']['system_cpu_usage']
        cpu_percent = (cpu_delta / system_delta) * len(stats['cpu_stats']['cpu_usage']['percpu_usage']) * 100.0 if system_delta > 0 else 0.0
        
        # Calculate memory usage
        memory_usage = stats['memory_stats'].get('usage', 0)
        memory_limit = stats['memory_stats'].get('limit', 0)
        memory_percent = (memory_usage / memory_limit * 100.0) if memory_limit > 0 else 0.0
        
        return ContainerStats(
            container_id=container.short_id,
            container_name=container.name,
            cpu_percent=round(cpu_percent, 2),
            memory_usage=f"{memory_usage / (1024**2):.2f} MB",
            memory_limit=f"{memory_limit / (1024**2):.2f} MB",
            memory_percent=round(memory_percent, 2),
            network_io=stats.get('networks', {})
        )
    
    except NotFound:
        raise HTTPException(status_code=404, detail=f"Container {container_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")


@router.post(
    "/deploy",
    response_model=DockerOperationResponse,
    summary="Deploy Service",
    description="Start a new container from a Docker image"
)
async def deploy_service(request: DeployServiceRequest) -> DockerOperationResponse:
    """Deploy a new service by creating and starting a container."""
    try:
        client = get_docker_client()
        
        # Try to pull the image if not available locally
        try:
            client.images.get(request.image)
        except NotFound:
            try:
                client.images.pull(request.image)
            except Exception as pull_error:
                raise HTTPException(
                    status_code=400,
                    detail=f"Image '{request.image}' not found locally and could not be pulled: {str(pull_error)}"
                )
        
        # Create and start container
        container = client.containers.run(
            image=request.image,
            name=request.name,
            ports=request.ports,
            environment=request.environment,
            detach=request.detach
        )
        
        return DockerOperationResponse(
            status="success",
            message=f"Service deployed successfully from image {request.image}",
            data={
                "container_id": container.short_id,
                "container_name": container.name,
                "image": request.image,
                "status": container.status
            }
        )
    
    except APIError as e:
        raise HTTPException(status_code=400, detail=f"Docker API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deploying service: {str(e)}")

