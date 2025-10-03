from typing import Any, Dict, Optional

import aiohttp
from loguru import logger


class RefeeApiError(Exception):
    def __init__(self, status: int, message: str, payload: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(f"API error {status}: {message}")
        self.status = status
        self.payload = payload or {}


class RefeeApiClient:
    def __init__(self, api_key: str, base_url: str = "https://api.refee.bot") -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _request(self, method: str, path: str, json: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self._base_url}{path}"
        logger.debug("RefeeAPI {method} {url} json={json}", method=method, url=url, json=json)
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, headers=self._headers(), json=json) as resp:
                try:
                    data = await resp.json(content_type=None)
                except Exception:  # pragma: no cover
                    text = await resp.text()
                    raise RefeeApiError(resp.status, f"Invalid JSON response: {text[:200]}")
                if resp.status >= 400:
                    message = data.get("message") or data.get("error") or str(data)
                    raise RefeeApiError(resp.status, message, data)
                return data  # type: ignore[return-value]

    # Public endpoints wrappers
    async def precount_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Expected to calculate energy order cost based on transfer params
        return await self._request("POST", "/precountOrder", json=payload)

    async def precount_bandwidth(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self._request("POST", "/precountBandwidth", json=payload)

    async def buy_energy(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Example payload could include: ownerAddress, energyAmount, comments
        return await self._request("POST", "/buyenergy", json=payload)

    async def buy_bandwidth(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self._request("POST", "/buybandwidth", json=payload)

