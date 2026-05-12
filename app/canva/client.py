import asyncio

import httpx

CANVA_API_BASE = "https://api.canva.com/rest/v1"

POLL_INTERVAL_SECONDS = 1.5
MAX_POLL_ATTEMPTS = 60


class CanvaApiError(Exception):
    pass


class CanvaClient:
    def __init__(self, access_token: str):
        self._headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    async def autofill_brand_template(
        self, brand_template_id: str, data: dict[str, str]
    ) -> str:
        payload = {
            "brand_template_id": brand_template_id,
            "data": {key: {"type": "text", "text": value} for key, value in data.items()},
        }
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{CANVA_API_BASE}/autofills", json=payload, headers=self._headers
            )
            if resp.status_code >= 400:
                raise CanvaApiError(f"Autofill request failed: {resp.status_code} {resp.text}")
            job = resp.json()["job"]
            job_id = job["id"]

            design_id = await self._poll_autofill(client, job_id)
            return design_id

    async def _poll_autofill(self, client: httpx.AsyncClient, job_id: str) -> str:
        for _ in range(MAX_POLL_ATTEMPTS):
            await asyncio.sleep(POLL_INTERVAL_SECONDS)
            resp = await client.get(
                f"{CANVA_API_BASE}/autofills/{job_id}", headers=self._headers
            )
            resp.raise_for_status()
            job = resp.json()["job"]
            status = job.get("status")
            if status == "success":
                return job["result"]["design"]["id"]
            if status == "failed":
                raise CanvaApiError(f"Autofill job failed: {job.get('error')}")
        raise CanvaApiError("Autofill job timed out")

    async def export_design_as_pdf(self, design_id: str) -> list[str]:
        payload = {
            "design_id": design_id,
            "format": {"type": "pdf"},
        }
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{CANVA_API_BASE}/exports", json=payload, headers=self._headers
            )
            if resp.status_code >= 400:
                raise CanvaApiError(f"Export request failed: {resp.status_code} {resp.text}")
            job = resp.json()["job"]
            job_id = job["id"]
            return await self._poll_export(client, job_id)

    async def _poll_export(self, client: httpx.AsyncClient, job_id: str) -> list[str]:
        for _ in range(MAX_POLL_ATTEMPTS):
            await asyncio.sleep(POLL_INTERVAL_SECONDS)
            resp = await client.get(
                f"{CANVA_API_BASE}/exports/{job_id}", headers=self._headers
            )
            resp.raise_for_status()
            job = resp.json()["job"]
            status = job.get("status")
            if status == "success":
                return [url["url"] for url in job["urls"]]
            if status == "failed":
                raise CanvaApiError(f"Export job failed: {job.get('error')}")
        raise CanvaApiError("Export job timed out")


async def download_pdf(url: str, destination) -> None:
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        destination.write(resp.content)
