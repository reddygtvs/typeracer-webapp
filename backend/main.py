from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import polars as pl
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder
import json
import numpy as np
from datetime import datetime
from typing import Dict, Any
import io
from insights import calculate_insights_with_fallback
from models import ChartRequest, StatsResponse, ChartResponse
from config import settings

app = FastAPI(title="TypeRacer Analytics API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def process_race_data(df: pl.DataFrame) -> pl.DataFrame:
    """Process and clean the race data with Polars - FIXED VERSION"""
    
    # Parse datetime once
    df = df.with_columns([
        pl.col("Date/Time (UTC)").str.to_datetime("%Y-%m-%d %H:%M:%S").alias("datetime_utc")
    ])
    
    # Rename columns properly (select, not alias to avoid duplication)
    df = df.select([
        pl.col("Race #").alias("race_num"),
        pl.col("WPM").alias("wpm"),
        pl.col("Accuracy").alias("accuracy"),
        pl.col("Rank").alias("rank"),
        pl.col("# Racers").alias("num_racers"),
        pl.col("Text ID").alias("text_id"),
        pl.col("datetime_utc"),
        # Create time columns from already parsed datetime
        pl.col("datetime_utc").dt.truncate("1mo").alias("year_month"),
        pl.col("datetime_utc").dt.date().alias("date"),
        pl.col("datetime_utc").dt.hour().alias("hour"),
        pl.col("datetime_utc").dt.weekday().alias("day_of_week"),
        # Create win column
        (pl.col("Rank") == 1).cast(pl.Int32).alias("win")
    ]).sort("race_num")
    
    return df

def process_csv_data(csv_data: str) -> pl.DataFrame:
    """Process CSV data from string"""
    try:
        df = pl.read_csv(io.StringIO(csv_data))
        return process_race_data(df)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid CSV data: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.post("/stats")
async def get_stats(request: ChartRequest):
    """Get basic statistics from CSV data"""
    df = process_csv_data(request.csv_data)
    
    avg_accuracy = df["accuracy"].mean()
    return {
        "total_races": df.height,
        "avg_wpm": float(df["wpm"].mean()),
        "best_wpm": float(df["wpm"].max()),
        "total_wins": int(df["win"].sum()),
        "avg_accuracy": float(avg_accuracy) if avg_accuracy is not None else 0.0,
        "date_range": {
            "start": str(df["datetime_utc"].min()),
            "end": str(df["datetime_utc"].max())
        }
    }

@app.post("/charts/wpm-distribution")
async def wmp_distribution(request: ChartRequest):
    """Generate WPM distribution chart"""
    df = process_csv_data(request.csv_data)
    
    # Convert to pandas for plotly compatibility
    df_pandas = df.to_pandas()
    
    # Calculate key statistics
    mean_wpm = df_pandas["wpm"].mean()
    median_wpm = df_pandas["wpm"].median()
    
    # Create histogram with better bin size (15 bins for clearer visualization)
    fig = px.histogram(
        df_pandas, 
        x="wpm", 
        nbins=15,  # Reduced for clearer bars
        title="WPM Distribution",
        labels={"wpm": "Words Per Minute", "count": "Number of Races"},
        color_discrete_sequence=["#39FF14"]  # Spotify green for visibility
    )
    
    # Add mean and median lines for context (no annotations to prevent overlap)
    fig.add_vline(
        x=mean_wpm, 
        line_dash="dash", 
        line_color="#FF6B6B",
        line_width=2
    )
    
    fig.add_vline(
        x=median_wpm, 
        line_dash="dot", 
        line_color="#74B9FF",
        line_width=2
    )
    
    # Add clean legend info instead of overlapping annotations
    fig.update_layout(
        title=f"WPM Distribution (Mean: {mean_wpm:.1f}, Median: {median_wpm:.1f})"
    )
    
    fig.update_layout(
        template="plotly_dark",
        height=400,
        font=dict(family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, system-ui, sans-serif"),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        title_font_color="white",
        showlegend=False,
        xaxis=dict(
            title_font_color="rgb(181, 179, 173)",
            tickfont_color="rgb(181, 179, 173)",
            gridcolor="rgb(55, 55, 53)"
        ),
        yaxis=dict(
            title_font_color="rgb(181, 179, 173)", 
            tickfont_color="rgb(181, 179, 173)",
            gridcolor="rgb(55, 55, 53)"
        )
    )
    
    # Update hover template for better UX
    fig.update_traces(
        hovertemplate="<b>%{x} WPM</b><br>Races: %{y}<br><extra></extra>"
    )
    
    # Calculate insights
    insights_data = calculate_insights_with_fallback(df, "wmp-distribution")
    
    # Return chart data with insights
    chart_data = json.loads(fig.to_json())
    chart_data.update(insights_data)
    
    return chart_data

@app.post("/charts/performance-over-time")
async def performance_over_time(request: ChartRequest):
    """Generate performance over time chart"""
    df = process_csv_data(request.csv_data)
    
    # Monthly average WPM
    monthly_avg = df.group_by("year_month").agg([
        pl.col("wpm").mean().alias("avg_wpm")
    ]).sort("year_month")
    
    df_pandas = monthly_avg.to_pandas()
    
    fig = px.line(
        df_pandas,
        x="year_month",
        y="avg_wpm",
        title="Monthly Average WPM Over Time",
        labels={"year_month": "Month", "avg_wpm": "Average WPM"},
        line_shape="spline"
    )
    
    fig.update_traces(line_color="#10b981", line_width=3)
    fig.update_layout(
        template="plotly_white",
        height=400,
        font=dict(family="Inter, sans-serif")
    )
    
    # Calculate insights
    insights_data = calculate_insights_with_fallback(df, "performance-over-time")
    
    # Return chart data with insights
    chart_data = json.loads(fig.to_json())
    chart_data.update(insights_data)
    
    return chart_data

@app.post("/charts/rolling-average")
async def rolling_average(request: ChartRequest):
    """Generate rolling average chart"""
    df = process_csv_data(request.csv_data)
    
    # Calculate rolling average
    df_with_rolling = df.with_columns([
        pl.col("wpm").rolling_mean(window_size=100).alias("rolling_avg_wpm")
    ])
    
    df_pandas = df_with_rolling.to_pandas()
    
    fig = px.line(
        df_pandas,
        x="race_num",
        y="rolling_avg_wpm",
        title="Rolling Average WPM (100 races)",
        labels={"race_num": "Race Number", "rolling_avg_wpm": "Rolling Average WPM"}
    )
    
    fig.update_traces(line_color="#8b5cf6", line_width=2)
    fig.update_layout(
        template="plotly_white",
        height=400,
        font=dict(family="Inter, sans-serif")
    )
    
    # Calculate insights
    insights_data = calculate_insights_with_fallback(df, "rolling-average")
    
    # Return chart data with insights
    chart_data = json.loads(fig.to_json())
    chart_data.update(insights_data)
    
    return chart_data

@app.post("/charts/rank-distribution")
async def rank_distribution(request: ChartRequest):
    """Generate rank distribution chart"""
    df = process_csv_data(request.csv_data)
    
    # Calculate rank distribution
    rank_dist = df.group_by("rank").agg([
        pl.count().alias("count")
    ]).with_columns([
        (pl.col("count") / pl.col("count").sum() * 100).alias("percentage")
    ]).sort("rank")
    
    df_pandas = rank_dist.to_pandas()
    
    fig = px.bar(
        df_pandas,
        x="rank",
        y="percentage",
        title="Rank Distribution",
        labels={"rank": "Rank", "percentage": "Percentage (%)"},
        color="percentage",
        color_continuous_scale="viridis"
    )
    
    fig.update_layout(
        template="plotly_white",
        height=400,
        font=dict(family="Inter, sans-serif"),
        showlegend=False
    )
    
    # Calculate insights
    insights_data = calculate_insights_with_fallback(df, "rank-distribution")
    
    # Return chart data with insights
    chart_data = json.loads(fig.to_json())
    chart_data.update(insights_data)
    
    return chart_data

@app.post("/charts/hourly-performance")
async def hourly_performance(request: ChartRequest):
    """Generate hourly performance chart"""
    df = process_csv_data(request.csv_data)
    
    # Calculate hourly average
    hourly_avg = df.group_by("hour").agg([
        pl.col("wpm").mean().alias("avg_wpm")
    ]).sort("hour")
    
    df_pandas = hourly_avg.to_pandas()
    
    fig = px.bar(
        df_pandas,
        x="hour",
        y="avg_wpm",
        title="Average WPM by Hour of Day",
        labels={"hour": "Hour of Day", "avg_wpm": "Average WPM"},
        color="avg_wpm",
        color_continuous_scale="blues"
    )
    
    fig.update_layout(
        template="plotly_white",
        height=400,
        font=dict(family="Inter, sans-serif"),
        showlegend=False
    )
    
    # Calculate insights
    insights_data = calculate_insights_with_fallback(df, "hourly-performance")
    
    # Return chart data with insights
    chart_data = json.loads(fig.to_json())
    chart_data.update(insights_data)
    
    return chart_data

@app.post("/charts/accuracy-distribution")
async def accuracy_distribution(request: ChartRequest):
    """Generate accuracy distribution chart"""
    df = process_csv_data(request.csv_data)
    
    df_pandas = df.to_pandas()
    
    fig = px.histogram(
        df_pandas, 
        x="accuracy", 
        nbins=30,
        title="Accuracy Distribution",
        labels={"accuracy": "Accuracy", "count": "Frequency"},
        color_discrete_sequence=["#ef4444"]
    )
    
    fig.update_layout(
        template="plotly_white",
        height=400,
        font=dict(family="Inter, sans-serif")
    )
    
    # Calculate insights
    insights_data = calculate_insights_with_fallback(df, "accuracy-distribution")
    
    # Return chart data with insights
    chart_data = json.loads(fig.to_json())
    chart_data.update(insights_data)
    
    return chart_data

@app.post("/charts/daily-performance")
async def daily_performance(request: ChartRequest):
    """Generate daily performance over time chart"""
    df = process_csv_data(request.csv_data)
    
    # Daily average WPM
    daily_avg = df.group_by("date").agg([
        pl.col("wpm").mean().alias("avg_wpm")
    ]).sort("date")
    
    df_pandas = daily_avg.to_pandas()
    
    fig = px.line(
        df_pandas,
        x="date",
        y="avg_wpm",
        title="Daily Average WPM Over Time",
        labels={"date": "Date", "avg_wpm": "Average WPM"}
    )
    
    fig.update_traces(line_color="#f97316", line_width=2)
    fig.update_layout(
        template="plotly_white",
        height=400,
        font=dict(family="Inter, sans-serif")
    )
    
    # Calculate insights
    insights_data = calculate_insights_with_fallback(df, "daily-performance")
    
    # Return chart data with insights
    chart_data = json.loads(fig.to_json())
    chart_data.update(insights_data)
    
    return chart_data

@app.post("/charts/wpm-vs-accuracy")
async def wpm_vs_accuracy(request: ChartRequest):
    """Generate WPM vs Accuracy scatter plot"""
    df = process_csv_data(request.csv_data)
    
    df_pandas = df.to_pandas()
    
    fig = px.scatter(
        df_pandas,
        x="wpm",
        y="accuracy",
        title="WPM vs Accuracy",
        labels={"wpm": "Words Per Minute", "accuracy": "Accuracy"},
        opacity=0.6
    )
    
    fig.update_layout(
        template="plotly_white",
        height=400,
        font=dict(family="Inter, sans-serif")
    )
    
    # Calculate insights
    insights_data = calculate_insights_with_fallback(df, "wpm-vs-accuracy")
    
    # Return chart data with insights
    chart_data = json.loads(fig.to_json())
    chart_data.update(insights_data)
    
    return chart_data

@app.post("/charts/win-rate-monthly")
async def win_rate_monthly(request: ChartRequest):
    """Generate monthly win rate chart"""
    df = process_csv_data(request.csv_data)
    
    try:
        # Monthly win rate
        monthly_wins = df.group_by("year_month").agg([
            pl.col("win").mean().alias("win_rate")
        ]).sort("year_month")
        
        df_pandas = monthly_wins.to_pandas()
        
        fig = px.line(
            df_pandas,
            x="year_month",
            y="win_rate",
            title="Monthly Win Rate Over Time",
            labels={"year_month": "Month", "win_rate": "Win Rate"}
        )
        
        fig.update_traces(line_color="#eab308", line_width=3)
        fig.update_layout(
            template="plotly_white",
            height=400,
            font=dict(family="Inter, sans-serif")
        )
        
        # Calculate insights
        insights_data = calculate_insights_with_fallback(df, "win-rate-monthly")
        
        # Return chart data with insights
        chart_data = json.loads(fig.to_json())
        chart_data.update(insights_data)
        
        return chart_data
        
    except Exception as e:
        print(f"Error in win-rate-monthly endpoint: {str(e)}")
        print(f"DataFrame columns: {df.columns if df is not None else 'No DataFrame'}")
        raise HTTPException(status_code=500, detail=f"Error generating chart: {str(e)}")

@app.post("/charts/top-texts")
async def top_texts(request: ChartRequest):
    """Generate top vs bottom texts performance chart"""
    df = process_csv_data(request.csv_data)
    
    # Calculate average WPM by text
    text_wpm = df.group_by("text_id").agg([
        pl.col("wpm").mean().alias("avg_wpm"),
        pl.count().alias("race_count")
    ]).filter(pl.col("race_count") >= 5)  # Only texts with 5+ races
    
    # Get top 10 and bottom 10
    top_10 = text_wpm.top_k(10, by="avg_wpm")
    bottom_10 = text_wpm.bottom_k(10, by="avg_wpm")
    
    # Combine and convert
    combined = pl.concat([top_10, bottom_10])
    df_pandas = combined.to_pandas()
    df_pandas['text_id'] = df_pandas['text_id'].astype(str)
    
    fig = px.bar(
        df_pandas,
        x="text_id",
        y="avg_wpm",
        title="Top 10 vs Bottom 10 Texts by Average WPM",
        labels={"text_id": "Text ID", "avg_wpm": "Average WPM"},
        color="avg_wpm",
        color_continuous_scale="viridis"
    )
    
    fig.update_layout(
        template="plotly_white",
        height=400,
        font=dict(family="Inter, sans-serif"),
        xaxis_tickangle=-45
    )
    
    # Calculate insights
    insights_data = calculate_insights_with_fallback(df, "top-texts")
    
    # Return chart data with insights
    chart_data = json.loads(fig.to_json())
    chart_data.update(insights_data)
    
    return chart_data

@app.post("/charts/consistency-score")
async def consistency_score(request: ChartRequest):
    """Generate consistency score over time chart"""
    df = process_csv_data(request.csv_data)
    
    # Calculate rolling standard deviation (consistency metric)
    df_sorted = df.sort("race_num")
    df_with_rolling = df_sorted.with_columns([
        pl.col("wpm").rolling_std(window_size=30).alias("rolling_std_wpm")
    ])
    
    df_pandas = df_with_rolling.to_pandas()
    
    fig = px.line(
        df_pandas,
        x="race_num",
        y="rolling_std_wpm",
        title="Consistency Score Over Time (30-race rolling std dev)",
        labels={"race_num": "Race Number", "rolling_std_wpm": "WPM Standard Deviation"}
    )
    
    fig.update_traces(line_color="#f97316", line_width=2)
    fig.update_layout(
        template="plotly_white",
        height=400,
        font=dict(family="Inter, sans-serif")
    )
    
    # Calculate insights
    insights_data = calculate_insights_with_fallback(df, "consistency-score")
    
    # Return chart data with insights
    chart_data = json.loads(fig.to_json())
    chart_data.update(insights_data)
    
    return chart_data

@app.post("/charts/accuracy-by-rank")
async def accuracy_by_rank(request: ChartRequest):
    """Generate average accuracy by rank chart"""
    df = process_csv_data(request.csv_data)
    
    try:
        # Calculate average accuracy by rank with more stats
        rank_accuracy = df.group_by("rank").agg([
            pl.col("accuracy").mean().alias("avg_accuracy"),
            pl.col("accuracy").count().alias("count"),
            pl.col("accuracy").std().alias("std_accuracy")
        ]).sort("rank")
        
        df_pandas = rank_accuracy.to_pandas()
        df_pandas = df_pandas.round(2)
        
        # Filter out ranks with very few races for better visualization
        df_pandas = df_pandas[df_pandas['count'] >= 3]
        
        fig = px.bar(
            df_pandas,
            x="rank",
            y="avg_accuracy",
            title="Average Accuracy by Rank",
            labels={"rank": "Rank", "avg_accuracy": "Average Accuracy (%)"},
            color="avg_accuracy",
            color_continuous_scale="RdYlGn",  # Red-Yellow-Green for better contrast
            text="avg_accuracy"  # Add data labels
        )
        
        # Make differences more pronounced by adjusting y-axis range
        min_acc = df_pandas['avg_accuracy'].min()
        max_acc = df_pandas['avg_accuracy'].max()
        y_range_padding = (max_acc - min_acc) * 0.1
        
        fig.update_layout(
            template="plotly_white",
            height=400,
            font=dict(family="Inter, sans-serif"),
            showlegend=False,
            yaxis=dict(
                range=[min_acc - y_range_padding, max_acc + y_range_padding]  # Zoom in on actual data range
            )
        )
        
        # Format text labels to show one decimal place
        fig.update_traces(
            texttemplate='%{text:.1f}%',
            textposition='outside'
        )
        
        # Calculate insights
        insights_data = calculate_insights_with_fallback(df, "accuracy-by-rank")
        
        # Return chart data with insights
        chart_data = json.loads(fig.to_json())
        chart_data.update(insights_data)
        
        return chart_data
        
    except Exception as e:
        print(f"Error in accuracy-by-rank endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating chart: {str(e)}")

@app.post("/charts/cumulative-accuracy")
async def cumulative_accuracy(request: ChartRequest):
    """Generate cumulative average accuracy over time chart"""
    df = process_csv_data(request.csv_data)
    
    try:
        # Sort by race number and calculate cumulative accuracy
        df_sorted = df.sort("race_num")
        
        # Convert to pandas for cumulative calculation
        df_pandas = df_sorted.to_pandas()
        df_pandas['cumulative_accuracy'] = df_pandas['accuracy'].expanding().mean()
        
        fig = px.line(
            df_pandas,
            x="race_num",
            y="cumulative_accuracy",
            title="Cumulative Average Accuracy Over All Races",
            labels={"race_num": "Race Number", "cumulative_accuracy": "Cumulative Average Accuracy"}
        )
        
        fig.update_traces(line_color="#8b5cf6", line_width=2)
        fig.update_layout(
            template="plotly_white",
            height=400,
            font=dict(family="Inter, sans-serif")
        )
        
        # Calculate insights
        insights_data = calculate_insights_with_fallback(df, "cumulative-accuracy")
        
        # Return chart data with insights
        chart_data = json.loads(fig.to_json())
        chart_data.update(insights_data)
        
        return chart_data
        
    except Exception as e:
        print(f"Error in cumulative-accuracy endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating chart: {str(e)}")

@app.post("/charts/wpm-by-rank-boxplot")
async def wmp_by_rank_boxplot(request: ChartRequest):
    """Generate outlier analysis: WPM by rank box plot"""
    df = process_csv_data(request.csv_data)
    
    try:
        df_pandas = df.to_pandas()
        
        fig = px.box(
            df_pandas,
            x="rank",
            y="wpm",
            title="Outlier Analysis: WPM by Rank",
            labels={"rank": "Rank", "wpm": "WPM"}
        )
        
        fig.update_layout(
            template="plotly_white",
            height=400,
            font=dict(family="Inter, sans-serif")
        )
        
        # Calculate insights
        insights_data = calculate_insights_with_fallback(df, "wpm-by-rank-boxplot")
        
        # Return chart data with insights
        chart_data = json.loads(fig.to_json())
        chart_data.update(insights_data)
        
        return chart_data
        
    except Exception as e:
        print(f"Error in wpm-by-rank-boxplot endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating chart: {str(e)}")

@app.post("/charts/racers-impact")
async def racers_impact(request: ChartRequest):
    """Generate impact of number of racers on average WPM chart"""
    df = process_csv_data(request.csv_data)
    
    try:
        # Calculate average WPM by number of racers
        racers_wpm = df.group_by("num_racers").agg([
            pl.col("wpm").mean().alias("avg_wpm")
        ]).sort("num_racers")
        
        df_pandas = racers_wpm.to_pandas()
        
        fig = px.line(
            df_pandas,
            x="num_racers",
            y="avg_wpm",
            title="Impact of Number of Racers on Average WPM",
            labels={"num_racers": "Number of Racers", "avg_wpm": "Average WPM"},
            markers=True
        )
        
        fig.update_traces(line_color="#14b8a6", line_width=3, marker_size=6)
        fig.update_layout(
            template="plotly_white",
            height=400,
            font=dict(family="Inter, sans-serif")
        )
        
        # Calculate insights
        insights_data = calculate_insights_with_fallback(df, "racers-impact")
        
        # Return chart data with insights
        chart_data = json.loads(fig.to_json())
        chart_data.update(insights_data)
        
        return chart_data
        
    except Exception as e:
        print(f"Error in racers-impact endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating chart: {str(e)}")

@app.post("/charts/frequent-texts-improvement")
async def frequent_texts_improvement(request: ChartRequest):
    """Generate WPM improvement over time for frequent texts"""
    df = process_csv_data(request.csv_data)
    
    try:
        # Get top 5 most frequent texts
        top_texts = df.group_by("text_id").agg([
            pl.count().alias("race_count")
        ]).top_k(5, by="race_count")
        
        top_text_ids = top_texts.select("text_id").to_pandas()["text_id"].tolist()
        
        # Filter and process data for rolling averages
        frequent_texts_df = df.filter(
            pl.col("text_id").is_in(top_text_ids)
        ).sort("datetime_utc").to_pandas()
        
        # Create interactive dropdown chart - show all texts with dropdown selector
        fig = go.Figure()
        colors = ["#39FF14", "#FF6B6B", "#74B9FF", "#A29BFE", "#FD79A8"]
        
        # Add traces for each text (initially all visible)
        for i, text_id in enumerate(top_text_ids):
            text_data = frequent_texts_df[frequent_texts_df['text_id'] == text_id].copy()
            
            if len(text_data) < 3:  # Skip if not enough data
                continue
                
            # Calculate rolling average
            text_data['rolling_wpm'] = text_data['wpm'].rolling(window=10, min_periods=1).mean()
            
            # Add rolling average line - show all texts at once
            fig.add_trace(
                go.Scatter(
                    x=text_data['datetime_utc'],
                    y=text_data['rolling_wpm'],
                    mode='lines',
                    name=f'Text {text_id}',
                    line=dict(color=colors[i], width=3),
                    visible=True,  # Show all texts
                    hovertemplate="<b>Text " + str(text_id) + "</b><br>" +
                                 "Date: %{x}<br>" +
                                 "Rolling Avg: %{y:.1f} WPM<br>" +
                                 "<extra></extra>"
                )
            )
        
        fig.update_layout(
            title="WPM Improvement Over Time - Top 5 Most Frequent Texts",
            height=400,
            template="plotly_dark",
            font=dict(family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, system-ui, sans-serif"),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            title_font_color="white",
            showlegend=True,  # Show legend since we're displaying multiple lines
            xaxis_title="Date",
            yaxis_title="WPM (10-Race Rolling Average)"
        )
        
        # Update axes for dark theme
        fig.update_xaxes(
            title_font_color="rgb(181, 179, 173)",
            tickfont_color="rgb(181, 179, 173)",
            gridcolor="rgb(55, 55, 53)"
        )
        
        fig.update_yaxes(
            title_font_color="rgb(181, 179, 173)", 
            tickfont_color="rgb(181, 179, 173)",
            gridcolor="rgb(55, 55, 53)"
        )
        
        # Calculate insights
        insights_data = calculate_insights_with_fallback(df, "frequent-texts-improvement")
        
        # Return chart data with insights
        chart_data = json.loads(fig.to_json())
        chart_data.update(insights_data)
        
        return chart_data
        
    except Exception as e:
        print(f"Error in frequent-texts-improvement endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating chart: {str(e)}")

@app.post("/charts/top-texts-distribution")
async def top_texts_distribution(request: ChartRequest):
    """Generate WPM distribution for top 10 texts"""
    df = process_csv_data(request.csv_data)
    
    try:
        # Get top 10 most frequent texts
        top_texts = df.group_by("text_id").agg([
            pl.count().alias("race_count")
        ]).top_k(10, by="race_count")
        
        top_text_ids = top_texts.select("text_id").to_pandas()["text_id"].tolist()
        
        # Filter data for these texts
        top_texts_data = df.filter(
            pl.col("text_id").is_in(top_text_ids)
        ).to_pandas()
        
        fig = go.Figure()
        
        # Use box plot instead of overlapping histograms for much better clarity
        colors = ["#39FF14", "#FF6B6B", "#74B9FF", "#A29BFE", "#FD79A8", 
                  "#FDCB6E", "#6C5CE7", "#00B894", "#E17055", "#81ECEC"]
        
        for i, text_id in enumerate(top_text_ids):
            text_data = top_texts_data[top_texts_data['text_id'] == text_id]
            fig.add_trace(go.Box(
                y=text_data['wpm'],
                name=f'Text {text_id}',
                marker_color=colors[i % len(colors)],
                boxpoints='outliers'  # Show outliers only
            ))
        
        fig.update_layout(
            title="WPM Distribution for Top 10 Most Frequent Texts",
            yaxis_title="WPM",
            xaxis_title="Text ID",
            template="plotly_dark",
            height=400,
            font=dict(family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, system-ui, sans-serif"),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            title_font_color="white",
            xaxis=dict(
                title_font_color="rgb(181, 179, 173)",
                tickfont_color="rgb(181, 179, 173)",
                gridcolor="rgb(55, 55, 53)"
            ),
            yaxis=dict(
                title_font_color="rgb(181, 179, 173)", 
                tickfont_color="rgb(181, 179, 173)",
                gridcolor="rgb(55, 55, 53)"
            )
        )
        
        # Calculate insights
        insights_data = calculate_insights_with_fallback(df, "top-texts-distribution")
        
        # Return chart data with insights
        chart_data = json.loads(fig.to_json())
        chart_data.update(insights_data)
        
        return chart_data
        
    except Exception as e:
        print(f"Error in top-texts-distribution endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating chart: {str(e)}")

@app.post("/charts/win-rate-after-win")
async def win_rate_after_win(request: ChartRequest):
    """Generate win rate after previous win chart"""
    df = process_csv_data(request.csv_data)
    
    try:
        # Sort by race number and create previous win column
        df_sorted = df.sort("race_num")
        df_pandas = df_sorted.to_pandas()
        
        # Create previous win column
        df_pandas['prev_win'] = df_pandas['win'].shift(1).fillna(0).astype(int)
        
        # Calculate win rate after previous result
        win_rate_stats = df_pandas.groupby('prev_win')['win'].mean().reset_index()
        win_rate_stats['condition'] = win_rate_stats['prev_win'].map({
            1: 'After Win',
            0: 'After Loss'
        })
        
        fig = px.bar(
            win_rate_stats,
            x='condition',
            y='win',
            title="Win Rate After Previous Race Result",
            labels={"condition": "Previous Race Result", "win": "Win Rate"},
            color='win',
            color_continuous_scale="viridis"
        )
        
        fig.update_layout(
            template="plotly_white",
            height=400,
            font=dict(family="Inter, sans-serif"),
            showlegend=False
        )
        
        # Calculate insights
        insights_data = calculate_insights_with_fallback(df, "win-rate-after-win")
        
        # Return chart data with insights
        chart_data = json.loads(fig.to_json())
        chart_data.update(insights_data)
        
        return chart_data
        
    except Exception as e:
        print(f"Error in win-rate-after-win endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating chart: {str(e)}")

@app.post("/charts/fastest-slowest-races")
async def fastest_slowest_races(request: ChartRequest):
    """Generate top 5 fastest and slowest races chart"""
    df = process_csv_data(request.csv_data)
    
    try:
        # Get top 5 fastest and slowest races
        df_pandas = df.to_pandas()
        
        fastest_5 = df_pandas.nlargest(5, 'wpm')
        slowest_5 = df_pandas.nsmallest(5, 'wpm')
        
        fig = go.Figure()
        
        # Add fastest races
        fig.add_trace(go.Scatter(
            x=fastest_5['race_num'],
            y=fastest_5['wpm'],
            mode='markers',
            name='Top 5 Fastest',
            marker=dict(color='red', size=10),
            text=fastest_5['wpm'].round(1),
            textposition='top center'
        ))
        
        # Add slowest races
        fig.add_trace(go.Scatter(
            x=slowest_5['race_num'],
            y=slowest_5['wpm'],
            mode='markers',
            name='Top 5 Slowest',
            marker=dict(color='blue', size=10),
            text=slowest_5['wpm'].round(1),
            textposition='bottom center'
        ))
        
        fig.update_layout(
            title="Top 5 Fastest and Slowest Races",
            xaxis_title="Race Number",
            yaxis_title="WPM",
            template="plotly_white",
            height=400,
            font=dict(family="Inter, sans-serif")
        )
        
        # Calculate insights
        insights_data = calculate_insights_with_fallback(df, "fastest-slowest-races")
        
        # Return chart data with insights
        chart_data = json.loads(fig.to_json())
        chart_data.update(insights_data)
        
        return chart_data
        
    except Exception as e:
        print(f"Error in fastest-slowest-races endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating chart: {str(e)}")

@app.post("/charts/time-between-races")
async def time_between_races(request: ChartRequest):
    """Generate time between races and performance chart"""
    df = process_csv_data(request.csv_data)
    
    try:
        # Sort by datetime and calculate time differences
        df_sorted = df.sort("datetime_utc")
        df_pandas = df_sorted.to_pandas()
        
        # Calculate time difference in hours
        df_pandas['time_diff_hours'] = df_pandas['datetime_utc'].diff().dt.total_seconds().div(3600).fillna(0)
        
        # Create bins for time differences
        bins = [0, 1, 3, 6, 12, 24, 48, 168, float('inf')]
        labels = ['0-1h', '1-3h', '3-6h', '6-12h', '12-24h', '24-48h', '48h-1wk', '1wk+']
        df_pandas['time_bin'] = pd.cut(df_pandas['time_diff_hours'], bins=bins, labels=labels)
        
        # Calculate average WPM for each bin with more stats
        time_wpm_stats = df_pandas.groupby('time_bin', observed=False).agg({
            'wpm': ['mean', 'count', 'std']
        }).round(2).reset_index()
        time_wpm_stats.columns = ['time_bin', 'avg_wpm', 'count', 'std_wpm']
        
        # Filter out bins with very few samples for better visualization
        time_wpm_stats = time_wpm_stats[time_wpm_stats['count'] >= 5]
        
        fig = px.bar(
            time_wpm_stats,
            x='time_bin',
            y='avg_wpm',
            title="Average WPM by Time Between Races",
            labels={"time_bin": "Time Between Races", "avg_wpm": "Average WPM"},
            color='avg_wpm',
            color_continuous_scale="RdYlGn",  # Red-Yellow-Green scale for better contrast
            text='avg_wpm'  # Add data labels
        )
        
        # Make differences more pronounced by adjusting y-axis range
        min_wpm = time_wpm_stats['avg_wpm'].min()
        max_wpm = time_wpm_stats['avg_wpm'].max()
        y_range_padding = (max_wpm - min_wpm) * 0.1
        
        fig.update_layout(
            template="plotly_white",
            height=400,
            font=dict(family="Inter, sans-serif"),
            xaxis_tickangle=-45,
            showlegend=False,
            yaxis=dict(
                range=[min_wpm - y_range_padding, max_wpm + y_range_padding]  # Zoom in on the actual data range
            )
        )
        
        # Format text labels to show one decimal place
        fig.update_traces(
            texttemplate='%{text:.1f}',
            textposition='outside'
        )
        
        # Calculate insights
        insights_data = calculate_insights_with_fallback(df, "time-between-races")
        
        # Return chart data with insights
        chart_data = json.loads(fig.to_json())
        chart_data.update(insights_data)
        
        return chart_data
        
    except Exception as e:
        print(f"Error in time-between-races endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating chart: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)