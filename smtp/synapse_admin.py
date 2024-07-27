import httpx
from config import admin_token
import logging

async def get_username(email):
    headers = {'Authorization': f"Bearer {admin_token}"}
    async with httpx.AsyncClient(headers=headers) as client:
        request = await client.get(
            f"https://matrix.spaceship.im/_synapse/admin/v1/threepid/email/users/{email}"
        )
    if request.status_code == 200:
        username = request.json()["user_id"]
        return username
    else:
        logging.warn(request.text)
        logging.warning(email)
    return None