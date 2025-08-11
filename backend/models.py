from pydantic import BaseModel
from typing import Dict, Any, List

class ChartRequest(BaseModel):
    csv_data: str

class StatsResponse(BaseModel):
    total_races: int
    avg_wpm: float
    best_wpm: float
    total_wins: int
    avg_accuracy: float
    date_range: Dict[str, str]

class ChartResponse(BaseModel):
    data: List[Dict[str, Any]]
    layout: Dict[str, Any]
    insights: List[str]
    has_insights: bool