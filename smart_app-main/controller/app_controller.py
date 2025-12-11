from __future__ import annotations

from typing import Dict, List, Any

from controller.iot_facade import IOTFacade
from devices.base_device import Device, LoggingDeviceDecorator
from devices.smart_speaker import SmartSpeakerDevice
from devices.smart_light import SmartLightDevice
from devices.smart_curtains import SmartCurtainsDevice


class AppController:
    def __init__(self) -> None:
        self.facade = IOTFacade()
        self._register_default_devices()

    def _register_default_devices(self) -> None:
        speaker = LoggingDeviceDecorator(
            SmartSpeakerDevice("speaker_001", "127.0.0.1", 8001)
        )
        light = LoggingDeviceDecorator(
            SmartLightDevice("light_001", "127.0.0.1", 8002)
        )
        curtains = LoggingDeviceDecorator(
            SmartCurtainsDevice("curtains_001", "127.0.0.1", 8003)
        )

        self.facade.register_device(speaker)
        self.facade.register_device(light)
        self.facade.register_device(curtains)

    def toggle_speaker(self) -> Dict[str, Any]:
        status = self.facade.get_device_status("speaker_001")
        if not status:
            return {}
        current_state = "off" if status.get("is_on") else "on"
        success = self.facade.perform_device_action(
            "speaker_001",
            "power",
            state=current_state,
        )
        if success:
            return self.facade.get_device_status("speaker_001") or {}
        return {}

    def set_speaker_volume(self, volume: int) -> bool:
        return self.facade.perform_device_action(
            "speaker_001",
            "set_volume",
            level=volume,
        )

    def toggle_light(self) -> Dict[str, Any]:
        status = self.facade.get_device_status("light_001")
        if not status:
            return {}
        current_state = "off" if status.get("is_on") else "on"
        success = self.facade.perform_device_action(
            "light_001",
            "power",
            state=current_state,
        )
        if success:
            return self.facade.get_device_status("light_001") or {}
        return {}

    def set_light_brightness(self, brightness: int) -> bool:
        return self.facade.perform_device_action(
            "light_001",
            "set_brightness",
            level=brightness,
        )

    def toggle_curtains(self) -> Dict[str, Any]:
        status = self.facade.get_device_status("curtains_001")
        if not status:
            return {}
        current_state = "close" if status.get("is_open") else "open"
        success = self.facade.perform_device_action(
            "curtains_001",
            "power",
            state=current_state,
        )
        if success:
            return self.facade.get_device_status("curtains_001") or {}
        return {}

    def set_curtains_position(self, position: int) -> bool:
        return self.facade.perform_device_action(
            "curtains_001",
            "set_position",
            value=position,
        )

    def get_all_status(self) -> List[Dict[str, Any]]:
        return self.facade.get_all_status()

    def register_new_device(self, device: Device) -> str:
        return self.facade.register_device(device)
