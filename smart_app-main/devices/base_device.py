from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple


class Device(ABC):
    def __init__(self, device_id: str, host: str, port: int) -> None:
        self.device_id = device_id
        self.host = host
        self.port = port

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        ...

    @abstractmethod
    def perform_action(self, action: str, **kwargs) -> bool:
        ...

    def connection_info(self) -> Tuple[str, int]:
        return self.host, self.port


class LoggingDeviceDecorator(Device):
    def __init__(self, wrapped: Device) -> None:
        super().__init__(wrapped.device_id, wrapped.host, wrapped.port)
        self._wrapped = wrapped

    def get_status(self) -> Dict[str, Any]:
        return self._wrapped.get_status()

    def perform_action(self, action: str, **kwargs) -> bool:
        return self._wrapped.perform_action(action, **kwargs)
