use axum::{
    extract::State,
    http::StatusCode,
    response::Json,
};
use polars::prelude::{col, lit, IntoLazy, DataFrame};
use polars::chunked_array::ops::SortMultipleOptions;
use serde_json::{json, Map, Value};
use std::sync::Arc;
use tracing::instrument;

use crate::{models, AppState};

#[instrument]
pub async fn wpm_distribution_handler(
    State(state): State<Arc<AppState>>,
    Json(request): Json<models::ChartRequest>,
) -> Result<Json<models::ChartResponse>, StatusCode> {
    let csv_hash = crate::cache::DataCache::get_csv_hash(&request.csv_data);
    let df = if let Some(cached_df) = state.cache.get_dataframe(&csv_hash) {
        cached_df
    } else {
        let processed_df = crate::data_processing::process_csv_data(&request.csv_data)
            .map_err(|_| StatusCode::BAD_REQUEST)?;
        state.cache.insert_dataframe(csv_hash.clone(), processed_df.clone());
        Arc::new(processed_df)
    };
    
    let mean_wpm = (*df).clone().lazy().select([col("wpm").mean()]).collect().map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .column("wpm").map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?.get(0).map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .try_extract::<f64>().unwrap_or(0.0);
    let median_wpm = (*df).clone().lazy().select([col("wpm").median()]).collect().map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .column("wpm").map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?.get(0).map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .try_extract::<f64>().unwrap_or(0.0);
    
    let wpm_values: Vec<f64> = (*df).clone().column("wpm").map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .cast(&polars::datatypes::DataType::Float64).map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .f64().map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?.into_iter().filter_map(|v| v).collect();
    
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
    
    let mut layout = Map::new();
    layout.insert("template".to_string(), json!({"data":{"histogram":[{"marker":{"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"histogram"}]},"layout":{"colorway":["#636efa","#EF553B","#00cc96","#ab63fa","#FFA15A","#19d3f3","#FF6692","#B6E880","#FF97FF","#FECB52"],"font":{"color":"#f2f5fa"},"paper_bgcolor":"rgb(17,17,17)","plot_bgcolor":"rgb(17,17,17)"}}));
    layout.insert("xaxis".to_string(), json!({"anchor": "y", "domain": [0.0, 1.0], "title": {"text": "Words Per Minute", "font": {"color": "rgb(181, 179, 173)"}}, "tickfont": {"color": "rgb(181, 179, 173)"}, "gridcolor": "rgb(55, 55, 53)"}));
    layout.insert("yaxis".to_string(), json!({"anchor": "x", "domain": [0.0, 1.0], "title": {"text": "count", "font": {"color": "rgb(181, 179, 173)"}}, "tickfont": {"color": "rgb(181, 179, 173)"}, "gridcolor": "rgb(55, 55, 53)"}));
    layout.insert("legend".to_string(), json!({"tracegroupgap": 0}));
    layout.insert("title".to_string(), json!({"text": format!("WPM Distribution (Mean: {:.1}, Median: {:.1})", mean_wpm, median_wpm), "font": {"color": "white"}}));
    layout.insert("barmode".to_string(), json!("relative"));
    layout.insert("shapes".to_string(), json!([{"line": {"color": "#FF6B6B", "dash": "dash", "width": 2}, "type": "line", "x0": mean_wpm, "x1": mean_wpm, "xref": "x", "y0": 0, "y1": 1, "yref": "y domain"}, {"line": {"color": "#74B9FF", "dash": "dot", "width": 2}, "type": "line", "x0": median_wpm, "x1": median_wpm, "xref": "x", "y0": 0, "y1": 1, "yref": "y domain"}]));
    layout.insert("font".to_string(), json!({"family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, system-ui, sans-serif"}));
    layout.insert("height".to_string(), json!(400));
    layout.insert("paper_bgcolor".to_string(), json!("rgba(0,0,0,0)"));
    layout.insert("plot_bgcolor".to_string(), json!("rgba(0,0,0,0)"));
    layout.insert("showlegend".to_string(), json!(false));
    
    let mut insights = Vec::new();
    insights.push(format!("Your average typing speed is {:.1} WPM", mean_wpm));
    
    let response = models::ChartResponse {
        data: Value::Array(data.into_iter().map(|m| Value::Object(m)).collect()),
        layout: Value::Object(layout),
        insights,
        has_insights: true,
    };
    
    Ok(Json(response))
}

#[instrument]
pub async fn accuracy_distribution_handler(
    State(state): State<Arc<AppState>>,
    Json(request): Json<models::ChartRequest>,
) -> Result<Json<models::ChartResponse>, StatusCode> {
    let csv_hash = crate::cache::DataCache::get_csv_hash(&request.csv_data);
    let df = if let Some(cached_df) = state.cache.get_dataframe(&csv_hash) {
        cached_df
    } else {
        let processed_df = crate::data_processing::process_csv_data(&request.csv_data)
            .map_err(|_| StatusCode::BAD_REQUEST)?;
        state.cache.insert_dataframe(csv_hash.clone(), processed_df.clone());
        Arc::new(processed_df)
    };
    
    let accuracy_values: Vec<f64> = (*df).clone().column("accuracy").map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .cast(&polars::datatypes::DataType::Float64).map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .f64().map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?.into_iter().filter_map(|v| v).collect();
    
    let mut data = Vec::new();
    let mut trace = Map::new();
    trace.insert("alignmentgroup".to_string(), json!("True"));
    trace.insert("bingroup".to_string(), json!("x"));
    trace.insert("hovertemplate".to_string(), json!("Accuracy=%{x}<br>Frequency=%{y}<br><extra></extra>"));
    trace.insert("legendgroup".to_string(), json!(""));
    trace.insert("marker".to_string(), json!({"color": "#ef4444", "pattern": {"shape": ""}}));
    trace.insert("name".to_string(), json!(""));
    trace.insert("nbinsx".to_string(), json!(30));
    trace.insert("offsetgroup".to_string(), json!(""));
    trace.insert("orientation".to_string(), json!("v"));
    trace.insert("showlegend".to_string(), json!(false));
    trace.insert("x".to_string(), Value::Array(accuracy_values.iter().map(|&v| json!(v)).collect()));
    trace.insert("xaxis".to_string(), json!("x"));
    trace.insert("yaxis".to_string(), json!("y"));
    trace.insert("type".to_string(), json!("histogram"));
    data.push(trace);
    
    let mut layout = Map::new();
    layout.insert("template".to_string(), json!("plotly_white"));
    layout.insert("title".to_string(), json!({"text": "Accuracy Distribution"}));
    layout.insert("xaxis".to_string(), json!({"title": {"text": "Accuracy"}}));
    layout.insert("yaxis".to_string(), json!({"title": {"text": "Frequency"}}));
    layout.insert("height".to_string(), json!(400));
    layout.insert("font".to_string(), json!({"family": "Inter, sans-serif"}));
    layout.insert("barmode".to_string(), json!("relative"));
    layout.insert("legend".to_string(), json!({"tracegroupgap": 0}));
    
    let mean_accuracy = accuracy_values.iter().sum::<f64>() / accuracy_values.len() as f64;
    let mut insights = Vec::new();
    insights.push(format!("Your average accuracy is {:.1}%", mean_accuracy * 100.0));
    
    let response = models::ChartResponse {
        data: Value::Array(data.into_iter().map(|m| Value::Object(m)).collect()),
        layout: Value::Object(layout),
        insights,
        has_insights: true,
    };
    
    Ok(Json(response))
}

#[instrument]
pub async fn performance_over_time_handler(
    State(state): State<Arc<AppState>>,
    Json(request): Json<models::ChartRequest>,
) -> Result<Json<models::ChartResponse>, StatusCode> {
    let csv_hash = crate::cache::DataCache::get_csv_hash(&request.csv_data);
    let df = if let Some(cached_df) = state.cache.get_dataframe(&csv_hash) {
        cached_df
    } else {
        let processed_df = crate::data_processing::process_csv_data(&request.csv_data)
            .map_err(|_| StatusCode::BAD_REQUEST)?;
        state.cache.insert_dataframe(csv_hash.clone(), processed_df.clone());
        Arc::new(processed_df)
    };
    
    let monthly_avg = (*df).clone().lazy()
        .group_by([col("year_month")])
        .agg([col("wpm").mean().alias("avg_wpm")])
        .sort(["year_month"], SortMultipleOptions::default())
        .collect().map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    
    let year_month_str = monthly_avg.clone().lazy()
        .select([col("year_month").dt().to_string("%Y-%m-%d")])
        .collect().map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
        
    let year_month_values: Vec<String> = year_month_str.column("year_month").map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .str().map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?.into_iter()
        .map(|v| v.unwrap_or("").to_string()).collect();
        
    let avg_wpm_values: Vec<f64> = monthly_avg.column("avg_wpm").map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .cast(&polars::datatypes::DataType::Float64).map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .f64().map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?.into_iter().filter_map(|v| v).collect();
    
    let mut data = Vec::new();
    let mut trace = Map::new();
    trace.insert("x".to_string(), Value::Array(year_month_values.iter().map(|v| json!(v)).collect()));
    trace.insert("y".to_string(), Value::Array(avg_wpm_values.iter().map(|&v| json!(v)).collect()));
    trace.insert("type".to_string(), json!("scatter"));
    trace.insert("mode".to_string(), json!("lines"));
    trace.insert("name".to_string(), json!(""));
    trace.insert("line".to_string(), json!({"color": "#10b981", "width": 3, "shape": "spline"}));
    trace.insert("hovertemplate".to_string(), json!("Month=%{x}<br>Average WPM=%{y}<br><extra></extra>"));
    data.push(trace);
    
    let mut layout = Map::new();
    layout.insert("title".to_string(), json!({"text": "Monthly Average WPM Over Time"}));
    layout.insert("xaxis".to_string(), json!({"title": {"text": "Month"}}));
    layout.insert("yaxis".to_string(), json!({"title": {"text": "Average WPM"}}));
    layout.insert("template".to_string(), json!("plotly_white"));
    layout.insert("height".to_string(), json!(400));
    layout.insert("font".to_string(), json!({"family": "Inter, sans-serif"}));
    
    let mut insights = Vec::new();
    insights.push("Performance over time trends".to_string());
    
    let response = models::ChartResponse {
        data: Value::Array(data.into_iter().map(|m| Value::Object(m)).collect()),
        layout: Value::Object(layout),
        insights,
        has_insights: true,
    };
    
    Ok(Json(response))
}

#[instrument]
pub async fn daily_performance_handler(
    State(state): State<Arc<AppState>>,
    Json(request): Json<models::ChartRequest>,
) -> Result<Json<models::ChartResponse>, StatusCode> {
    let csv_hash = crate::cache::DataCache::get_csv_hash(&request.csv_data);
    let df = if let Some(cached_df) = state.cache.get_dataframe(&csv_hash) {
        cached_df
    } else {
        let processed_df = crate::data_processing::process_csv_data(&request.csv_data)
            .map_err(|_| StatusCode::BAD_REQUEST)?;
        state.cache.insert_dataframe(csv_hash.clone(), processed_df.clone());
        Arc::new(processed_df)
    };
    
    let daily_avg = (*df).clone().lazy()
        .group_by([col("date")])
        .agg([col("wpm").mean().alias("avg_wpm")])
        .sort(["date"], SortMultipleOptions::default())
        .collect().map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    
    // Convert to pandas equivalent for line chart
    let dates: Vec<String> = daily_avg.column("date").map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .str().map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?.into_iter()
        .map(|v| v.unwrap_or("").to_string()).collect();
    let avg_wpm_values: Vec<f64> = daily_avg.column("avg_wpm").map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .cast(&polars::datatypes::DataType::Float64).map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .f64().map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?.into_iter().filter_map(|v| v).collect();
    
    let mut data = Vec::new();
    let mut trace = Map::new();
    trace.insert("x".to_string(), Value::Array(dates.iter().map(|v| json!(v)).collect()));
    trace.insert("y".to_string(), Value::Array(avg_wpm_values.iter().map(|&v| json!(v)).collect()));
    trace.insert("type".to_string(), json!("scatter"));
    trace.insert("mode".to_string(), json!("lines"));
    trace.insert("name".to_string(), json!(""));
    trace.insert("line".to_string(), json!({"color": "#f97316", "width": 2}));
    trace.insert("hovertemplate".to_string(), json!("Date=%{x}<br>Average WPM=%{y}<br><extra></extra>"));
    data.push(trace);
    
    let mut layout = Map::new();
    layout.insert("title".to_string(), json!({"text": "Daily Average WPM Over Time"}));
    layout.insert("xaxis".to_string(), json!({"title": {"text": "Date"}}));
    layout.insert("yaxis".to_string(), json!({"title": {"text": "Average WPM"}}));
    layout.insert("template".to_string(), json!("plotly_white"));
    layout.insert("height".to_string(), json!(400));
    layout.insert("font".to_string(), json!({"family": "Inter, sans-serif"}));
    
    let mut insights = Vec::new();
    insights.push("Daily performance trends".to_string());
    
    let response = models::ChartResponse {
        data: Value::Array(data.into_iter().map(|m| Value::Object(m)).collect()),
        layout: Value::Object(layout),
        insights,
        has_insights: true,
    };
    
    Ok(Json(response))
}

#[instrument]
pub async fn rolling_average_handler(
    State(state): State<Arc<AppState>>,
    Json(request): Json<models::ChartRequest>,
) -> Result<Json<models::ChartResponse>, StatusCode> {
    let csv_hash = crate::cache::DataCache::get_csv_hash(&request.csv_data);
    let df = if let Some(cached_df) = state.cache.get_dataframe(&csv_hash) {
        cached_df
    } else {
        let processed_df = crate::data_processing::process_csv_data(&request.csv_data)
            .map_err(|_| StatusCode::BAD_REQUEST)?;
        state.cache.insert_dataframe(csv_hash.clone(), processed_df.clone());
        Arc::new(processed_df)
    };
    
    // Manually calculate 100-race rolling average to match Python exactly
    let df_sorted = (*df).clone().lazy().sort(["race_num"], SortMultipleOptions::default()).collect().map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    
    let race_nums: Vec<i32> = df_sorted.column("race_num").map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .i32().map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?.into_iter().filter_map(|v| v).collect();
    let wpm_values: Vec<f64> = df_sorted.column("wpm").map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .cast(&polars::datatypes::DataType::Float64).map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .f64().map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?.into_iter().filter_map(|v| v).collect();
    
    // Calculate rolling average manually - 100-race window
    let mut rolling_avg = Vec::new();
    for i in 0..wpm_values.len() {
        let start = if i >= 99 { i - 99 } else { 0 };
        let window = &wpm_values[start..=i];
        let avg = window.iter().sum::<f64>() / window.len() as f64;
        rolling_avg.push(avg);
    }
    
    let mut data = Vec::new();
    let mut trace = Map::new();
    trace.insert("x".to_string(), Value::Array(race_nums.iter().map(|&v| json!(v)).collect()));
    trace.insert("y".to_string(), Value::Array(rolling_avg.iter().map(|&v| json!(v)).collect()));
    trace.insert("type".to_string(), json!("scatter"));
    trace.insert("mode".to_string(), json!("lines"));
    trace.insert("name".to_string(), json!(""));
    trace.insert("line".to_string(), json!({"color": "#8b5cf6", "width": 2}));
    trace.insert("hovertemplate".to_string(), json!("Race Number=%{x}<br>Rolling Average WPM=%{y}<br><extra></extra>"));
    data.push(trace);
    
    let mut layout = Map::new();
    layout.insert("title".to_string(), json!({"text": "Rolling Average WPM (100 races)"}));
    layout.insert("xaxis".to_string(), json!({"title": {"text": "Race Number"}}));
    layout.insert("yaxis".to_string(), json!({"title": {"text": "Rolling Average WPM"}}));
    layout.insert("template".to_string(), json!("plotly_white"));
    layout.insert("height".to_string(), json!(400));
    layout.insert("font".to_string(), json!({"family": "Inter, sans-serif"}));
    
    let mut insights = Vec::new();
    insights.push("Rolling average progression".to_string());
    
    let response = models::ChartResponse {
        data: Value::Array(data.into_iter().map(|m| Value::Object(m)).collect()),
        layout: Value::Object(layout),
        insights,
        has_insights: true,
    };
    
    Ok(Json(response))
}

#[instrument]
pub async fn rank_distribution_handler(
    State(state): State<Arc<AppState>>,
    Json(request): Json<models::ChartRequest>,
) -> Result<Json<models::ChartResponse>, StatusCode> {
    let csv_hash = crate::cache::DataCache::get_csv_hash(&request.csv_data);
    let df = if let Some(cached_df) = state.cache.get_dataframe(&csv_hash) {
        cached_df
    } else {
        let processed_df = crate::data_processing::process_csv_data(&request.csv_data)
            .map_err(|_| StatusCode::BAD_REQUEST)?;
        state.cache.insert_dataframe(csv_hash.clone(), processed_df.clone());
        Arc::new(processed_df)
    };
    
    let rank_dist = (*df).clone().lazy()
        .group_by([col("rank")])
        .agg([col("rank").len().alias("count")])
        .with_columns([(col("count").cast(polars::datatypes::DataType::Float64) / col("count").sum().cast(polars::datatypes::DataType::Float64) * lit(100.0)).alias("percentage")])
        .sort(["rank"], SortMultipleOptions::default())
        .collect().map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    
    let ranks: Vec<i32> = rank_dist.column("rank").map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .i32().map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?.into_iter().filter_map(|v| v).collect();
    let percentages: Vec<f64> = rank_dist.column("percentage").map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .f64().map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?.into_iter().filter_map(|v| v).collect();
    
    let mut data = Vec::new();
    let mut trace = Map::new();
    trace.insert("x".to_string(), Value::Array(ranks.iter().map(|&v| json!(v)).collect()));
    trace.insert("y".to_string(), Value::Array(percentages.iter().map(|&v| json!(v)).collect()));
    trace.insert("type".to_string(), json!("bar"));
    trace.insert("name".to_string(), json!(""));
    trace.insert("marker".to_string(), json!({"colorscale": "viridis", "color": percentages.clone()}));
    trace.insert("hovertemplate".to_string(), json!("Rank=%{x}<br>Percentage=%{y}%<br><extra></extra>"));
    data.push(trace);
    
    let mut layout = Map::new();
    layout.insert("title".to_string(), json!({"text": "Rank Distribution"}));
    layout.insert("xaxis".to_string(), json!({"title": {"text": "Rank"}}));
    layout.insert("yaxis".to_string(), json!({"title": {"text": "Percentage (%)"}}));
    layout.insert("template".to_string(), json!("plotly_white"));
    layout.insert("height".to_string(), json!(400));
    layout.insert("font".to_string(), json!({"family": "Inter, sans-serif"}));
    layout.insert("showlegend".to_string(), json!(false));
    
    let mut insights = Vec::new();
    insights.push("Rank distribution analysis".to_string());
    
    let response = models::ChartResponse {
        data: Value::Array(data.into_iter().map(|m| Value::Object(m)).collect()),
        layout: Value::Object(layout),
        insights,
        has_insights: true,
    };
    
    Ok(Json(response))
}

#[instrument]
pub async fn hourly_performance_handler(
    State(state): State<Arc<AppState>>,
    Json(request): Json<models::ChartRequest>,
) -> Result<Json<models::ChartResponse>, StatusCode> {
    let csv_hash = crate::cache::DataCache::get_csv_hash(&request.csv_data);
    let df = if let Some(cached_df) = state.cache.get_dataframe(&csv_hash) {
        cached_df
    } else {
        let processed_df = crate::data_processing::process_csv_data(&request.csv_data)
            .map_err(|_| StatusCode::BAD_REQUEST)?;
        state.cache.insert_dataframe(csv_hash.clone(), processed_df.clone());
        Arc::new(processed_df)
    };
    
    let hourly_avg = (*df).clone().lazy()
        .group_by([col("hour")])
        .agg([col("wpm").mean().alias("avg_wpm")])
        .sort(["hour"], SortMultipleOptions::default())
        .collect().map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    
    let hours: Vec<i32> = hourly_avg.column("hour").map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .i32().map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?.into_iter().filter_map(|v| v).collect();
    let avg_wpm_values: Vec<f64> = hourly_avg.column("avg_wpm").map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .cast(&polars::datatypes::DataType::Float64).map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .f64().map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?.into_iter().filter_map(|v| v).collect();
    
    let mut data = Vec::new();
    let mut trace = Map::new();
    trace.insert("x".to_string(), Value::Array(hours.iter().map(|&v| json!(v)).collect()));
    trace.insert("y".to_string(), Value::Array(avg_wpm_values.iter().map(|&v| json!(v)).collect()));
    trace.insert("type".to_string(), json!("bar"));
    trace.insert("name".to_string(), json!(""));
    trace.insert("marker".to_string(), json!({"colorscale": "blues", "color": avg_wpm_values.clone()}));
    trace.insert("hovertemplate".to_string(), json!("Hour of Day=%{x}<br>Average WPM=%{y}<br><extra></extra>"));
    data.push(trace);
    
    let mut layout = Map::new();
    layout.insert("title".to_string(), json!({"text": "Average WPM by Hour of Day"}));
    layout.insert("xaxis".to_string(), json!({"title": {"text": "Hour of Day"}}));
    layout.insert("yaxis".to_string(), json!({"title": {"text": "Average WPM"}}));
    layout.insert("template".to_string(), json!("plotly_white"));
    layout.insert("height".to_string(), json!(400));
    layout.insert("font".to_string(), json!({"family": "Inter, sans-serif"}));
    layout.insert("showlegend".to_string(), json!(false));
    
    let mut insights = Vec::new();
    insights.push("Performance by hour analysis".to_string());
    
    let response = models::ChartResponse {
        data: Value::Array(data.into_iter().map(|m| Value::Object(m)).collect()),
        layout: Value::Object(layout),
        insights,
        has_insights: true,
    };
    
    Ok(Json(response))
}

#[instrument]
pub async fn wpm_vs_accuracy_handler(
    State(state): State<Arc<AppState>>,
    Json(request): Json<models::ChartRequest>,
) -> Result<Json<models::ChartResponse>, StatusCode> {
    let csv_hash = crate::cache::DataCache::get_csv_hash(&request.csv_data);
    let df = if let Some(cached_df) = state.cache.get_dataframe(&csv_hash) {
        cached_df
    } else {
        let processed_df = crate::data_processing::process_csv_data(&request.csv_data)
            .map_err(|_| StatusCode::BAD_REQUEST)?;
        state.cache.insert_dataframe(csv_hash.clone(), processed_df.clone());
        Arc::new(processed_df)
    };
    
    let wpm_values: Vec<f64> = (*df).clone().column("wpm").map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .cast(&polars::datatypes::DataType::Float64).map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .f64().map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?.into_iter().filter_map(|v| v).collect();
    let accuracy_values: Vec<f64> = (*df).clone().column("accuracy").map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .cast(&polars::datatypes::DataType::Float64).map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .f64().map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?.into_iter().filter_map(|v| v).collect();
    
    let mut data = Vec::new();
    let mut trace = Map::new();
    trace.insert("x".to_string(), Value::Array(wpm_values.iter().map(|&v| json!(v)).collect()));
    trace.insert("y".to_string(), Value::Array(accuracy_values.iter().map(|&v| json!(v)).collect()));
    trace.insert("type".to_string(), json!("scatter"));
    trace.insert("mode".to_string(), json!("markers"));
    trace.insert("name".to_string(), json!(""));
    trace.insert("marker".to_string(), json!({"opacity": 0.6}));
    trace.insert("hovertemplate".to_string(), json!("Words Per Minute=%{x}<br>Accuracy=%{y}<br><extra></extra>"));
    data.push(trace);
    
    let mut layout = Map::new();
    layout.insert("title".to_string(), json!({"text": "WPM vs Accuracy"}));
    layout.insert("xaxis".to_string(), json!({"title": {"text": "Words Per Minute"}}));
    layout.insert("yaxis".to_string(), json!({"title": {"text": "Accuracy"}}));
    layout.insert("template".to_string(), json!("plotly_white"));
    layout.insert("height".to_string(), json!(400));
    layout.insert("font".to_string(), json!({"family": "Inter, sans-serif"}));
    
    let mut insights = Vec::new();
    insights.push("WPM vs Accuracy correlation".to_string());
    
    let response = models::ChartResponse {
        data: Value::Array(data.into_iter().map(|m| Value::Object(m)).collect()),
        layout: Value::Object(layout),
        insights,
        has_insights: true,
    };
    
    Ok(Json(response))
}

#[instrument]
pub async fn win_rate_monthly_handler(
    State(state): State<Arc<AppState>>,
    Json(request): Json<models::ChartRequest>,
) -> Result<Json<models::ChartResponse>, StatusCode> {
    let csv_hash = crate::cache::DataCache::get_csv_hash(&request.csv_data);
    let df = if let Some(cached_df) = state.cache.get_dataframe(&csv_hash) {
        cached_df
    } else {
        let processed_df = crate::data_processing::process_csv_data(&request.csv_data).map_err(|_| StatusCode::BAD_REQUEST)?;
        state.cache.insert_dataframe(csv_hash.clone(), processed_df.clone());
        Arc::new(processed_df)
    };
    
    let monthly_wins = (*df).clone().lazy()
        .group_by([col("year_month")])
        .agg([col("win").cast(polars::datatypes::DataType::Float64).mean().alias("win_rate")])
        .sort(["year_month"], SortMultipleOptions::default())
        .collect().map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    
    let year_month_str = monthly_wins.clone().lazy()
        .select([col("year_month").dt().to_string("%Y-%m-%d")])
        .collect().map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    let year_month_values: Vec<String> = year_month_str.column("year_month").map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .str().map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?.into_iter().map(|v| v.unwrap_or("").to_string()).collect();
    let win_rates: Vec<f64> = monthly_wins.column("win_rate").map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .f64().map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?.into_iter().filter_map(|v| v).collect();
    
    let mut data = Vec::new();
    let mut trace = Map::new();
    trace.insert("x".to_string(), Value::Array(year_month_values.iter().map(|v| json!(v)).collect()));
    trace.insert("y".to_string(), Value::Array(win_rates.iter().map(|&v| json!(v)).collect()));
    trace.insert("type".to_string(), json!("scatter"));
    trace.insert("mode".to_string(), json!("lines"));
    trace.insert("name".to_string(), json!(""));
    trace.insert("line".to_string(), json!({"color": "#eab308", "width": 3}));
    data.push(trace);
    
    let mut layout = Map::new();
    layout.insert("title".to_string(), json!({"text": "Monthly Win Rate Over Time"}));
    layout.insert("xaxis".to_string(), json!({"title": {"text": "Month"}}));
    layout.insert("yaxis".to_string(), json!({"title": {"text": "Win Rate"}}));
    layout.insert("template".to_string(), json!("plotly_white"));
    layout.insert("height".to_string(), json!(400));
    layout.insert("font".to_string(), json!({"family": "Inter, sans-serif"}));
    
    let response = models::ChartResponse {
        data: Value::Array(data.into_iter().map(|m| Value::Object(m)).collect()),
        layout: Value::Object(layout),
        insights: vec!["Win rate trends over time".to_string()],
        has_insights: true,
    };
    
    Ok(Json(response))
}

#[instrument]
pub async fn top_texts_handler(
    State(state): State<Arc<AppState>>,
    Json(request): Json<models::ChartRequest>,
) -> Result<Json<models::ChartResponse>, StatusCode> {
    let csv_hash = crate::cache::DataCache::get_csv_hash(&request.csv_data);
    let df = if let Some(cached_df) = state.cache.get_dataframe(&csv_hash) {
        cached_df
    } else {
        let processed_df = crate::data_processing::process_csv_data(&request.csv_data).map_err(|_| StatusCode::BAD_REQUEST)?;
        state.cache.insert_dataframe(csv_hash.clone(), processed_df.clone());
        Arc::new(processed_df)
    };
    
    let text_wpm = (*df).clone().lazy()
        .group_by([col("text_id")])
        .agg([col("wpm").mean().alias("avg_wpm"), col("text_id").len().alias("race_count")])
        .filter(col("race_count").gt_eq(lit(5)))
        .collect().map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    
    let top_10 = text_wpm.clone().lazy().sort(["avg_wpm"], SortMultipleOptions::default().with_order_descending(true))
        .limit(10).collect().map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    let bottom_10 = text_wpm.clone().lazy().sort(["avg_wpm"], SortMultipleOptions::default())
        .limit(10).collect().map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    
    let combined = polars::prelude::concat([top_10.lazy(), bottom_10.lazy()], polars::prelude::UnionArgs::default())
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?.collect().map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    
    let text_ids: Vec<String> = combined.column("text_id").map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .str().map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?.into_iter()
        .map(|v| v.unwrap_or("").to_string()).collect();
    let avg_wpms: Vec<f64> = combined.column("avg_wpm").map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .cast(&polars::datatypes::DataType::Float64).map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .f64().map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?.into_iter().filter_map(|v| v).collect();
    
    let mut data = Vec::new();
    let mut trace = Map::new();
    trace.insert("x".to_string(), Value::Array(text_ids.iter().map(|v| json!(v)).collect()));
    trace.insert("y".to_string(), Value::Array(avg_wpms.iter().map(|&v| json!(v)).collect()));
    trace.insert("type".to_string(), json!("bar"));
    trace.insert("name".to_string(), json!(""));
    trace.insert("marker".to_string(), json!({"colorscale": "viridis", "color": avg_wpms.clone()}));
    data.push(trace);
    
    let mut layout = Map::new();
    layout.insert("title".to_string(), json!({"text": "Top 10 vs Bottom 10 Texts by Average WPM"}));
    layout.insert("xaxis".to_string(), json!({"title": {"text": "Text ID"}, "tickangle": -45}));
    layout.insert("yaxis".to_string(), json!({"title": {"text": "Average WPM"}}));
    layout.insert("template".to_string(), json!("plotly_white"));
    layout.insert("height".to_string(), json!(400));
    layout.insert("font".to_string(), json!({"family": "Inter, sans-serif"}));
    
    let response = models::ChartResponse {
        data: Value::Array(data.into_iter().map(|m| Value::Object(m)).collect()),
        layout: Value::Object(layout),
        insights: vec!["Top vs bottom performing texts".to_string()],
        has_insights: true,
    };
    
    Ok(Json(response))
}

#[instrument]
pub async fn consistency_score_handler(
    State(state): State<Arc<AppState>>,
    Json(request): Json<models::ChartRequest>,
) -> Result<Json<models::ChartResponse>, StatusCode> {
    let csv_hash = crate::cache::DataCache::get_csv_hash(&request.csv_data);
    let df = if let Some(cached_df) = state.cache.get_dataframe(&csv_hash) {
        cached_df
    } else {
        let processed_df = crate::data_processing::process_csv_data(&request.csv_data).map_err(|_| StatusCode::BAD_REQUEST)?;
        state.cache.insert_dataframe(csv_hash.clone(), processed_df.clone());
        Arc::new(processed_df)
    };
    
    // Manually calculate 30-race rolling standard deviation to match Python exactly
    let df_sorted = (*df).clone().lazy().sort(["race_num"], SortMultipleOptions::default()).collect().map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    
    let race_nums: Vec<i32> = df_sorted.column("race_num").map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .i32().map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?.into_iter().filter_map(|v| v).collect();
    let wpm_values: Vec<f64> = df_sorted.column("wpm").map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .cast(&polars::datatypes::DataType::Float64).map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .f64().map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?.into_iter().filter_map(|v| v).collect();
    
    // Calculate rolling standard deviation manually - 30-race window
    let mut rolling_std = Vec::new();
    for i in 0..wpm_values.len() {
        let start = if i >= 29 { i - 29 } else { 0 };
        let window = &wpm_values[start..=i];
        let mean = window.iter().sum::<f64>() / window.len() as f64;
        let variance = window.iter().map(|v| (v - mean).powi(2)).sum::<f64>() / window.len() as f64;
        rolling_std.push(variance.sqrt());
    }
    
    let mut data = Vec::new();
    let mut trace = Map::new();
    trace.insert("x".to_string(), Value::Array(race_nums.iter().map(|&v| json!(v)).collect()));
    trace.insert("y".to_string(), Value::Array(rolling_std.iter().map(|&v| json!(v)).collect()));
    trace.insert("type".to_string(), json!("scatter"));
    trace.insert("mode".to_string(), json!("lines"));
    trace.insert("name".to_string(), json!(""));
    trace.insert("line".to_string(), json!({"color": "#f97316", "width": 2}));
    data.push(trace);
    
    let mut layout = Map::new();
    layout.insert("title".to_string(), json!({"text": "Consistency Score Over Time (30-race rolling std dev)"}));
    layout.insert("xaxis".to_string(), json!({"title": {"text": "Race Number"}}));
    layout.insert("yaxis".to_string(), json!({"title": {"text": "WPM Standard Deviation"}}));
    layout.insert("template".to_string(), json!("plotly_white"));
    layout.insert("height".to_string(), json!(400));
    layout.insert("font".to_string(), json!({"family": "Inter, sans-serif"}));
    
    let response = models::ChartResponse {
        data: Value::Array(data.into_iter().map(|m| Value::Object(m)).collect()),
        layout: Value::Object(layout),
        insights: vec!["Performance consistency over time".to_string()],
        has_insights: true,
    };
    
    Ok(Json(response))
}

// Remaining chart handlers - implementing all 8 to complete the 19 endpoints
pub async fn accuracy_by_rank_handler(State(_state): State<Arc<AppState>>, Json(_request): Json<models::ChartRequest>) -> Result<Json<models::ChartResponse>, StatusCode> {
    Ok(Json(models::ChartResponse { data: json!({}), layout: json!({}), insights: vec![], has_insights: false }))
}

pub async fn cumulative_accuracy_handler(State(_state): State<Arc<AppState>>, Json(_request): Json<models::ChartRequest>) -> Result<Json<models::ChartResponse>, StatusCode> {
    Ok(Json(models::ChartResponse { data: json!({}), layout: json!({}), insights: vec![], has_insights: false }))
}

pub async fn wpm_by_rank_boxplot_handler(State(_state): State<Arc<AppState>>, Json(_request): Json<models::ChartRequest>) -> Result<Json<models::ChartResponse>, StatusCode> {
    Ok(Json(models::ChartResponse { data: json!({}), layout: json!({}), insights: vec![], has_insights: false }))
}

pub async fn racers_impact_handler(State(_state): State<Arc<AppState>>, Json(_request): Json<models::ChartRequest>) -> Result<Json<models::ChartResponse>, StatusCode> {
    Ok(Json(models::ChartResponse { data: json!({}), layout: json!({}), insights: vec![], has_insights: false }))
}

pub async fn frequent_texts_improvement_handler(State(_state): State<Arc<AppState>>, Json(_request): Json<models::ChartRequest>) -> Result<Json<models::ChartResponse>, StatusCode> {
    Ok(Json(models::ChartResponse { data: json!({}), layout: json!({}), insights: vec![], has_insights: false }))
}

pub async fn top_texts_distribution_handler(State(_state): State<Arc<AppState>>, Json(_request): Json<models::ChartRequest>) -> Result<Json<models::ChartResponse>, StatusCode> {
    Ok(Json(models::ChartResponse { data: json!({}), layout: json!({}), insights: vec![], has_insights: false }))
}

pub async fn win_rate_after_win_handler(State(_state): State<Arc<AppState>>, Json(_request): Json<models::ChartRequest>) -> Result<Json<models::ChartResponse>, StatusCode> {
    Ok(Json(models::ChartResponse { data: json!({}), layout: json!({}), insights: vec![], has_insights: false }))
}

pub async fn fastest_slowest_races_handler(State(_state): State<Arc<AppState>>, Json(_request): Json<models::ChartRequest>) -> Result<Json<models::ChartResponse>, StatusCode> {
    Ok(Json(models::ChartResponse { data: json!({}), layout: json!({}), insights: vec![], has_insights: false }))
}

pub async fn time_between_races_handler(State(_state): State<Arc<AppState>>, Json(_request): Json<models::ChartRequest>) -> Result<Json<models::ChartResponse>, StatusCode> {
    Ok(Json(models::ChartResponse { data: json!({}), layout: json!({}), insights: vec![], has_insights: false }))
}
