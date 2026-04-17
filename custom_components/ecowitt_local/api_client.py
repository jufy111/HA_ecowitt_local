"""API client for Ecowitt Gateway local HTTP API."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp

from .const import (
    ENDPOINT_LIVEDATA,
    ENDPOINT_IOT_CMD,
    ENDPOINT_IOT_DEVICE_LIST,
    VAL_TYPE_TIME,
    VAL_TYPE_VOLUME,
)

_LOGGER = logging.getLogger(__name__)


class EcowittApiError(Exception):
    """Base exception for API errors."""


class EcowittConnectionError(EcowittApiError):
    """Connection failed."""


class EcowittApiClient:
    """Async HTTP client for Ecowitt gateway."""

    def __init__(
        self,
        host: str,
        port: int = 80,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        self._base_url = f"http://{host}:{port}"
        self._session = session
        self._owns_session = session is None

    @property
    def base_url(self) -> str:
        return self._base_url

    # ── GET: Live sensor data ────────────────────────────
    async def async_get_livedata(self) -> dict[str, Any]:
        return await self._request("GET", ENDPOINT_LIVEDATA)

    # ── GET: Discover IoT devices ────────────────────────
    async def async_get_iot_device_list(self) -> list[dict[str, Any]]:
        result = await self._request("GET", ENDPOINT_IOT_DEVICE_LIST)
        return result.get("command", [])

    # ── POST: Read IoT device status ─────────────────────
    async def async_read_iot_device(
        self, device_id: int, model: int = 1
    ) -> dict[str, Any]:
        payload = {
            "command": [{"cmd": "read_device", "id": device_id, "model": model}]
        }
        result = await self._request("POST", ENDPOINT_IOT_CMD, json_data=payload)
        commands = result.get("command", [])
        return commands[0] if commands else {}

    # ── Valve: Open indefinitely ─────────────────────────
    async def async_valve_open(
        self, device_id: int, model: int = 1
    ) -> dict[str, Any]:
        payload = self._build_quick_run(
            device_id=device_id, model=model,
            always_on=1, val_type=VAL_TYPE_TIME, val=0,
        )
        return await self._request("POST", ENDPOINT_IOT_CMD, json_data=payload)

    # ── Valve: Open for N minutes ────────────────────────
    async def async_valve_open_for_minutes(
        self,
        device_id: int,
        minutes: int,
        model: int = 1,
        on_time: int = 0,
        off_time: int = 0,
    ) -> dict[str, Any]:
        payload = self._build_quick_run(
            device_id=device_id, model=model,
            always_on=0, val_type=VAL_TYPE_TIME, val=minutes,
            on_time=on_time, off_time=off_time,
        )
        return await self._request("POST", ENDPOINT_IOT_CMD, json_data=payload)

    # ── Valve: Open for N litres ─────────────────────────
    async def async_valve_open_for_litres(
        self,
        device_id: int,
        litres: float,
        model: int = 1,
        on_time: int = 0,
        off_time: int = 0,
    ) -> dict[str, Any]:
        decilitres = int(litres * 10)
        payload = self._build_quick_run(
            device_id=device_id, model=model,
            always_on=0, val_type=VAL_TYPE_VOLUME, val=decilitres,
            on_time=on_time, off_time=off_time,
        )
        return await self._request("POST", ENDPOINT_IOT_CMD, json_data=payload)

    # ── Valve: Close / Stop ──────────────────────────────
    async def async_valve_close(
        self, device_id: int, model: int = 1
    ) -> dict[str, Any]:
        payload = {
            "command": [{"cmd": "quick_stop", "id": device_id, "model": model}]
        }
        return await self._request("POST", ENDPOINT_IOT_CMD, json_data=payload)

    # ── Build quick_run payload ──────────────────────────
    @staticmethod
    def _build_quick_run(
        device_id: int,
        model: int,
        always_on: int,
        val_type: int,
        val: int,
        on_time: int = 0,
        off_time: int = 0,
    ) -> dict:
        return {
            "command": [
                {
                    "cmd": "quick_run",
                    "id": device_id,
                    "model": model,
                    "on_type": 0,
                    "off_type": 0,
                    "always_on": always_on,
                    "on_time": on_time,
                    "off_time": off_time,
                    "val_type": val_type,
                    "val": val,
                }
            ]
        }

    # ── Core HTTP handler ────────────────────────────────
    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: dict | None = None,
    ) -> dict[str, Any]:
        url = f"{self._base_url}{endpoint}"

        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
            self._owns_session = True

        try:
            _LOGGER.debug("%s %s body=%s", method, url, json_data)
            async with self._session.request(
                method, url, json=json_data,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                resp.raise_for_status()
                _LOGGER.debug("%s %s → %s", method, url, resp.status)
                text = await resp.text()
                try:
                    import json
                    return json.loads(text)
                except (ValueError, TypeError):
                    _LOGGER.debug("Non-JSON response from %s: %s", url, text)
                    return {}
        except aiohttp.ClientResponseError as err:
            _LOGGER.error("HTTP error %s %s: %s", method, url, err.status)
            raise EcowittApiError(f"HTTP {err.status}") from err
        except (aiohttp.ClientError, TimeoutError) as err:
            _LOGGER.error("Connection error %s %s: %s", method, url, err)
            raise EcowittConnectionError(str(err)) from err

    async def async_close(self) -> None:
        if self._owns_session and self._session and not self._session.closed:
            await self._session.close()