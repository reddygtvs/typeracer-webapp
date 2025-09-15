use dashmap::DashMap;
use polars::prelude::DataFrame;
use sha2::{Digest, Sha256};
use std::sync::Arc;

#[derive(Clone, Debug)]
pub struct DataCache {
    dataframe_cache: DashMap<String, Arc<DataFrame>>,
    chart_cache: DashMap<String, serde_json::Value>,
}

impl DataCache {
    pub fn new() -> Self {
        Self {
            dataframe_cache: DashMap::new(),
            chart_cache: DashMap::new(),
        }
    }

    pub fn get_csv_hash(csv_data: &str) -> String {
        let mut hasher = Sha256::new();
        hasher.update(csv_data);
        format!("{:x}", hasher.finalize())[..12].to_string()
    }

    pub fn get_dataframe(&self, csv_hash: &str) -> Option<Arc<DataFrame>> {
        self.dataframe_cache.get(csv_hash).map(|df| df.clone())
    }

    pub fn insert_dataframe(&self, csv_hash: String, df: DataFrame) {
        // Simple cache management - keep only last 10 datasets
        if self.dataframe_cache.len() > 10 {
            if let Some(oldest_key) = self.dataframe_cache.iter().next().map(|entry| entry.key().clone()) {
                self.dataframe_cache.remove(&oldest_key);
            }
        }
        self.dataframe_cache.insert(csv_hash, Arc::new(df));
    }

    pub fn get_chart_cache_key(csv_data: &str, chart_type: &str) -> String {
        let csv_hash = Self::get_csv_hash(csv_data);
        format!("{}_{}", csv_hash, chart_type)
    }

    pub fn get_chart(&self, cache_key: &str) -> Option<serde_json::Value> {
        self.chart_cache.get(cache_key).map(|chart| chart.clone())
    }

    pub fn insert_chart(&self, cache_key: String, chart: serde_json::Value) {
        // Simple cache management - keep only last 50 charts
        if self.chart_cache.len() > 50 {
            if let Some(oldest_key) = self.chart_cache.iter().next().map(|entry| entry.key().clone()) {
                self.chart_cache.remove(&oldest_key);
            }
        }
        self.chart_cache.insert(cache_key, chart);
    }
}