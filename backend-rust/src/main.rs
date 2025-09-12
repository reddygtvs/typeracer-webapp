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
        .route("/charts/wpm-distribution", post(wpm_distribution_handler))
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

#[instrument]
async fn wpm_distribution_handler(
    State(state): State<Arc<AppState>>,
    Json(request): Json<crate::models::ChartRequest>,
) -> Result<Json<crate::models::ChartResponse>, StatusCode> {
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
    
    // Calculate mean and median WPM
    let mean_wpm = (*df).clone().lazy()
        .select([col("wpm").mean()])
        .collect()
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .column("wpm")
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .get(0)
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .try_extract::<f64>()
        .unwrap_or(0.0);
        
    let median_wpm = (*df).clone().lazy()
        .select([col("wpm").median()])
        .collect()
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .column("wpm")
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .get(0)
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .try_extract::<f64>()
        .unwrap_or(0.0);
    
    // Create identical plotly.js histogram JSON structure
    let wpm_values: Vec<f64> = (*df).clone()
        .column("wpm")
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .f64()
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .into_iter()
        .filter_map(|v| v)
        .collect();
    
    use serde_json::{json, Map, Value};
    
    // Build identical data structure to Python
    let mut data = Vec::new();
    let mut trace = Map::new();
    trace.insert("alignmentgroup".to_string(), json!("True"));
    trace.insert("bingroup".to_string(), json!("x"));
    trace.insert("hovertemplate".to_string(), json!("<b>%{x} WPM</b><br>Races: %{y}<br><extra></extra>"));
    trace.insert("legendgroup".to_string(), json!(""));
    trace.insert("marker".to_string(), json!({"color": "#39FF14", "pattern": {"shape": ""}}));
    trace.insert("name".to_string(), json!(""));
    trace.insert("nbinsx".to_string(), json!(15));
    trace.insert("offsetgroup".to_string(), json!(""));
    trace.insert("orientation".to_string(), json!("v"));
    trace.insert("showlegend".to_string(), json!(false));
    trace.insert("x".to_string(), Value::Array(wpm_values.iter().map(|&v| json!(v)).collect()));
    trace.insert("xaxis".to_string(), json!("x"));
    trace.insert("yaxis".to_string(), json!("y"));
    trace.insert("type".to_string(), json!("histogram"));
    
    data.push(trace);
    
    // Build layout structure identical to Python
    let mut layout = Map::new();
    layout.insert("template".to_string(), json!({"data":{"barpolar":[{"marker":{"line":{"color":"rgb(17,17,17)","width":0.5},"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"barpolar"}],"bar":[{"error_x":{"color":"#f2f5fa"},"error_y":{"color":"#f2f5fa"},"marker":{"line":{"color":"rgb(17,17,17)","width":0.5},"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"bar"}],"carpet":[{"aaxis":{"endlinecolor":"#A2B1C6","gridcolor":"#506784","linecolor":"#506784","minorgridcolor":"#506784","startlinecolor":"#A2B1C6"},"baxis":{"endlinecolor":"#A2B1C6","gridcolor":"#506784","linecolor":"#506784","minorgridcolor":"#506784","startlinecolor":"#A2B1C6"},"type":"carpet"}],"choropleth":[{"colorbar":{"outlinewidth":0,"ticks":""},"type":"choropleth"}],"contourcarpet":[{"colorbar":{"outlinewidth":0,"ticks":""},"type":"contourcarpet"}],"contour":[{"colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"type":"contour"}],"heatmapgl":[{"colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"type":"heatmapgl"}],"heatmap":[{"colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"type":"heatmap"}],"histogram2dcontour":[{"colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"type":"histogram2dcontour"}],"histogram2d":[{"colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"type":"histogram2d"}],"histogram":[{"marker":{"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"histogram"}],"mesh3d":[{"colorbar":{"outlinewidth":0,"ticks":""},"type":"mesh3d"}],"parcoords":[{"line":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"parcoords"}],"pie":[{"automargin":true,"type":"pie"}],"scatter3d":[{"line":{"colorbar":{"outlinewidth":0,"ticks":""}},"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scatter3d"}],"scattercarpet":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scattercarpet"}],"scattergeo":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scattergeo"}],"scattergl":[{"marker":{"line":{"color":"#283442"}},"type":"scattergl"}],"scattermapbox":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scattermapbox"}],"scatterpolargl":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scatterpolargl"}],"scatterpolar":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scatterpolar"}],"scatter":[{"marker":{"line":{"color":"#283442"}},"type":"scatter"}],"scatterternary":[{"marker":{"colorbar":{"outlinewidth":0,"ticks":""}},"type":"scatterternary"}],"surface":[{"colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"type":"surface"}],"table":[{"cells":{"fill":{"color":"#506784"},"line":{"color":"rgb(17,17,17)"}},"header":{"fill":{"color":"#2a3f5f"},"line":{"color":"rgb(17,17,17)"}},"type":"table"}]},"layout":{"annotationdefaults":{"arrowcolor":"#f2f5fa","arrowhead":0,"arrowwidth":1},"autotypenumbers":"strict","coloraxis":{"colorbar":{"outlinewidth":0,"ticks":""}},"colorscale":{"diverging":[[0,"#8e0152"],[0.1,"#c51b7d"],[0.2,"#de77ae"],[0.3,"#f1b6da"],[0.4,"#fde0ef"],[0.5,"#f7f7f7"],[0.6,"#e6f5d0"],[0.7,"#b8e186"],[0.8,"#7fbc41"],[0.9,"#4d9221"],[1,"#276419"]],"sequential":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"sequentialminus":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]},"colorway":["#636efa","#EF553B","#00cc96","#ab63fa","#FFA15A","#19d3f3","#FF6692","#B6E880","#FF97FF","#FECB52"],"font":{"color":"#f2f5fa"},"geo":{"bgcolor":"rgb(17,17,17)","lakecolor":"rgb(17,17,17)","landcolor":"rgb(17,17,17)","showlakes":true,"showland":true,"subunitcolor":"#506784"},"hoverlabel":{"align":"left"},"hovermode":"closest","mapbox":{"style":"dark"},"paper_bgcolor":"rgb(17,17,17)","plot_bgcolor":"rgb(17,17,17)","polar":{"angularaxis":{"gridcolor":"#506784","linecolor":"#506784","ticks":""},"bgcolor":"rgb(17,17,17)","radialaxis":{"gridcolor":"#506784","linecolor":"#506784","ticks":""}},"scene":{"xaxis":{"backgroundcolor":"rgb(17,17,17)","gridcolor":"#506784","gridwidth":2,"linecolor":"#506784","showbackground":true,"ticks":"","zerolinecolor":"#C8D4E3"},"yaxis":{"backgroundcolor":"rgb(17,17,17)","gridcolor":"#506784","gridwidth":2,"linecolor":"#506784","showbackground":true,"ticks":"","zerolinecolor":"#C8D4E3"},"zaxis":{"backgroundcolor":"rgb(17,17,17)","gridcolor":"#506784","gridwidth":2,"linecolor":"#506784","showbackground":true,"ticks":"","zerolinecolor":"#C8D4E3"}},"shapedefaults":{"line":{"color":"#f2f5fa"}},"sliderdefaults":{"bgcolor":"#C8D4E3","bordercolor":"rgb(17,17,17)","borderwidth":1,"tickwidth":0},"ternary":{"aaxis":{"gridcolor":"#506784","linecolor":"#506784","ticks":""},"baxis":{"gridcolor":"#506784","linecolor":"#506784","ticks":""},"bgcolor":"rgb(17,17,17)","caxis":{"gridcolor":"#506784","linecolor":"#506784","ticks":""}},"title":{"x":0.05},"updatemenudefaults":{"bgcolor":"#506784","borderwidth":0},"xaxis":{"automargin":true,"gridcolor":"#283442","linecolor":"#506784","ticks":"","title":{"standoff":15},"zerolinecolor":"#283442","zerolinewidth":2},"yaxis":{"automargin":true,"gridcolor":"#283442","linecolor":"#506784","ticks":"","title":{"standoff":15},"zerolinecolor":"#283442","zerolinewidth":2}}}));
    
    layout.insert("xaxis".to_string(), json!({
        "anchor": "y",
        "domain": [0.0, 1.0],
        "title": {"text": "Words Per Minute", "font": {"color": "rgb(181, 179, 173)"}},
        "tickfont": {"color": "rgb(181, 179, 173)"},
        "gridcolor": "rgb(55, 55, 53)"
    }));
    
    layout.insert("yaxis".to_string(), json!({
        "anchor": "x",
        "domain": [0.0, 1.0],
        "title": {"text": "count", "font": {"color": "rgb(181, 179, 173)"}},
        "tickfont": {"color": "rgb(181, 179, 173)"},
        "gridcolor": "rgb(55, 55, 53)"
    }));
    
    layout.insert("legend".to_string(), json!({"tracegroupgap": 0}));
    layout.insert("title".to_string(), json!({
        "text": format!("WPM Distribution (Mean: {:.1}, Median: {:.1})", mean_wpm, median_wpm),
        "font": {"color": "white"}
    }));
    layout.insert("barmode".to_string(), json!("relative"));
    
    // Add shapes for mean and median lines
    layout.insert("shapes".to_string(), json!([
        {
            "line": {"color": "#FF6B6B", "dash": "dash", "width": 2},
            "type": "line",
            "x0": mean_wpm,
            "x1": mean_wpm,
            "xref": "x",
            "y0": 0,
            "y1": 1,
            "yref": "y domain"
        },
        {
            "line": {"color": "#74B9FF", "dash": "dot", "width": 2},
            "type": "line", 
            "x0": median_wpm,
            "x1": median_wpm,
            "xref": "x",
            "y0": 0,
            "y1": 1,
            "yref": "y domain"
        }
    ]));
    
    layout.insert("font".to_string(), json!({"family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, system-ui, sans-serif"}));
    layout.insert("height".to_string(), json!(400));
    layout.insert("paper_bgcolor".to_string(), json!("rgba(0,0,0,0)"));
    layout.insert("plot_bgcolor".to_string(), json!("rgba(0,0,0,0)"));
    layout.insert("showlegend".to_string(), json!(false));
    
    // Generate insights identical to Python
    let mut insights = Vec::new();
    insights.push(format!("Your average typing speed is {:.1} WPM", mean_wpm));
    
    // Calculate most common WPM range
    let min_wpm = wpm_values.iter().copied().fold(f64::INFINITY, f64::min);
    let max_wpm = wpm_values.iter().copied().fold(f64::NEG_INFINITY, f64::max);
    let range_size = (max_wpm - min_wpm) / 15.0; // 15 bins
    let mut most_common_count = 0;
    let mut most_common_range = (0.0, 0.0);
    
    for i in 0..15 {
        let range_start = min_wpm + i as f64 * range_size;
        let range_end = range_start + range_size;
        let count = wpm_values.iter().filter(|&&v| v >= range_start && v < range_end).count();
        if count > most_common_count {
            most_common_count = count;
            most_common_range = (range_start, range_end);
        }
    }
    
    insights.push(format!("Most races fall between {:.0}-{:.0} WPM range", most_common_range.0, most_common_range.1));
    
    // Top 10% threshold
    let mut sorted_wpm = wpm_values.clone();
    sorted_wpm.sort_by(|a, b| b.partial_cmp(a).unwrap());
    let top_10_percent_idx = (sorted_wpm.len() as f64 * 0.1) as usize;
    let top_10_threshold = sorted_wpm[top_10_percent_idx.min(sorted_wpm.len() - 1)];
    insights.push(format!("You need {:.1}+ WPM to reach your top 10% performances", top_10_threshold));
    
    // Bottom 10% threshold
    let bottom_10_percent_idx = (sorted_wpm.len() as f64 * 0.9) as usize;
    let bottom_10_threshold = sorted_wpm[bottom_10_percent_idx.min(sorted_wpm.len() - 1)];
    insights.push(format!("Your slowest 10% of races are below {:.1} WPM", bottom_10_threshold));
    
    // Standard deviation
    let variance: f64 = wpm_values.iter().map(|v| {
        let diff = v - mean_wpm;
        diff * diff
    }).sum::<f64>() / wpm_values.len() as f64;
    let std_dev = variance.sqrt();
    insights.push(format!("Speed consistency: ±{:.1} WPM standard deviation", std_dev));
    
    // Fast and learning races count
    let fast_races = wpm_values.iter().filter(|&&v| v >= 100.0).count();
    let learning_races = wpm_values.iter().filter(|&&v| v < 40.0).count();
    insights.push(format!("Fast races (100+ WPM): {} times, Learning races (<40 WPM): {} times", fast_races, learning_races));
    
    let response = crate::models::ChartResponse {
        data: serde_json::Value::Array(data.into_iter().map(|m| serde_json::Value::Object(m)).collect()),
        layout: serde_json::Value::Object(layout),
        insights,
        has_insights: true,
    };
    
    Ok(Json(response))
}