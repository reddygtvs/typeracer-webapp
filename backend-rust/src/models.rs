use serde::{Deserialize, Serialize};

#[derive(Deserialize, Debug)]
pub struct ChartRequest {
    pub csv_data: String,
}

#[derive(Serialize, Debug)]
pub struct StatsResponse {
    pub total_races: usize,
    pub avg_wpm: f64,
    pub best_wpm: f64,
    pub total_wins: i32,
    pub avg_accuracy: f64,
    pub date_range: DateRange,
}

#[derive(Serialize, Debug)]
pub struct DateRange {
    pub start: String,
    pub end: String,
}

#[derive(Serialize, Debug)]
pub struct ChartResponse {
    pub data: serde_json::Value,
    pub layout: serde_json::Value,
    pub insights: Vec<String>,
    pub has_insights: bool,
}