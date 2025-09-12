use axum::{
    extract::State,
    http::StatusCode,
    response::Json,
    routing::{get, post},
    Router,
};
use serde::Serialize;
use std::sync::Arc;
use tokio::net::TcpListener;
use tower_http::cors::CorsLayer;
use tracing::{info, instrument};
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

// Polars imports
use polars::prelude::{col, IntoLazy};

mod models;
mod data_processing;
mod cache;
mod config;

use crate::config::Settings;

#[derive(Clone)]
pub struct AppState {
    pub settings: Settings,
    pub cache: Arc<crate::cache::DataCache>,
}

impl std::fmt::Debug for AppState {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("AppState")
            .field("settings", &self.settings)
            .field("cache", &"DataCache")
            .finish()
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Initialize tracing
    tracing_subscriber::registry()
        .with(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "backend_rust=info,tower_http=debug".into()),
        )
        .with(tracing_subscriber::fmt::layer())
        .init();

    // Load configuration
    let settings = Settings::new()?;
    let state = AppState { 
        settings: settings.clone(),
        cache: Arc::new(crate::cache::DataCache::new()),
    };

    // Build our application with routes
    let app = Router::new()
        .route("/health", get(health_handler))
        .route("/stats", post(stats_handler))
        .layer(
            CorsLayer::new()
                .allow_origin(settings.cors_origins.iter().map(|s| s.parse().unwrap()).collect::<Vec<_>>())
                .allow_methods([
                    axum::http::Method::GET,
                    axum::http::Method::POST,
                    axum::http::Method::OPTIONS,
                ])
                .allow_headers([
                    axum::http::header::CONTENT_TYPE,
                    axum::http::header::AUTHORIZATION,
                ])
                .allow_credentials(true)
        )
        .with_state(Arc::new(state));

    // Start server
    let listener = TcpListener::bind("0.0.0.0:8000").await?;
    info!("TypeRacer Rust Backend listening on: {}", listener.local_addr()?);
    
    axum::serve(listener, app).await?;

    Ok(())
}

#[instrument]
async fn health_handler(State(_state): State<Arc<AppState>>) -> Result<Json<HealthResponse>, StatusCode> {
    let response = HealthResponse {
        status: "healthy".to_string(),
        timestamp: chrono::Utc::now(),
    };
    
    Ok(Json(response))
}

#[derive(Serialize)]
struct HealthResponse {
    status: String,
    timestamp: chrono::DateTime<chrono::Utc>,
}

#[instrument]
async fn stats_handler(
    State(state): State<Arc<AppState>>,
    Json(request): Json<crate::models::ChartRequest>,
) -> Result<Json<crate::models::StatsResponse>, StatusCode> {
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
        .trim_matches('"')  // Remove extra quotes
        .to_string();
    let end_date = max_date_df.column("datetime_utc")
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .get(0)
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .to_string()
        .trim_matches('"')  // Remove extra quotes
        .to_string();
    
    let response = crate::models::StatsResponse {
        total_races,
        avg_wpm,
        best_wpm,
        total_wins,
        avg_accuracy,
        date_range: crate::models::DateRange {
            start: start_date,
            end: end_date,
        },
    };
    
    Ok(Json(response))
}