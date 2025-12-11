# lab2_patterns.py
from __future__ import annotations

import json
import math
from abc import ABC, abstractmethod
from typing import List, Dict


# ---------- Containers ----------

class Container(ABC):
    def __init__(self, ID: int, weight: int):
        self.ID = ID
        self.weight = weight

    @abstractmethod
    def consumption(self) -> float:
        pass

    def equals(self, other: Container) -> bool:
        return (
            type(self) is type(other)
            and self.ID == other.ID
            and self.weight == other.weight
        )


class BasicContainer(Container):
    def consumption(self) -> float:
        return self.weight * 2.50


class HeavyContainer(Container):
    def consumption(self) -> float:
        return self.weight * 3.00


class RefrigeratedContainer(HeavyContainer):
    def consumption(self) -> float:
        return self.weight * 5.00


class LiquidContainer(HeavyContainer):
    def consumption(self) -> float:
        return self.weight * 4.00


# ---------- Interfaces ----------

class IPort(ABC):
    @abstractmethod
    def incomingShip(self, s: Ship) -> None:
        pass

    @abstractmethod
    def outgoingShip(self, s: Ship) -> None:
        pass


class IShip(ABC):
    @abstractmethod
    def sailTo(self, p: Port) -> bool:
        pass

    @abstractmethod
    def reFuel(self, newFuel: float) -> None:
        pass

    @abstractmethod
    def load(self, cont: Container) -> bool:
        pass

    @abstractmethod
    def unLoad(self, cont: Container) -> bool:
        pass


# ---------- Port ----------

class Port(IPort):
    def __init__(self, ID: int, latitude: float, longitude: float):
        self.ID = ID
        self.latitude = latitude
        self.longitude = longitude
        self.containers: List[Container] = []
        self.history: List[Ship] = []
        self.current: List[Ship] = []

    def incomingShip(self, s: Ship) -> None:
        if s not in self.current:
            self.current.append(s)
        if s not in self.history:
            self.history.append(s)

    def outgoingShip(self, s: Ship) -> None:
        if s in self.current:
            self.current.remove(s)
        if s not in self.history:
            self.history.append(s)

    def getDistance(self, other: Port) -> float:
        return math.sqrt(
            (self.latitude - other.latitude) ** 2
            + (self.longitude - other.longitude) ** 2
        )


# ---------- Ship ----------

class Ship(IShip):
    def __init__(
        self,
        ID: int,
        currentPort: Port,
        totalWeightCapacity: int,
        maxNumberOfAllContainers: int,
        maxNumberOfHeavyContainers: int,
        maxNumberOfRefrigeratedContainers: int,
        maxNumberOfLiquidContainers: int,
        fuelConsumptionPerKM: float,
    ):
        self.ID = ID
        self.fuel: float = 0.0
        self.currentPort: Port = currentPort
        self.totalWeightCapacity = totalWeightCapacity
        self.maxNumberOfAllContainers = maxNumberOfAllContainers
        self.maxNumberOfHeavyContainers = maxNumberOfHeavyContainers
        self.maxNumberOfRefrigeratedContainers = maxNumberOfRefrigeratedContainers
        self.maxNumberOfLiquidContainers = maxNumberOfLiquidContainers
        self.fuelConsumptionPerKM = fuelConsumptionPerKM
        self.containers: List[Container] = []

        currentPort.incomingShip(self)

    def getCurrentContainers(self) -> List[Container]:
        return sorted(self.containers, key=lambda c: c.ID)

    def reFuel(self, newFuel: float) -> None:
        self.fuel += newFuel

    def load(self, cont: Container) -> bool:
        if cont not in self.currentPort.containers:
            return False

        if len(self.containers) >= self.maxNumberOfAllContainers:
            return False

        current_weight = sum(c.weight for c in self.containers)
        if current_weight + cont.weight > self.totalWeightCapacity:
            return False

        if isinstance(cont, HeavyContainer):
            heavy_count = len(
                [c for c in self.containers if isinstance(c, HeavyContainer)]
            )
            if heavy_count >= self.maxNumberOfHeavyContainers:
                return False

        if isinstance(cont, RefrigeratedContainer):
            ref_count = len(
                [c for c in self.containers if isinstance(c, RefrigeratedContainer)]
            )
            if ref_count >= self.maxNumberOfRefrigeratedContainers:
                return False

        if isinstance(cont, LiquidContainer):
            liq_count = len(
                [c for c in self.containers if isinstance(c, LiquidContainer)]
            )
            if liq_count >= self.maxNumberOfLiquidContainers:
                return False

        self.currentPort.containers.remove(cont)
        self.containers.append(cont)
        return True

    def unLoad(self, cont: Container) -> bool:
        if cont not in self.containers:
            return False
        self.containers.remove(cont)
        self.currentPort.containers.append(cont)
        return True

    def sailTo(self, p: Port) -> bool:
        distance = self.currentPort.getDistance(p)
        per_km = self.fuelConsumptionPerKM + sum(
            c.consumption() for c in self.containers
        )
        required = distance * per_km

        if self.fuel < required:
            return False

        self.fuel -= required
        self.currentPort.outgoingShip(self)
        self.currentPort = p
        p.incomingShip(self)
        return True


# ---------- Simulation / I/O ----------

def run_simulation(input_path: str = "input.json", output_path: str = "output.json"):
    ports: Dict[int, Port] = {}
    ships: Dict[int, Ship] = {}
    containers: Dict[int, Container] = {}
    next_container_id = 0

    with open(input_path) as f:
        operations = json.load(f)

    for op in operations:
        action = op["op"]

        if action == "create_port":
            pid = op["id"]
            ports[pid] = Port(pid, op["lat"], op["lon"])

        elif action == "create_container":
            next_container_id += 1
            weight = op["weight"]
            special = op.get("type")  # "R", "L" or None
            port_id = op["port_id"]

            if special == "R":
                cont = RefrigeratedContainer(next_container_id, weight)
            elif special == "L":
                cont = LiquidContainer(next_container_id, weight)
            elif weight <= 3000:
                cont = BasicContainer(next_container_id, weight)
            else:
                cont = HeavyContainer(next_container_id, weight)

            containers[cont.ID] = cont
            ports[port_id].containers.append(cont)

        elif action == "create_ship":
            sid = op["id"]
            port_id = op["port_id"]
            ships[sid] = Ship(
                sid,
                ports[port_id],
                op["max_weight"],
                op["max_all"],
                op["max_heavy"],
                op["max_ref"],
                op["max_liq"],
                op["fuel_per_km"],
            )

        elif action == "load":
            ship_id = op["ship_id"]
            cont_id = op["container_id"]
            ships[ship_id].load(containers[cont_id])

        elif action == "unload":
            ship_id = op["ship_id"]
            cont_id = op["container_id"]
            ships[ship_id].unLoad(containers[cont_id])

        elif action == "sail":
            ship_id = op["ship_id"]
            port_id = op["port_id"]
            ships[ship_id].sailTo(ports[port_id])

        elif action == "refuel":
            ship_id = op["ship_id"]
            amount = op["amount"]
            ships[ship_id].reFuel(amount)

    out: Dict[str, dict] = {}

    for pid in sorted(ports.keys()):
        p = ports[pid]
        key = f"Port {pid}"
        port_dict: Dict[str, object] = {
            "lat": round(p.latitude, 2),
            "lon": round(p.longitude, 2),
            "basic_container": [],
            "heavy_container": [],
            "refrigerated_container": [],
            "liquid_container": [],
        }

        for c in p.containers:
            if isinstance(c, RefrigeratedContainer):
                port_dict["refrigerated_container"].append(c.ID)
            elif isinstance(c, LiquidContainer):
                port_dict["liquid_container"].append(c.ID)
            elif isinstance(c, HeavyContainer):
                port_dict["heavy_container"].append(c.ID)
            elif isinstance(c, BasicContainer):
                port_dict["basic_container"].append(c.ID)

        for k in (
            "basic_container",
            "heavy_container",
            "refrigerated_container",
            "liquid_container",
        ):
            port_dict[k] = sorted(port_dict[k])

        for s in sorted(p.current, key=lambda x: x.ID):
            ship_key = f"ship_{s.ID}"
            ship_dict: Dict[str, object] = {
                "fuel_left": round(s.fuel, 2),
                "basic_container": [],
                "heavy_container": [],
                "refrigerated_container": [],
                "liquid_container": [],
            }

            for c in s.getCurrentContainers():
                if isinstance(c, RefrigeratedContainer):
                    ship_dict["refrigerated_container"].append(c.ID)
                elif isinstance(c, LiquidContainer):
                    ship_dict["liquid_container"].append(c.ID)
                elif isinstance(c, HeavyContainer):
                    ship_dict["heavy_container"].append(c.ID)
                elif isinstance(c, BasicContainer):
                    ship_dict["basic_container"].append(c.ID)

            for k in (
                "basic_container",
                "heavy_container",
                "refrigerated_container",
                "liquid_container",
            ):
                ship_dict[k] = sorted(ship_dict[k])

            port_dict[ship_key] = ship_dict

        out[key] = port_dict

    with open(output_path, "w") as f:
        json.dump(out, f, indent=2)


if __name__ == "__main__":
    run_simulation()
