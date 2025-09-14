use axum::{
    extract::State,
    http::StatusCode,
    response::Json,
};
use polars::prelude::{col, IntoLazy};
use std::sync::Arc;
use tracing::instrument;

use crate::{models, AppState};

#[instrument]
pub async fn stats_handler(
    State(state): State<Arc<AppState>>,
    Json(request): Json<models::ChartRequest>,
) -> Result<Json<models::StatsResponse>, StatusCode> {
    // Get or process dataframe from cache
    let csv_hash = crate::cache::DataCache::get_csv_hash(&request.csv_data);
    
    let df = if let Some(cached_df) = state.cache.get_dataframe(&csv_hash) {
        cached_df
    } else {
        // Process CSV and cache it
        let processed_df = crate::data_processing::process_csv_data(&request.csv_data)
            .map_err(|_| StatusCode::BAD_REQUEST)?;
        
        state.cache.insert_dataframe(csv_hash.clone(), processed_df.clone());
        Arc::new(processed_df)
    };
    
    // Calculate stats using DataFrame operations
    let total_races = df.height();
    
    // Get mean WPM
    let avg_wpm_df = (*df).clone().lazy()
        .select([col("wpm").mean()])
        .collect()
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    let avg_wpm = avg_wpm_df.column("wpm")
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .get(0)
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .try_extract::<f64>()
        .unwrap_or(0.0);
    
    // Get max WPM
    let max_wpm_df = (*df).clone().lazy()
        .select([col("wpm").max()])
        .collect()
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    let best_wpm = max_wpm_df.column("wpm")
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .get(0)
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .try_extract::<f64>()
        .unwrap_or(0.0);
    
    // Get sum of wins
    let wins_sum_df = (*df).clone().lazy()
        .select([col("win").sum()])
        .collect()
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    let total_wins = wins_sum_df.column("win")
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .get(0)
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .try_extract::<i32>()
        .unwrap_or(0);
    
    // Get mean accuracy  
    let avg_acc_df = (*df).clone().lazy()
        .select([col("accuracy").mean()])
        .collect()
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    let avg_accuracy = avg_acc_df.column("accuracy")
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .get(0)
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .try_extract::<f64>()
        .unwrap_or(0.0);
    
    // Get date range - format to match Python backend exactly
    let min_date_df = (*df).clone().lazy()
        .select([col("datetime_utc").min()])
        .collect()
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    let max_date_df = (*df).clone().lazy()
        .select([col("datetime_utc").max()])
        .collect()
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    
    let start_date = min_date_df.column("datetime_utc")
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .get(0)
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .to_string()
        .trim_matches('"')
        .to_string();
    let end_date = max_date_df.column("datetime_utc")
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .get(0)
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .to_string()
        .trim_matches('"')
        .to_string();
    
    let response = models::StatsResponse {
        total_races,
        avg_wpm,
        best_wpm,
        total_wins,
        avg_accuracy,
        date_range: models::DateRange {
            start: start_date,
            end: end_date,
        },
    };
    
    Ok(Json(response))
}