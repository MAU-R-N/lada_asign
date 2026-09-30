import httpx
from datetime import datetime, timedelta

_token_cache: dict[str, dict] = {}


async def get_token(cliente: dict) -> str:
    cliente_id = cliente["id"]
    ahora = datetime.utcnow()

    if cliente_id in _token_cache:
        cached = _token_cache[cliente_id]
        if ahora < cached["expira_en"]:
            return cached["access_token"]

    return await _login(cliente)


async def _login(cliente: dict) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{cliente['base_url']}/auth/oauth/token",
            headers={"Authorization": "Basic TkFVUEhJTFVTOnNlY3JldA=="},
            data={
                "username":   cliente["username"],
                "password":   cliente["password"],
                "grant_type": "password",
            }
        )
    response.raise_for_status()
    return _guardar_token(cliente["id"], response.json())


def _guardar_token(cliente_id: str, data: dict) -> str:
    _token_cache[cliente_id] = {
        "access_token": data["access_token"],
        "expira_en":    datetime.utcnow() + timedelta(seconds=data["expires_in"] - 60)
    }
    return data["access_token"]