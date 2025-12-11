from __future__ import annotations

from typing import Dict, Any, List
import logging

import httpx

from devices.base_device import Device


class IOTFacade:
    def __init__(self, timeout: float = 2.0) -> None:
        self._devices: Dict[str, Device] = {}
        self._timeout = timeout

    def register_device(self, device: Device) -> str:
        self._devices[device.device_id] = device
        logging.info(
            "Registered device %s at %s:%s",
            device.device_id,
            device.host,
            device.port,
        )
        return device.device_id

    def devices(self) -> Dict[str, Device]:
        return dict(self._devices)

    def _base_url(self, device: Device) -> str:
        return f"http://{device.host}:{device.port}"

    def get_device_status(self, device_id: str) -> Dict[str, Any] | None:
        device = self._devices.get(device_id)
        if not device:
            return None

        url = self._base_url(device) + "/status"
        try:
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.get(url)
            resp.raise_for_status()
            data = resp.json()
            data.setdefault("connection", f"{device.host}:{device.port}")
            return data
        except Exception as exc:
            logging.error("[FACADE] Error get_device_status(%s): %s", device_id, exc)
            return None

    def perform_device_action(self, device_id: str, action: str, **kwargs) -> bool:
        device = self._devices.get(device_id)
        if not device:
            return False

        base = self._base_url(device)
        try:
            with httpx.Client(timeout=self._timeout) as client:
                if action == "power":
                    state = kwargs["state"]
                    resp = client.post(f"{base}/power/{state}")
                elif action == "set_volume":
                    level = kwargs["level"]
                    resp = client.post(f"{base}/volume/{level}")
                elif action == "set_brightness":
                    level = kwargs["level"]
                    resp = client.post(f"{base}/brightness/{level}")
                elif action == "set_position":
                    value = kwargs["value"]
                    resp = client.post(f"{base}/position/{value}")
                else:
                    return False

            resp.raise_for_status()
            return True
        except Exception as exc:
            logging.error(
                "[FACADE] Error perform_device_action(%s, %s): %s",
                device_id,
                action,
                exc,
            )
            return False

    def get_all_status(self) -> List[Dict[str, Any]]:
        result: List[Dict[str, Any]] = []
        for device_id in list(self._devices.keys()):
            status = self.get_device_status(device_id)
            if status:
                result.append(status)
        return result
