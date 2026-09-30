import httpx
from datetime import date
from app.auth import get_token


def _build_url(cliente: dict, fecha_inicio: str, fecha_fin: str) -> str:
    base = cliente["base_url"]
    mid  = cliente["membership_id"]
    eid  = cliente["endpoint_id"]
    return (
        f"{base}/memberships/{mid}/core/creditApp"
        f"/getSolitudesByTime/{eid}/{fecha_inicio}/{fecha_fin}"
    )


async def fetch_entrevistas(cliente: dict, fecha: date) -> list[dict]:
    token        = await get_token(cliente)
    fecha_str    = fecha.strftime("%Y-%m-%d")
    fecha_inicio = f"{fecha_str} 00:00:00"
    fecha_fin    = f"{fecha_str} 23:59:59"

    async with httpx.AsyncClient() as client:
        response = await client.get(
            _build_url(cliente, fecha_inicio, fecha_fin),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type":  "application/json",
            },
            timeout=30.0
        )

    response.raise_for_status()
    return response.json()  # Lista directa, confirmado


async def fetch_hoy_y_ayer(cliente: dict) -> dict[str, list[dict]]:
    hoy  = date.today()
    ayer = date.fromordinal(hoy.toordinal() - 1)
    return {
        "ayer": await fetch_entrevistas(cliente, ayer),
        "hoy":  await fetch_entrevistas(cliente, hoy),
    }