from __future__ import annotations

from typing import Dict, Any

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from devices.base_device import Device


class LightState(BaseModel):
    is_on: bool = False
    brightness: int = 50


class SmartLightDevice(Device):
    def __init__(self, device_id: str, host: str = "127.0.0.1", port: int = 8002) -> None:
        super().__init__(device_id, host, port)
        self.state = LightState()
        self.app = FastAPI(title=f"Smart Light {device_id}")
        self._setup_routes()

    def _setup_routes(self) -> None:
        app = self.app

        @app.get("/status")
        async def get_status() -> Dict[str, Any]:
            return self.get_status()

        @app.post("/power/{state}")
        async def set_power(state: str) -> Dict[str, str]:
            if not self.perform_action("power", state=state):
                raise HTTPException(status_code=400, detail="Invalid power state")
            return {"status": "success"}

        @app.post("/brightness/{level}")
        async def set_brightness(level: int) -> Dict[str, str]:
            if not self.perform_action("set_brightness", level=level):
                raise HTTPException(status_code=400, detail="Invalid brightness level")
            return {"status": "success"}

    def get_status(self) -> Dict[str, Any]:
        return {
            "device_id": self.device_id,
            "type": "smart_light",
            "is_on": self.state.is_on,
            "brightness": self.state.brightness,
            "connection": f"{self.host}:{self.port}",
        }

    def perform_action(self, action: str, **kwargs) -> bool:
        if action == "power":
            state = kwargs.get("state")
            if state == "on":
                self.state.is_on = True
                return True
            if state == "off":
                self.state.is_on = False
                return True
            return False

        if action == "set_brightness":
            level = kwargs.get("level")
            if not isinstance(level, int):
                return False
            if 0 <= level <= 100:
                self.state.brightness = level
                return True
            return False

        return False

    def run_server(self) -> None:
        uvicorn.run(self.app, host=self.host, port=self.port, log_level="info")


if __name__ == "__main__":
    device = SmartLightDevice("light_001")
    device.run_server()
