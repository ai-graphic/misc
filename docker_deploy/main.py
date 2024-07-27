from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import docker
import os

app = FastAPI()

class DeployData(BaseModel):
    username: str
    env_vars: dict

client = docker.from_env()

@app.post("/deploy")
async def deploy(data: DeployData):
    try:
        image_name = ""
        if data.env_vars['STREAMING'] == True and data.env_vars['TYPE'] == "WORKFLOW":
                image_name = "agifm/multi_bot"
        else:
                image_name = "agifm/matrix_chatgpt_bot"

        container_name = data.username

        # Check if the container already exists and remove it if necessary
        try:
            container = client.containers.get(container_name)
            container.stop()
            container.remove()
        except docker.errors.NotFound:
            pass

        # Define the volume source path and ensure the directory exists
        base_source_path = "/home/azureuser/app/keys"
        user_source_path = os.path.join(base_source_path, data.username)
        if not os.path.exists(user_source_path):
            os.makedirs(user_source_path)

        # Define the volume mapping
        volume_mapping = {
            user_source_path: {
                "bind": "/app/keys",
                "mode": "rw"
            }
        }

        # Create and start the new container with volume attached
        container = client.containers.run(
            image_name,
            name=container_name,
            environment=data.env_vars,
            volumes=volume_mapping,
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
