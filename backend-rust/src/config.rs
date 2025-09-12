use serde::{Deserialize, Serialize};
use std::env;

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Settings {
    pub cors_origins: Vec<String>,
    pub log_level: String,
    pub port: u16,
}

impl Settings {
    pub fn new() -> Result<Self, Box<dyn std::error::Error>> {
        // Default CORS origins matching Python backend
        let default_cors_origins = vec![
            "http://localhost:5173".to_string(),
            "http://localhost:5174".to_string(),
            "http://localhost:3000".to_string(),
            "https://typeracer-webapp.fly.dev".to_string(),
        ];

        let cors_origins = env::var("CORS_ORIGINS")
            .map(|s| s.split(',').map(|s| s.trim().to_string()).collect())
            .unwrap_or(default_cors_origins);

        let log_level = env::var("LOG_LEVEL").unwrap_or_else(|_| "INFO".to_string());
        let port = env::var("PORT")
            .map(|p| p.parse().unwrap_or(8000))
            .unwrap_or(8000);

        Ok(Settings {
            cors_origins,
            log_level,
            port,
        })
    }
}