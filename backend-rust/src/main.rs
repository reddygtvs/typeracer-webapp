use axum::{
    routing::{get, post}, 
    Router,
};
use std::sync::Arc;
use tokio::net::TcpListener;
use tower_http::cors::CorsLayer;
use tracing::info;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

mod handlers;
mod models;
mod data_processing;
mod cache;

use handlers::charts::*;

#[derive(Clone, Debug)]
pub struct AppState {
    pub cache: cache::DataCache,
}

#[derive(Clone, Debug)]
pub struct Settings {
    pub cors_origins: Vec<String>,
}

impl Settings {
    pub fn new() -> Result<Self, Box<dyn std::error::Error>> {
        Ok(Settings {
            cors_origins: vec!["http://localhost:3000".to_string()],
        })
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    tracing_subscriber::registry()
        .with(tracing_subscriber::EnvFilter::try_from_default_env().unwrap_or_else(|_| "info".into()))
        .with(tracing_subscriber::fmt::layer())
        .init();

    let settings = Settings::new()?;
    let state = AppState { 
        cache: cache::DataCache::new(),
    };

    let app = Router::new()
        .route("/health", get(health_handler))
        .route("/charts/wpm-distribution", post(wpm_distribution_handler))
        .route("/charts/accuracy-distribution", post(accuracy_distribution_handler))
        .route("/charts/performance-over-time", post(performance_over_time_handler))
        .route("/charts/daily-performance", post(daily_performance_handler))
        .route("/charts/rolling-average", post(rolling_average_handler))
        .route("/charts/rank-distribution", post(rank_distribution_handler))
        .route("/charts/hourly-performance", post(hourly_performance_handler))
        .route("/charts/wpm-vs-accuracy", post(wpm_vs_accuracy_handler))
        .route("/charts/win-rate-monthly", post(win_rate_monthly_handler))
        .route("/charts/top-texts", post(top_texts_handler))
        .route("/charts/consistency-score", post(consistency_score_handler))
        .route("/charts/accuracy-by-rank", post(accuracy_by_rank_handler))
        .route("/charts/cumulative-accuracy", post(cumulative_accuracy_handler))
        .route("/charts/wpm-by-rank-boxplot", post(wpm_by_rank_boxplot_handler))
        .route("/charts/racers-impact", post(racers_impact_handler))
        .route("/charts/frequent-texts-improvement", post(frequent_texts_improvement_handler))
        .route("/charts/top-texts-distribution", post(top_texts_distribution_handler))
        .route("/charts/win-rate-after-win", post(win_rate_after_win_handler))
        .route("/charts/fastest-slowest-races", post(fastest_slowest_races_handler))
        .route("/charts/time-between-races", post(time_between_races_handler))
        .layer(CorsLayer::new()
            .allow_origin(settings.cors_origins.iter().map(|s| s.parse().unwrap()).collect::<Vec<_>>())
            .allow_methods([axum::http::Method::GET, axum::http::Method::POST, axum::http::Method::OPTIONS])
            .allow_headers([axum::http::header::CONTENT_TYPE, axum::http::header::AUTHORIZATION])
            .allow_credentials(true))
        .with_state(Arc::new(state));

    let listener = TcpListener::bind("0.0.0.0:8000").await?;
    info!("TypeRacer Rust Backend listening on: {}", listener.local_addr()?);
    axum::serve(listener, app).await?;
    Ok(())
}

async fn health_handler() -> &'static str {
    "OK"
}