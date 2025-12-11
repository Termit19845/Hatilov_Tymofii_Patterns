
# Assignment — SmartApp IoT Microservices Refactor

##  Overview

In this assignment, you will **refactor a SmartApp IoT system into a real microservices architecture**.  
Each smart device (speaker, light, curtains) will run as its **own FastAPI microservice** on a **separate port**, and a **main web application** will communicate with them through HTTP.

You will:
- Build independent FastAPI microservices for devices
- Create a main controller app to communicate with devices
- Use design patterns (Controller, Facade, Decorator)
- Extend the system with your own device

---

##  Learning Objectives

- Understand **microservice architecture** with multiple FastAPI apps  
- Use **Controller** and **Facade** patterns to decouple logic  
- Extend functionality without changing core HTML/CSS  
- Run multiple microservices simultaneously on different ports

---

##  Final Architecture

```

SmartApp System
├── Main Web Application (FastAPI, Port 8000)
├── Device Microservices
│   ├── Smart Speaker (Port 8001)
│   ├── Smart Light (Port 8002)
│   └── Smart Curtains (Port 8003) ← Your extension
└── Controller & Facade Layer

```

Each device exposes:
- `/status` → Returns current state  
- `/power/{state}` → Turns device on/off (or open/close for curtains)  
- Additional endpoints as needed (e.g., `/volume`, `/brightness`, `/position`)

---

## Project Structure

```

smartapp-iot/
├── main.py                 # Main FastAPI web app
├── controller/
│   ├── app_controller.py   # Business logic
│   └── iot_facade.py       # Handles HTTP requests to devices
├── devices/
│   ├── base_device.py
│   ├── smart_speaker.py
│   ├── smart_light.py
│   └── smart_curtains.py   # ← You will create this
├── web/
│   ├── templates/
│   │   └── index.html
│   └── static/
│       └── style.css
└── requirements.txt

````

You **don’t edit** HTML/CSS — only run them.

---

##  Step 1: Install Dependencies

```bash
pip install -r requirements.txt
````

---

##  Step 2: Create Microservices and stuff

`controller/app_controller.py`

```python
from typing import Dict, List, Any
from controller.iot_facade import IOTFacade
from devices.base_device import Device, LoggingDeviceDecorator
from devices.smart_speaker import SmartSpeakerDevice
from devices.smart_light import SmartLightDevice

class AppController:
    """Main application controller"""
    
    def __init__(self):
        self.facade = IOTFacade()
        self._register_default_devices()
    
    def _register_default_devices(self):
        """Register default devices with the system"""
        # Create and register devices with real network configuration
        speaker = LoggingDeviceDecorator(
            SmartSpeakerDevice("speaker_001", "127.0.0.1", 8001)
        )
        light = LoggingDeviceDecorator(
            SmartLightDevice("light_001", "127.0.0.1", 8002)
        )
        
        self.facade.register_device(speaker)
        self.facade.register_device(light)
    
    def toggle_speaker(self) -> Dict[str, Any]:
        """Toggle speaker power state"""
        status = self.facade.get_device_status("speaker_001")
        if status:
            current_state = "off" if status["is_on"] else "on"
            success = self.facade.perform_device_action(
                "speaker_001", "power", state=current_state
            )
            if success:
                return self.facade.get_device_status("speaker_001")
        return {}
    
    def set_speaker_volume(self, volume: int) -> bool:
        """Set speaker volume"""
        return self.facade.perform_device_action(
            "speaker_001", "set_volume", level=volume
        )
    
    def toggle_light(self) -> Dict[str, Any]:
        """Toggle light power state"""
        status = self.facade.get_device_status("light_001")
        if status:
            current_state = "off" if status["is_on"] else "on"
            success = self.facade.perform_device_action(
                "light_001", "power", state=current_state
            )
            if success:
                return self.facade.get_device_status("light_001")
        return {}
    
    def set_light_brightness(self, brightness: int) -> bool:
        """Set light brightness"""
        return self.facade.perform_device_action(
            "light_001", "set_brightness", level=brightness
        )
    
    def get_all_status(self) -> List[Dict[str, Any]]:
        """Get status of all devices"""
        return self.facade.get_all_status()
    
    def register_new_device(self, device: Device) -> str:
        """Register a new device with the system"""
        return self.facade.register_device(device)
```


###  Smart Speaker Example

`devices/smart_speaker.py`:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import uvicorn
from devices.base_device import Device

class SpeakerState(BaseModel):
    is_on: bool = False
    volume: int = 50
    playing: bool = False
    current_track: str = ""

class SmartSpeakerDevice(Device):
    def __init__(self, device_id: str, host="127.0.0.1", port=8001):
        super().__init__(device_id, host, port)
        self.state = SpeakerState()
        self.app = FastAPI(title=f"Smart Speaker {device_id}")
        self._setup_routes()

    def _setup_routes(self):
        app = self.app

        @app.get("/status")
        async def get_status():
            return self.get_status()

        @app.post("/power/{state}")
        async def set_power(state: str):
            if not self.perform_action("power", state=state):
                raise HTTPException(status_code=400, detail="Invalid power state")
            return {"status": "success"}

    def get_status(self) -> Dict[str, Any]:
        return {
            "device_id": self.device_id,
            "type": "smart_speaker",
            "is_on": self.state.is_on,
            "volume": self.state.volume,
            "playing": self.state.playing,
            "current_track": self.state.current_track,
            "connection": f"{self.host}:{self.port}"
        }

    def perform_action(self, action: str, **kwargs) -> bool:
        if action == "power":
            state = kwargs.get("state")
            if state == "on":
                self.state.is_on = True
                return True
            elif state == "off":
                self.state.is_on = False
                self.state.playing = False
                return True
        return False

    def run_server(self):
        uvicorn.run(self.app, host=self.host, port=self.port, log_level="info")

if __name__ == "__main__":
    speaker = SmartSpeakerDevice("speaker_001")
    speaker.run_server()
```

 Run the microservice:

```bash
python devices/smart_speaker.py
```

Visit [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs) to test endpoints.

---

##  Step 3: Add New Device — Curtains (Think here in Creational Patterns Style!)

`devices/smart_curtains.py`:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import uvicorn
from devices.base_device import Device

class CurtainState(BaseModel):
    is_open: bool = False
    position: int = 0  # 0 = closed, 100 = fully open

class SmartCurtainsDevice(Device):
    def __init__(self, device_id: str, host="127.0.0.1", port=8003):
        super().__init__(device_id, host, port)
        self.state = CurtainState()
        self.app = FastAPI(title=f"Smart Curtains {device_id}")
        self._setup_routes()

    def _setup_routes(self):
        app = self.app

        @app.get("/status")
        async def get_status():
            return self.get_status()

        @app.post("/power/{state}")
        async def set_power(state: str):
            if not self.perform_action("power", state=state):
                raise HTTPException(status_code=400, detail="Invalid curtain state")
            return {"status": "success"}

        @app.post("/position/{value}")
        async def set_position(value: int):
            if not self.perform_action("position", value=value):
                raise HTTPException(status_code=400, detail="Invalid position")
            return {"status": "success"}

    def get_status(self) -> Dict[str, Any]:
        return {
            "device_id": self.device_id,
            "type": "smart_curtains",
            "is_open": self.state.is_open,
            "position": self.state.position,
            "connection": f"{self.host}:{self.port}"
        }

    def perform_action(self, action: str, **kwargs) -> bool:
        if action == "power":
            state = kwargs.get("state")
            if state == "open":
                self.state.is_open = True
                self.state.position = 100
                return True
            elif state == "close":
                self.state.is_open = False
                self.state.position = 0
                return True
        elif action == "position":
            value = kwargs.get("value")
            if 0 <= value <= 100:
                self.state.position = value
                self.state.is_open = value > 0
                return True
        return False

    def run_server(self):
        uvicorn.run(self.app, host=self.host, port=self.port, log_level="info")

if __name__ == "__main__":
    curtains = SmartCurtainsDevice("curtains_001")
    curtains.run_server()
```

 Run in new terminal:

```bash
python devices/smart_curtains.py
```

---
##  Step 3: `main.py` — FastAPI Main Web Application

Below is the **full working `main.py` file** for the SmartApp IoT Microservices assignment.  
This file is responsible for:

- Running the **main dashboard**   
- Communicating with **device microservices** through HTTP   
- Using the **Controller** and **Facade** patterns to manage devices

---

```python
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from controller.app_controller import AppController
import uvicorn

# Create FastAPI app
app = FastAPI(title="SmartApp IoT System")

#  Load HTML templates (for dashboard)
templates = Jinja2Templates(directory="web/templates")

#  Mount static files (CSS, images, etc.)
app.mount("/static", StaticFiles(directory="web/static"), name="static")

#  Initialize our main application controller
controller = AppController()

#  Main dashboard page
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Show the main dashboard with all device statuses.
    """
    status = controller.get_all_status()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "devices": status}
    )

#  Toggle Smart Speaker power
@app.post("/toggle_speaker")
async def toggle_speaker(request: Request):
    speaker_status = controller.toggle_speaker()
    status = controller.get_all_status()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "devices": status, "updated_device": speaker_status}
    )

#  Toggle Smart Light power
@app.post("/toggle_light")
async def toggle_light(request: Request):
    light_status = controller.toggle_light()
    status = controller.get_all_status()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "devices": status, "updated_device": light_status}
    )

#  Set Smart Speaker volume
@app.post("/set_volume")
async def set_volume(request: Request, volume: int = Form(...)):
    controller.set_speaker_volume(volume)
    status = controller.get_all_status()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "devices": status}
    )

#  Set Smart Light brightness
@app.post("/set_brightness")
async def set_brightness(request: Request, brightness: int = Form(...)):
    controller.set_light_brightness(brightness)
    status = controller.get_all_status()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "devices": status}
    )

#  Entry point
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
```

##  Step 5: Run All Services

Open **3–4 terminals**:

**Terminal 1**

```bash
python devices/smart_speaker.py
```

**Terminal 2**

```bash
python devices/smart_light.py
```

**Terminal 3**

```bash
python devices/smart_curtains.py
```

**Terminal 4**

```bash
python main.py
```

---

##  Patterns Used

| Pattern      | Location                 | Purpose                                    |
| ------------ | ------------------------ | ------------------------------------------ |
| Controller   | `AppController`          | Business logic                             |
| Facade       | `iot_facade.py`          | Abstracts HTTP requests                    |
| Decorator    | Optional logging wrapper | Add functionality without modifying device |
| Microservice | Devices directory        | Independent services                       |

---

##  Deliverables

* Working **speaker**, **light**, **curtains** microservices
* Updated **controller** integration
* Screenshot of dashboard with all devices visible
* Short **README** describing your curtain device features

---

## Bonus

* Add extra feature (e.g. curtain timer, light color changer)
* Use decorator to add logging or authentication

---

## Summary

* You now have **multiple FastAPI microservices** communicating with a central app.
* You applied **Controller** and **Facade** patterns.
* You extended the system with a **new device**.
* You didn’t need to touch HTML or CSS at all.

```
```
