from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import docker

app = FastAPI()

class DeployData(BaseModel):
    username: str
    env_vars: dict

client = docker.from_env()

@app.post("/deploy")
async def deploy(data: DeployData):
    try:
        image_name = ""
        if 'type' in data.env_vars:
            if data.env_vars['type'] == 'streaming':
                image_name = "agifm/multi_bot"
            else:
                image_name = "agifm/matrix_chatgpt_bot"
        else:
            raise HTTPException(status_code=400, detail="env_vars must contain 'type'")

        container_name = data.username

        # Check if the container already exists and remove it if necessary
        try:
            container = client.containers.get(container_name)
            container.stop()
            container.remove()
        except docker.errors.NotFound:
            pass

        # Create and start the new container
        container = client.containers.run(
            image_name,
            name=container_name,
            environment=data.env_vars,
            detach=True
        )

        return {"message": "Container deployed successfully", "container_id": container.id}

    except docker.errors.ImageNotFound:
        raise HTTPException(status_code=404, detail="Docker image not found")
    except docker.errors.DockerException as e:
        raise HTTPException(status_code=500, detail=f"Docker error: {str(e)}")

# Optional: Define a health check endpoint
@app.get("/health")
async def health():
    return {"status": "ok"}
