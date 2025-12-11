from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any
import json
import uuid

from fastapi import FastAPI
from pydantic import BaseModel


# ===================== Domain models =====================

class WeatherInfo(BaseModel):
    condition: str  # "sunny", "rainy", "cold", etc.
    temperature: int


class UserPreferences(BaseModel):
    username: str
    city: str
    prefers_outdoor: bool = True


class DayPlan(BaseModel):
    id: str
    username: str
    city: str
    weather_condition: str
    temperature: int
    strategy_used: str
    activities: List[str]


# ===================== Strategy pattern =====================

class PlanningStrategy(ABC):
    @abstractmethod
    def create_plan(self, prefs: UserPreferences, weather: WeatherInfo) -> List[str]:
        ...


class SunnyDayStrategy(PlanningStrategy):
    def create_plan(self, prefs: UserPreferences, weather: WeatherInfo) -> List[str]:
        activities = []
        if prefs.prefers_outdoor:
            activities.append("Go for a walk in the park")
            activities.append("Meet friends at an outdoor cafe")
        else:
            activities.append("Read a book on the balcony")
        activities.append("Evening walk to enjoy the sunset")
        return activities


class RainyDayStrategy(PlanningStrategy):
    def create_plan(self, prefs: UserPreferences, weather: WeatherInfo) -> List[str]:
        activities = [
            "Watch a movie at home",
            "Play video games",
            "Drink hot tea and listen to music",
        ]
        if not prefs.prefers_outdoor:
            activities.append("Do some cleaning or organizing at home")
        return activities


class ColdDayStrategy(PlanningStrategy):
    def create_plan(self, prefs: UserPreferences, weather: WeatherInfo) -> List[str]:
        activities = [
            "Go to the gym or indoor pool",
            "Cook something warm and tasty",
            "Meet friends in a warm place (mall or cafe)",
        ]
        return activities


# ===================== Observer pattern =====================

class PlanObserver(ABC):
    @abstractmethod
    def update(self, plan: DayPlan) -> None:
        ...


class PrintObserver(PlanObserver):
    def update(self, plan: DayPlan) -> None:
        print(f"[OBSERVER] New plan for {plan.username} in {plan.city}: {plan.activities}")


class FileStorageObserver(PlanObserver):
    def __init__(self, file_path: str = "plans.json") -> None:
        self.file_path = Path(file_path)

    def _load_all(self) -> List[Dict[str, Any]]:
        if not self.file_path.exists():
            return []
        try:
            with self.file_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []

    def _save_all(self, items: List[Dict[str, Any]]) -> None:
        with self.file_path.open("w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)

    def update(self, plan: DayPlan) -> None:
        items = self._load_all()
        items.append(plan.dict())
        self._save_all(items)


# ===================== Planner (Context + Subject) =====================

class SmartDayPlanner:
    def __init__(self) -> None:
        self.observers: List[PlanObserver] = []
        self.strategies: Dict[str, PlanningStrategy] = {
            "sunny": SunnyDayStrategy(),
            "clear": SunnyDayStrategy(),
            "rainy": RainyDayStrategy(),
            "drizzle": RainyDayStrategy(),
            "cold": ColdDayStrategy(),
            "snow": ColdDayStrategy(),
        }

    def attach(self, observer: PlanObserver) -> None:
        self.observers.append(observer)

    def notify(self, plan: DayPlan) -> None:
        for obs in self.observers:
            obs.update(plan)

    def choose_strategy(self, weather: WeatherInfo) -> PlanningStrategy:
        key = weather.condition.lower()
        if key in self.strategies:
            return self.strategies[key]
        # дефолтний вибір стратегії, якщо умови не впізнали
        if weather.temperature <= 5:
            return ColdDayStrategy()
        if "rain" in key:
            return RainyDayStrategy()
        return SunnyDayStrategy()

    def create_plan(self, prefs: UserPreferences, weather: WeatherInfo) -> DayPlan:
        strategy = self.choose_strategy(weather)
        activities = strategy.create_plan(prefs, weather)
        plan = DayPlan(
            id=str(uuid.uuid4()),
            username=prefs.username,
            city=prefs.city,
            weather_condition=weather.condition,
            temperature=weather.temperature,
            strategy_used=type(strategy).__name__,
            activities=activities,
        )
        self.notify(plan)
        return plan


# ===================== FastAPI application =====================

app = FastAPI(title="Smart Day Planner (Lab 6 minimal)")

planner = SmartDayPlanner()
planner.attach(PrintObserver())
planner.attach(FileStorageObserver("plans.json"))


class PlanRequest(BaseModel):
    username: str
    city: str
    prefers_outdoor: bool = True
    condition: str
    temperature: int


@app.post("/plan", response_model=DayPlan)
def create_day_plan(req: PlanRequest):
    prefs = UserPreferences(
        username=req.username,
        city=req.city,
        prefers_outdoor=req.prefers_outdoor,
    )
    weather = WeatherInfo(condition=req.condition, temperature=req.temperature)
    plan = planner.create_plan(prefs, weather)
    return plan


@app.get("/plans", response_model=List[DayPlan])
def get_all_plans():
    file_path = Path("plans.json")
    if not file_path.exists():
        return []
    try:
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return [DayPlan(**item) for item in data]
    except json.JSONDecodeError:
        return []


@app.get("/")
def root():
    return {
        "message": "Smart Day Planner API (Lab 6 minimal). Use POST /plan and GET /plans.",
        "endpoints": {
            "POST /plan": "Create new day plan based on weather and preferences",
            "GET /plans": "Get all saved plans",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8006)
