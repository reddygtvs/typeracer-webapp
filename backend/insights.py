import polars as pl
import pandas as pd
import numpy as np
from typing import List, Dict, Any
from datetime import datetime, timedelta

def calculate_insights_with_fallback(df: pl.DataFrame, chart_type: str) -> Dict[str, Any]:
    """Calculate insights for a chart with fallback for insufficient data"""
    try:
        insights = calculate_chart_insights(df, chart_type)
        return {
            "insights": insights,
            "has_insights": True
        }
    except Exception as e:
        print(f"Error calculating insights for {chart_type}: {str(e)}")
        return {
            "insights": [
                "Insufficient data for detailed analysis",
                f"Showing {len(df)} races",
                "Upload more data for insights"
            ],
            "has_insights": False
        }

def calculate_chart_insights(df: pl.DataFrame, chart_type: str) -> List[str]:
    """Calculate specific insights based on chart type"""
    
    if chart_type == "wpm-distribution":
        return calculate_wpm_distribution_insights(df)
    elif chart_type == "accuracy-distribution":
        return calculate_accuracy_distribution_insights(df)
    elif chart_type == "performance-over-time":
        return calculate_performance_over_time_insights(df)
    elif chart_type == "daily-performance":
        return calculate_daily_performance_insights(df)
    elif chart_type == "rolling-average":
        return calculate_rolling_average_insights(df)
    elif chart_type == "rank-distribution":
        return calculate_rank_distribution_insights(df)
    elif chart_type == "hourly-performance":
        return calculate_hourly_performance_insights(df)
    elif chart_type == "wpm-vs-accuracy":
        return calculate_wpm_vs_accuracy_insights(df)
    elif chart_type == "win-rate-monthly":
        return calculate_win_rate_monthly_insights(df)
    elif chart_type == "top-texts":
        return calculate_top_texts_insights(df)
    elif chart_type == "consistency-score":
        return calculate_consistency_insights(df)
    elif chart_type == "accuracy-by-rank":
        return calculate_accuracy_by_rank_insights(df)
    elif chart_type == "cumulative-accuracy":
        return calculate_cumulative_accuracy_insights(df)
    elif chart_type == "wpm-by-rank-boxplot":
        return calculate_wpm_by_rank_insights(df)
    elif chart_type == "racers-impact":
        return calculate_racers_impact_insights(df)
    elif chart_type == "frequent-texts-improvement":
        return calculate_frequent_texts_insights(df)
    elif chart_type == "top-texts-distribution":
        return calculate_top_texts_distribution_insights(df)
    elif chart_type == "win-rate-after-win":
        return calculate_win_rate_after_win_insights(df)
    elif chart_type == "fastest-slowest-races":
        return calculate_fastest_slowest_insights(df)
    elif chart_type == "time-between-races":
        return calculate_time_between_races_insights(df)
    else:
        return [
            "Chart insights not yet implemented",
            f"Showing data for {chart_type}",
            "More insights coming soon"
        ]

def calculate_wpm_distribution_insights(df: pl.DataFrame) -> List[str]:
    """Calculate insights for WPM distribution"""
    mean_wpm = df["wpm"].mean()
    p90_wpm = df["wpm"].quantile(0.9)
    
    # Calculate mode range (most common bin)
    wpm_values = df["wpm"].to_list()
    hist, bin_edges = np.histogram(wpm_values, bins=15)
    max_bin_idx = np.argmax(hist)
    mode_range = f"{bin_edges[max_bin_idx]:.0f}-{bin_edges[max_bin_idx + 1]:.0f}"
    
    return [
        f"Average: {mean_wpm:.1f} WPM",
        f"Most common range: {mode_range} WPM",
        f"Top 10% threshold: {p90_wpm:.1f} WPM"
    ]

def calculate_accuracy_distribution_insights(df: pl.DataFrame) -> List[str]:
    """Calculate insights for accuracy distribution"""
    mean_acc = df["accuracy"].mean()
    above_95_pct = (df["accuracy"] > 0.95).sum() / len(df) * 100
    perfect_count = (df["accuracy"] == 1.0).sum()
    
    return [
        f"Average: {mean_acc * 100:.1f}% accuracy",
        f"Above 95%: {above_95_pct:.1f}% of races",
        f"Perfect scores: {perfect_count} races at 100%"
    ]

def calculate_performance_over_time_insights(df: pl.DataFrame) -> List[str]:
    """Calculate insights for performance over time"""
    monthly_avg = df.group_by("year_month").agg([
        pl.col("wpm").mean().alias("avg_wpm")
    ]).sort("year_month")
    
    if len(monthly_avg) < 2:
        return ["Need at least 2 months of data", "Current month shown", "Keep racing for trends"]
    
    first_month_wpm = monthly_avg[0, "avg_wpm"]
    last_month_wpm = monthly_avg[-1, "avg_wpm"]
    best_month_idx = monthly_avg["avg_wpm"].arg_max()
    best_month_wpm = monthly_avg[best_month_idx, "avg_wpm"]
    best_month = monthly_avg[best_month_idx, "year_month"]
    
    change_pct = ((last_month_wpm - first_month_wpm) / first_month_wpm) * 100
    direction = "↗ Improved" if change_pct > 0 else "↘ Declined" if change_pct < 0 else "→ Stable"
    
    return [
        f"Trend: {first_month_wpm:.1f} → {last_month_wpm:.1f} WPM",
        f"Change: {direction} {abs(change_pct):.1f}%",
        f"Best month: {best_month.strftime('%b %Y')} ({best_month_wpm:.1f} WPM)"
    ]

def calculate_daily_performance_insights(df: pl.DataFrame) -> List[str]:
    """Calculate insights for daily performance"""
    daily_stats = df.group_by("date").agg([
        pl.col("wpm").mean().alias("avg_wpm"),
        pl.count().alias("race_count")
    ]).sort("date")
    
    most_active_idx = daily_stats["race_count"].arg_max()
    best_wpm_idx = daily_stats["avg_wpm"].arg_max()
    
    most_active_date = daily_stats[most_active_idx, "date"]
    most_active_count = daily_stats[most_active_idx, "race_count"]
    best_wpm_date = daily_stats[best_wpm_idx, "date"]
    best_wpm_value = daily_stats[best_wpm_idx, "avg_wpm"]
    
    std_dev = daily_stats["avg_wpm"].std()
    
    return [
        f"Most active: {most_active_date.strftime('%b %d')} ({most_active_count} races)",
        f"Best day: {best_wpm_date.strftime('%b %d')} with {best_wpm_value:.1f} WPM",
        f"Day-to-day variance: ±{std_dev:.1f} WPM"
    ]

def calculate_rolling_average_insights(df: pl.DataFrame) -> List[str]:
    """Calculate insights for rolling average"""
    df_sorted = df.sort("race_num")
    
    if len(df_sorted) < 100:
        current_avg = df_sorted["wpm"].mean()
        return [
            f"Current average: {current_avg:.1f} WPM",
            f"Need {100 - len(df_sorted)} more races for 100-race rolling average",
            "Keep racing to unlock rolling insights"
        ]
    
    # Calculate rolling averages
    df_with_rolling = df_sorted.with_columns([
        pl.col("wpm").rolling_mean(window_size=100).alias("rolling_avg")
    ])
    
    latest_100 = df_with_rolling[-1, "rolling_avg"]
    overall_avg = df_sorted["wpm"].mean()
    max_rolling = df_with_rolling["rolling_avg"].max()
    
    comparison = f"{latest_100 - overall_avg:+.1f} vs overall"
    
    return [
        f"Latest 100 races: {latest_100:.1f} WPM",
        f"vs Overall average: {comparison}",
        f"Best 100-race streak: {max_rolling:.1f} WPM"
    ]

def calculate_rank_distribution_insights(df: pl.DataFrame) -> List[str]:
    """Calculate insights for rank distribution"""
    mode_rank = df["rank"].mode()[0]
    win_rate = (df["rank"] == 1).sum() / len(df) * 100
    top3_rate = (df["rank"] <= 3).sum() / len(df) * 100
    
    return [
        f"Most common rank: #{mode_rank}",
        f"Win rate: {win_rate:.1f}%",
        f"Top 3 finishes: {top3_rate:.1f}% of races"
    ]

def calculate_hourly_performance_insights(df: pl.DataFrame) -> List[str]:
    """Calculate insights for hourly performance"""
    hourly_avg = df.group_by("hour").agg([
        pl.col("wpm").mean().alias("avg_wpm")
    ]).sort("hour")
    
    best_hour_idx = hourly_avg["avg_wpm"].arg_max()
    worst_hour_idx = hourly_avg["avg_wpm"].arg_min()
    
    best_hour = hourly_avg[best_hour_idx, "hour"]
    best_hour_wpm = hourly_avg[best_hour_idx, "avg_wpm"]
    worst_hour = hourly_avg[worst_hour_idx, "hour"]
    worst_hour_wpm = hourly_avg[worst_hour_idx, "avg_wpm"]
    
    wpm_range = best_hour_wpm - worst_hour_wpm
    
    return [
        f"Peak time: {best_hour}:00 ({best_hour_wpm:.1f} WPM)",
        f"Worst time: {worst_hour}:00 ({worst_hour_wpm:.1f} WPM)",
        f"Hour-to-hour range: {wpm_range:.1f} WPM difference"
    ]

def calculate_wpm_vs_accuracy_insights(df: pl.DataFrame) -> List[str]:
    """Calculate insights for WPM vs accuracy"""
    # Find dynamic threshold for high speed (75th percentile)
    high_speed_threshold = df["wpm"].quantile(0.75)
    high_speed_acc = df.filter(pl.col("wpm") > high_speed_threshold)["accuracy"].mean()
    
    high_acc_wpm = df.filter(pl.col("accuracy") > 0.98)["wpm"].mean()
    
    # Balance point: best WPM with 97%+ accuracy
    balance_point_wpm = df.filter(pl.col("accuracy") >= 0.97)["wpm"].max()
    
    return [
        f"High speed races (>{high_speed_threshold:.0f} WPM): {high_speed_acc * 100:.1f}% avg accuracy",
        f"High accuracy races (>98%): {high_acc_wpm:.1f} avg WPM",
        f"Speed-accuracy balance: {balance_point_wpm:.1f} WPM at 97%+"
    ]

# Continue with remaining insight functions...
def calculate_win_rate_monthly_insights(df: pl.DataFrame) -> List[str]:
    """Calculate insights for monthly win rate"""
    monthly_wins = df.group_by("year_month").agg([
        pl.col("win").mean().alias("win_rate")
    ]).sort("year_month")
    
    if len(monthly_wins) < 2:
        return ["Need multiple months", "Current month shown", "Keep racing for trends"]
    
    best_month_idx = monthly_wins["win_rate"].arg_max()
    worst_month_idx = monthly_wins["win_rate"].arg_min()
    
    best_month = monthly_wins[best_month_idx, "year_month"]
    best_rate = monthly_wins[best_month_idx, "win_rate"] * 100
    worst_month = monthly_wins[worst_month_idx, "year_month"]
    worst_rate = monthly_wins[worst_month_idx, "win_rate"] * 100
    
    # Calculate consecutive winning months
    win_rates = monthly_wins["win_rate"].to_list()
    max_streak = 0
    current_streak = 0
    for rate in win_rates:
        if rate > 0:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0
    
    return [
        f"Best month: {best_month.strftime('%b %Y')} ({best_rate:.1f}% wins)",
        f"Worst month: {worst_month.strftime('%b %Y')} ({worst_rate:.1f}% wins)",
        f"Win streak record: {max_streak} consecutive months"
    ]

def calculate_top_texts_insights(df: pl.DataFrame) -> List[str]:
    """Calculate insights for top texts"""
    text_wpm = df.group_by("text_id").agg([
        pl.col("wpm").mean().alias("avg_wpm"),
        pl.count().alias("count")
    ]).filter(pl.col("count") >= 5)
    
    if len(text_wpm) == 0:
        return ["Need more repeated texts", "Practice same texts more", "Upload more race data"]
    
    easiest_idx = text_wpm["avg_wpm"].arg_max()
    hardest_idx = text_wpm["avg_wpm"].arg_min()
    
    easiest_text = text_wpm[easiest_idx, "text_id"]
    easiest_wpm = text_wpm[easiest_idx, "avg_wpm"]
    hardest_text = text_wpm[hardest_idx, "text_id"]
    hardest_wpm = text_wpm[hardest_idx, "avg_wpm"]
    
    gap = easiest_wpm - hardest_wpm
    
    return [
        f"Easiest text: #{easiest_text} ({easiest_wpm:.1f} WPM)",
        f"Hardest text: #{hardest_text} ({hardest_wpm:.1f} WPM)",
        f"Text difficulty range: {gap:.1f} WPM spread"
    ]

# Add remaining insight calculation functions...
# For brevity, I'll implement the most complex ones and create placeholders for others

def calculate_consistency_insights(df: pl.DataFrame) -> List[str]:
    """Calculate insights for consistency score"""
    if len(df) < 30:
        return ["Need 30+ races for consistency", "Current data shown", "Keep racing for insights"]
    
    df_sorted = df.sort("race_num")
    
    # Calculate rolling std dev
    rolling_std = []
    for i in range(29, len(df_sorted)):
        window = df_sorted[i-29:i+1]["wpm"]
        rolling_std.append(window.std())
    
    min_std_idx = np.argmin(rolling_std)
    max_std_idx = np.argmax(rolling_std)
    
    overall_cv = (df["wpm"].std() / df["wpm"].mean()) * 100
    
    return [
        f"Most consistent period: Race {min_std_idx + 30} (σ={rolling_std[min_std_idx]:.1f})",
        f"Most variable period: Race {max_std_idx + 30} (σ={rolling_std[max_std_idx]:.1f})",
        f"Overall consistency: {overall_cv:.1f}% coefficient of variation"
    ]

# Placeholder functions for remaining charts
def calculate_accuracy_by_rank_insights(df: pl.DataFrame) -> List[str]:
    rank_acc = df.group_by("rank").agg([pl.col("accuracy").mean().alias("avg_acc")])
    
    rank_1_acc = rank_acc.filter(pl.col("rank") == 1)["avg_acc"].mean() * 100
    last_rank = rank_acc["rank"].max()
    last_acc = rank_acc.filter(pl.col("rank") == last_rank)["avg_acc"].mean() * 100
    pressure_drop = rank_1_acc - last_acc
    
    return [
        f"Rank 1 accuracy: {rank_1_acc:.1f}%",
        f"Last place accuracy: {last_acc:.1f}%",
        f"Pressure effect: {pressure_drop:.1f}% accuracy drop under pressure"
    ]

# Add remaining placeholder functions...
def calculate_cumulative_accuracy_insights(df: pl.DataFrame) -> List[str]:
    if len(df) < 200:
        return ["Need 200+ races", "Early career data", "Keep racing for comparison"]
    
    early_acc = df.head(100)["accuracy"].mean() * 100
    recent_acc = df.tail(100)["accuracy"].mean() * 100
    change = recent_acc - early_acc
    
    return [
        f"First 100 races: {early_acc:.1f}%",
        f"Last 100 races: {recent_acc:.1f}%",
        f"Accuracy improvement: {change:+.1f}% over time"
    ]

def calculate_wpm_by_rank_insights(df: pl.DataFrame) -> List[str]:
    rank_wpm = df.group_by("rank").agg([
        pl.col("wpm").min().alias("min_wpm"),
        pl.col("wpm").max().alias("max_wpm"),
        pl.col("wpm").std().alias("std_wpm")
    ])
    
    rank_1_stats = rank_wpm.filter(pl.col("rank") == 1)
    if len(rank_1_stats) > 0:
        r1_min = rank_1_stats[0, "min_wpm"]
        r1_max = rank_1_stats[0, "max_wpm"]
        
        # Find most consistent rank (lowest std dev)
        consistent_rank = rank_wpm.filter(pl.col("std_wpm") == rank_wpm["std_wpm"].min())[0, "rank"]
        
        # Find biggest upset (high WPM at low rank)
        upset_data = df.filter(pl.col("rank") > 5).top_k(1, by="wpm")
        upset_wpm = upset_data[0, "wpm"] if len(upset_data) > 0 else 0
        upset_rank = upset_data[0, "rank"] if len(upset_data) > 0 else 0
        
        return [
            f"Rank 1 range: {r1_min:.0f}-{r1_max:.0f} WPM",
            f"Most consistent rank: #{consistent_rank}",
            f"Biggest upset: {upset_wpm:.0f} WPM at rank #{upset_rank}"
        ]
    
    return ["Need more race data", "Race placement analysis", "Upload more races"]

def calculate_racers_impact_insights(df: pl.DataFrame) -> List[str]:
    racers_wpm = df.group_by("num_racers").agg([pl.col("wpm").mean().alias("avg_wpm")])
    
    solo_wpm = racers_wpm.filter(pl.col("num_racers") == 1)["avg_wpm"].mean() if len(racers_wpm.filter(pl.col("num_racers") == 1)) > 0 else 0
    large_field_wpm = racers_wpm.filter(pl.col("num_racers") >= 20)["avg_wpm"].mean() if len(racers_wpm.filter(pl.col("num_racers") >= 20)) > 0 else 0
    
    optimal_idx = racers_wpm["avg_wpm"].arg_max()
    optimal_size = racers_wpm[optimal_idx, "num_racers"]
    optimal_wpm = racers_wpm[optimal_idx, "avg_wpm"]
    
    return [
        f"Solo races: {solo_wpm:.1f} WPM average" if solo_wpm > 0 else "No solo races found",
        f"Large fields (20+ racers): {large_field_wpm:.1f} WPM" if large_field_wpm > 0 else "No large fields found",
        f"Optimal field size: {optimal_size} racers ({optimal_wpm:.1f} WPM)"
    ]

def calculate_frequent_texts_insights(df: pl.DataFrame) -> List[str]:
    text_counts = df.group_by("text_id").agg([pl.count().alias("count")])
    most_practiced_idx = text_counts["count"].arg_max()
    most_practiced_text = text_counts[most_practiced_idx, "text_id"]
    most_practiced_count = text_counts[most_practiced_idx, "count"]
    
    # Get improvement for most practiced text
    text_data = df.filter(pl.col("text_id") == most_practiced_text).sort("race_num")
    if len(text_data) >= 2:
        first_attempt = text_data[0, "wpm"]
        best_attempt = text_data["wpm"].max()
        learning_rate = (best_attempt - first_attempt) / (len(text_data) - 1)
        
        return [
            f"Most practiced text: #{most_practiced_text} ({most_practiced_count} times)",
            f"Improvement: {first_attempt:.1f} → {best_attempt:.1f} WPM",
            f"Learning rate: +{learning_rate:.1f} WPM per attempt"
        ]
    
    return ["Need more repeated texts", "Practice same texts more", "Upload more race data"]

def calculate_top_texts_distribution_insights(df: pl.DataFrame) -> List[str]:
    # Get most practiced texts
    text_counts = df.group_by("text_id").agg([
        pl.count().alias("count"),
        pl.col("wpm").mean().alias("avg_wpm")
    ]).top_k(10, by="count")
    
    if len(text_counts) == 0:
        return ["Need more race data", "Practice texts repeatedly", "Upload more races"]
    
    practiced_avg = text_counts["avg_wpm"].mean()
    overall_avg = df["wpm"].mean()
    min_wpm = text_counts["avg_wpm"].min()
    max_wpm = text_counts["avg_wpm"].max()
    above_avg_pct = (text_counts.filter(pl.col("avg_wpm") > overall_avg).height / len(text_counts)) * 100
    
    return [
        f"Most practiced texts average: {practiced_avg:.1f} WPM",
        f"Range across texts: {min_wpm:.0f}-{max_wpm:.0f} WPM",
        f"Mastery level: {above_avg_pct:.0f}% above personal average"
    ]

def calculate_win_rate_after_win_insights(df: pl.DataFrame) -> List[str]:
    df_sorted = df.sort("race_num")
    df_pandas = df_sorted.to_pandas()
    df_pandas['prev_win'] = df_pandas['win'].shift(1).fillna(0)
    
    after_win_rate = df_pandas[df_pandas['prev_win'] == 1]['win'].mean() * 100
    after_loss_rate = df_pandas[df_pandas['prev_win'] == 0]['win'].mean() * 100
    momentum_effect = after_win_rate - after_loss_rate
    
    return [
        f"After winning: {after_win_rate:.1f}% win rate",
        f"After losing: {after_loss_rate:.1f}% win rate",
        f"Momentum effect: {momentum_effect:+.1f}% higher after wins"
    ]

def calculate_fastest_slowest_insights(df: pl.DataFrame) -> List[str]:
    best_race = df.top_k(1, by="wpm")
    worst_race = df.bottom_k(1, by="wpm")
    
    best_wpm = best_race[0, "wpm"]
    best_race_num = best_race[0, "race_num"]
    worst_wpm = worst_race[0, "wpm"]
    worst_race_num = worst_race[0, "race_num"]
    
    gap = best_wpm - worst_wpm
    
    return [
        f"Best race: {best_wpm:.1f} WPM (Race #{best_race_num})",
        f"Worst race: {worst_wpm:.1f} WPM (Race #{worst_race_num})",
        f"Performance range: {gap:.1f} WPM total spread"
    ]

def calculate_time_between_races_insights(df: pl.DataFrame) -> List[str]:
    df_sorted = df.sort("datetime_utc")
    df_pandas = df_sorted.to_pandas()
    
    # Calculate time differences in hours
    df_pandas['time_diff_hours'] = df_pandas['datetime_utc'].diff().dt.total_seconds().div(3600).fillna(0)
    
    # Quick succession (<1hr)
    quick_races = df_pandas[df_pandas['time_diff_hours'] < 1]
    quick_avg = quick_races['wpm'].mean() if len(quick_races) > 0 else 0
    
    # After breaks (>24hr)
    break_races = df_pandas[df_pandas['time_diff_hours'] > 24]
    break_avg = break_races['wpm'].mean() if len(break_races) > 0 else 0
    
    # Find optimal rest time
    bins = [0, 1, 3, 6, 12, 24, 48, 168, float('inf')]
    labels = ['0-1h', '1-3h', '3-6h', '6-12h', '12-24h', '24-48h', '48h-1wk', '1wk+']
    df_pandas['time_bin'] = pd.cut(df_pandas['time_diff_hours'], bins=bins, labels=labels)
    
    time_wpm = df_pandas.groupby('time_bin', observed=False)['wpm'].mean()
    optimal_time = time_wpm.idxmax()
    optimal_wpm = time_wpm.max()
    
    return [
        f"Quick succession (<1hr): {quick_avg:.1f} WPM" if quick_avg > 0 else "No quick succession races",
        f"After breaks (>24hr): {break_avg:.1f} WPM" if break_avg > 0 else "No long break races",
        f"Optimal rest time: {optimal_time} ({optimal_wpm:.1f} WPM)"
    ]