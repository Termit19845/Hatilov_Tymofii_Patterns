from __future__ import annotations

from typing import Dict, Any

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from devices.base_device import Device


class CurtainState(BaseModel):
    is_open: bool = False
    position: int = 0  # 0 closed, 100 open


class SmartCurtainsDevice(Device):
    def __init__(self, device_id: str, host: str = "127.0.0.1", port: int = 8003) -> None:
        super().__init__(device_id, host, port)
        self.state = CurtainState()
        self.app = FastAPI(title=f"Smart Curtains {device_id}")
        self._setup_routes()

    def _setup_routes(self) -> None:
        app = self.app

        @app.get("/status")
        async def get_status() -> Dict[str, Any]:
            return self.get_status()

        @app.post("/power/{state}")
        async def set_power(state: str) -> Dict[str, str]:
            if not self.perform_action("power", state=state):
                raise HTTPException(status_code=400, detail="Invalid curtain state")
            return {"status": "success"}

        @app.post("/position/{value}")
        async def set_position(value: int) -> Dict[str, str]:
            if not self.perform_action("set_position", value=value):
                raise HTTPException(status_code=400, detail="Invalid position")
            return {"status": "success"}

    def get_status(self) -> Dict[str, Any]:
        return {
            "device_id": self.device_id,
            "type": "smart_curtains",
            "is_open": self.state.is_open,
            "position": self.state.position,
            "connection": f"{self.host}:{self.port}",
        }

    def perform_action(self, action: str, **kwargs) -> bool:
        if action == "power":
            state = kwargs.get("state")
            if state == "open":
                self.state.is_open = True
                self.state.position = 100
                return True
            if state == "close":
                self.state.is_open = False
                self.state.position = 0
                return True
            return False

        if action == "set_position":
            value = kwargs.get("value")
            if not isinstance(value, int):
                return False
            if 0 <= value <= 100:
                self.state.position = value
                self.state.is_open = value > 0
                return True
            return False

        return False

    def run_server(self) -> None:
        uvicorn.run(self.app, host=self.host, port=self.port, log_level="info")


if __name__ == "__main__":
    device = SmartCurtainsDevice("curtains_001")
    device.run_server()
