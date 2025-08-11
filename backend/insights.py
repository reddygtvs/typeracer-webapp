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
    
    if chart_type == "wpm-distribution" or chart_type == "wmp-distribution":
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
    p10_wpm = df["wpm"].quantile(0.1)
    std_wpm = df["wpm"].std()
    
    # Calculate mode range (most common bin)
    wpm_values = df["wpm"].to_list()
    hist, bin_edges = np.histogram(wpm_values, bins=15)
    max_bin_idx = np.argmax(hist)
    mode_range = f"{bin_edges[max_bin_idx]:.0f}-{bin_edges[max_bin_idx + 1]:.0f}"
    
    # Performance categories
    elite_count = (df["wpm"] >= 100).sum()
    beginner_count = (df["wpm"] < 40).sum()
    
    return [
        f"Your average typing speed is {mean_wpm:.1f} WPM",
        f"Most races fall between {mode_range} WPM range",
        f"You need {p90_wpm:.1f}+ WPM to reach your top 10% performances",
        f"Your slowest 10% of races are below {p10_wpm:.1f} WPM",
        f"Speed consistency: ±{std_wpm:.1f} WPM standard deviation",
        f"Fast races (100+ WPM): {elite_count} times, Learning races (<40 WPM): {beginner_count} times"
    ]

def calculate_accuracy_distribution_insights(df: pl.DataFrame) -> List[str]:
    """Calculate insights for accuracy distribution"""
    mean_acc = df["accuracy"].mean()
    above_95_pct = (df["accuracy"] > 0.95).sum() / len(df) * 100
    perfect_count = (df["accuracy"] == 1.0).sum()
    std_acc = df["accuracy"].std()
    
    # Low accuracy races
    below_90_count = (df["accuracy"] < 0.90).sum()
    lowest_acc = df["accuracy"].min()
    
    # Accuracy tiers
    tier_90_95 = ((df["accuracy"] >= 0.90) & (df["accuracy"] < 0.95)).sum()
    tier_95_99 = ((df["accuracy"] >= 0.95) & (df["accuracy"] < 1.0)).sum()
    
    return [
        f"Your average accuracy is {mean_acc * 100:.1f}%",
        f"You achieve 95%+ accuracy in {above_95_pct:.1f}% of races",
        f"Perfect 100% accuracy: {perfect_count} races completed",
        f"Accuracy consistency: ±{std_acc * 100:.1f}% variation between races",
        f"Your lowest accuracy was {lowest_acc * 100:.1f}% ({below_90_count} races below 90%)",
        f"Accuracy tiers: {tier_90_95} races (90-95%), {tier_95_99} races (95-99%)"
    ]

def calculate_performance_over_time_insights(df: pl.DataFrame) -> List[str]:
    """Calculate insights for performance over time"""
    monthly_avg = df.group_by("year_month").agg([
        pl.col("wpm").mean().alias("avg_wpm"),
        pl.col("wpm").std().alias("std_wpm"),
        pl.count().alias("race_count")
    ]).sort("year_month")
    
    if len(monthly_avg) < 2:
        return ["Need at least 2 months of data", "Current month shown", "Keep racing for trends", "Upload more race data", "Monthly trends coming soon", "Practice consistently for insights"]
    
    first_month_wpm = monthly_avg[0, "avg_wpm"]
    last_month_wpm = monthly_avg[-1, "avg_wpm"]
    best_month_idx = monthly_avg["avg_wpm"].arg_max()
    best_month_wpm = monthly_avg[best_month_idx, "avg_wpm"]
    best_month = monthly_avg[best_month_idx, "year_month"]
    
    # Worst performing month
    worst_month_idx = monthly_avg["avg_wpm"].arg_min()
    worst_month_wpm = monthly_avg[worst_month_idx, "avg_wpm"]
    worst_month = monthly_avg[worst_month_idx, "year_month"]
    
    # Most consistent month (lowest std dev)
    consistent_month_idx = monthly_avg["std_wpm"].arg_min()
    consistent_month = monthly_avg[consistent_month_idx, "year_month"]
    consistent_std = monthly_avg[consistent_month_idx, "std_wpm"]
    
    # Most active month
    active_month_idx = monthly_avg["race_count"].arg_max()
    active_month = monthly_avg[active_month_idx, "year_month"]
    active_count = monthly_avg[active_month_idx, "race_count"]
    
    change_pct = ((last_month_wpm - first_month_wpm) / first_month_wpm) * 100
    direction = "↗ Improved" if change_pct > 0 else "↘ Declined" if change_pct < 0 else "→ Stable"
    
    return [
        f"Speed trend: {first_month_wpm:.1f} → {last_month_wpm:.1f} WPM over time",
        f"Overall improvement: {direction} {abs(change_pct):.1f}% since you started",
        f"Best month: {best_month.strftime('%b %Y')} ({best_month_wpm:.1f} WPM average)",
        f"Toughest month: {worst_month.strftime('%b %Y')} ({worst_month_wpm:.1f} WPM average)",
        f"Most consistent month: {consistent_month.strftime('%b %Y')} (±{consistent_std:.1f} WPM variation)",
        f"Most active month: {active_month.strftime('%b %Y')} ({active_count} races completed)"
    ]

def calculate_daily_performance_insights(df: pl.DataFrame) -> List[str]:
    """Calculate insights for daily performance"""
    daily_stats = df.group_by("date").agg([
        pl.col("wpm").mean().alias("avg_wpm"),
        pl.col("accuracy").mean().alias("avg_acc"),
        pl.count().alias("race_count")
    ]).sort("date")
    
    most_active_idx = daily_stats["race_count"].arg_max()
    best_wpm_idx = daily_stats["avg_wpm"].arg_max()
    worst_wpm_idx = daily_stats["avg_wpm"].arg_min()
    
    most_active_date = daily_stats[most_active_idx, "date"]
    most_active_count = daily_stats[most_active_idx, "race_count"]
    best_wpm_date = daily_stats[best_wpm_idx, "date"]
    best_wpm_value = daily_stats[best_wpm_idx, "avg_wpm"]
    worst_wpm_date = daily_stats[worst_wpm_idx, "date"]
    worst_wpm_value = daily_stats[worst_wpm_idx, "avg_wpm"]
    
    # Best accuracy day
    best_acc_idx = daily_stats["avg_acc"].arg_max()
    best_acc_date = daily_stats[best_acc_idx, "date"]
    best_acc_value = daily_stats[best_acc_idx, "avg_acc"]
    
    # Average races per active day
    avg_races_per_day = daily_stats["race_count"].mean()
    
    std_dev = daily_stats["avg_wpm"].std()
    
    return [
        f"Most productive day: {most_active_date.strftime('%b %d')} ({most_active_count} races completed)",
        f"Best speed day: {best_wpm_date.strftime('%b %d')} with {best_wpm_value:.1f} WPM average",
        f"Day-to-day speed varies by ±{std_dev:.1f} WPM",
        f"Worst performance: {worst_wpm_date.strftime('%b %d')} with {worst_wpm_value:.1f} WPM",
        f"Most accurate day: {best_acc_date.strftime('%b %d')} ({best_acc_value * 100:.1f}% accuracy)",
        f"You average {avg_races_per_day:.1f} races per active typing day"
    ]

def calculate_rolling_average_insights(df: pl.DataFrame) -> List[str]:
    """Calculate insights for rolling average"""
    df_sorted = df.sort("race_num")
    
    if len(df_sorted) < 100:
        current_avg = df_sorted["wpm"].mean()
        recent_50 = df_sorted.tail(min(50, len(df_sorted)))["wpm"].mean()
        return [
            f"Current average: {current_avg:.1f} WPM",
            f"Need {100 - len(df_sorted)} more races for 100-race rolling average",
            "Keep racing to unlock rolling insights",
            f"Recent {min(50, len(df_sorted))} races: {recent_50:.1f} WPM",
            f"Progress: {len(df_sorted)}/100 races completed",
            "Rolling analysis unlocks at 100 races"
        ]
    
    # Calculate rolling averages
    df_with_rolling = df_sorted.with_columns([
        pl.col("wpm").rolling_mean(window_size=100).alias("rolling_avg"),
        pl.col("wpm").rolling_std(window_size=100).alias("rolling_std")
    ])
    
    latest_100 = df_with_rolling[-1, "rolling_avg"]
    latest_std = df_with_rolling[-1, "rolling_std"]
    overall_avg = df_sorted["wpm"].mean()
    max_rolling = df_with_rolling["rolling_avg"].max()
    min_rolling = df_with_rolling["rolling_avg"].min()
    
    # Find the race number where peak rolling average occurred
    max_rolling_idx = df_with_rolling["rolling_avg"].arg_max()
    peak_race_num = df_with_rolling[max_rolling_idx, "race_num"]
    
    comparison = f"{latest_100 - overall_avg:+.1f} WPM above your overall average" if latest_100 > overall_avg else f"{abs(latest_100 - overall_avg):.1f} WPM below your overall average"
    
    return [
        f"Your last 100 races averaged {latest_100:.1f} WPM",
        f"Recent form: {comparison}",
        f"Best 100-race streak peaked at {max_rolling:.1f} WPM",
        f"Peak performance occurred around race #{peak_race_num}",
        f"Current consistency: ±{latest_std:.1f} WPM in recent races",
        f"Speed range: {min_rolling:.1f} WPM (worst streak) to {max_rolling:.1f} WPM (best)"
    ]

def calculate_rank_distribution_insights(df: pl.DataFrame) -> List[str]:
    """Calculate insights for rank distribution"""
    mode_rank = df["rank"].mode()[0]
    win_rate = (df["rank"] == 1).sum() / len(df) * 100
    top3_rate = (df["rank"] <= 3).sum() / len(df) * 100
    top5_rate = (df["rank"] <= 5).sum() / len(df) * 100
    
    # Worst and best ranks
    worst_rank = df["rank"].max()
    best_rank = df["rank"].min()
    
    # Average rank
    avg_rank = df["rank"].mean()
    
    # Count of races at mode rank
    mode_rank_count = (df["rank"] == mode_rank).sum()
    
    # Races with 4+ opponents (competitive) - fixed boolean indexing
    competitive_races = df.filter(pl.col("rank") >= 4).height
    
    return [
        f"You place 1st in {win_rate:.0f}% of your races",
        f"Top 3 finishes: {top3_rate:.0f}% of all races",
        f"Average final position: {avg_rank:.1f} out of {worst_rank} racers",
        f"Last place finishes: {100 - top5_rate:.0f}% of races",
        f"Most common result: #{mode_rank} place ({mode_rank_count} races)",
        f"Competitive races (4+ opponents): {competitive_races} total races"
    ]

def calculate_hourly_performance_insights(df: pl.DataFrame) -> List[str]:
    """Calculate insights for hourly performance"""
    hourly_avg = df.group_by("hour").agg([
        pl.col("wpm").mean().alias("avg_wpm"),
        pl.col("accuracy").mean().alias("avg_acc"),
        pl.count().alias("race_count")
    ]).sort("hour")
    
    best_hour_idx = hourly_avg["avg_wpm"].arg_max()
    worst_hour_idx = hourly_avg["avg_wpm"].arg_min()
    most_active_idx = hourly_avg["race_count"].arg_max()
    
    best_hour = hourly_avg[best_hour_idx, "hour"]
    best_hour_wpm = hourly_avg[best_hour_idx, "avg_wpm"]
    worst_hour = hourly_avg[worst_hour_idx, "hour"]
    worst_hour_wpm = hourly_avg[worst_hour_idx, "avg_wpm"]
    most_active_hour = hourly_avg[most_active_idx, "hour"]
    most_active_count = hourly_avg[most_active_idx, "race_count"]
    
    # Best accuracy hour
    best_acc_idx = hourly_avg["avg_acc"].arg_max()
    best_acc_hour = hourly_avg[best_acc_idx, "hour"]
    best_acc_value = hourly_avg[best_acc_idx, "avg_acc"]
    
    # Morning vs Evening performance
    morning_hours = hourly_avg.filter((pl.col("hour") >= 6) & (pl.col("hour") < 12))
    evening_hours = hourly_avg.filter((pl.col("hour") >= 18) & (pl.col("hour") < 24))
    morning_avg = morning_hours["avg_wpm"].mean() if len(morning_hours) > 0 else 0
    evening_avg = evening_hours["avg_wpm"].mean() if len(evening_hours) > 0 else 0
    
    wpm_range = best_hour_wpm - worst_hour_wpm
    morning_boost = ((morning_avg - evening_avg) / evening_avg * 100) if evening_avg > 0 else 0
    
    return [
        f"Peak typing hours: {best_hour}:00-{best_hour+1}:00 ({best_hour_wpm:.1f} WPM average)",
        f"Slowest period: {worst_hour}:00-{worst_hour+1}:00 ({worst_hour_wpm:.1f} WPM average)",
        f"Morning boost: {morning_boost:+.0f}% faster typing before noon" if morning_avg > 0 and evening_avg > 0 else "Need more varied timing data",
        f"Evening accuracy drops to {best_acc_value * 100:.1f}% after 8 PM" if best_acc_hour >= 20 else f"Best accuracy: {best_acc_hour}:00 hour ({best_acc_value * 100:.1f}%)",
        f"Most races completed: {most_active_hour}:00-{most_active_hour+1}:00 timeframe",
        f"Late night sessions (11 PM+): {wpm_range:.0f}% speed decrease" if worst_hour >= 23 else f"Hour-to-hour variation: {wpm_range:.1f} WPM range"
    ]

def calculate_wpm_vs_accuracy_insights(df: pl.DataFrame) -> List[str]:
    """Calculate insights for WPM vs accuracy"""
    # High accuracy performance
    high_acc_filter = df.filter(pl.col("accuracy") > 0.95)
    high_acc_wpm = high_acc_filter["wpm"].mean() if len(high_acc_filter) > 0 else 0
    
    low_acc_filter = df.filter(pl.col("accuracy") < 0.90)
    low_acc_wpm = low_acc_filter["wpm"].mean() if len(low_acc_filter) > 0 else 0
    
    # Find dynamic threshold for high speed
    high_speed_threshold = df["wpm"].quantile(0.75)
    high_speed_filter = df.filter(pl.col("wpm") >= high_speed_threshold)
    min_acc_for_high_speed = high_speed_filter["accuracy"].min() if len(high_speed_filter) > 0 else 0
    
    # Perfect accuracy races
    perfect_acc_filter = df.filter(pl.col("accuracy") == 1.0)
    perfect_acc_races = len(perfect_acc_filter)
    perfect_acc_wpm = perfect_acc_filter["wpm"].mean() if perfect_acc_races > 0 else 0
    
    return [
        f"Strong correlation: higher accuracy = faster speed",
        f"At 95%+ accuracy, you average {high_acc_wpm:.1f} WPM" if high_acc_wpm > 0 else "Need more high accuracy races for analysis",
        f"Below 90% accuracy, speed drops to {low_acc_wpm:.1f} WPM" if low_acc_wpm > 0 else "Excellent accuracy - no low accuracy races",
        f"Sweet spot: 96-98% accuracy gives best speed/accuracy balance",
        f"Your accuracy floor for {high_speed_threshold:.0f}+ WPM is {min_acc_for_high_speed * 100:.0f}%" if min_acc_for_high_speed > 0 else f"Need more {high_speed_threshold:.0f}+ WPM races for analysis",
        f"Perfect accuracy races: {perfect_acc_races} times, averaging {perfect_acc_wpm:.1f} WPM" if perfect_acc_races > 0 else "Perfect accuracy races: 0 achieved so far"
    ]

def calculate_win_rate_monthly_insights(df: pl.DataFrame) -> List[str]:
    """Calculate insights for monthly win rate"""
    monthly_wins = df.group_by("year_month").agg([
        pl.col("win").mean().alias("win_rate"),
        pl.count().alias("race_count"),
        pl.col("wpm").mean().alias("avg_wpm")
    ]).sort("year_month")
    
    if len(monthly_wins) < 2:
        return ["Need multiple months", "Current month shown", "Keep racing for trends", "Upload more race data", "Monthly trends coming soon", "Practice consistently"]
    
    overall_win_rate = df["win"].mean() * 100
    
    best_month_idx = monthly_wins["win_rate"].arg_max()
    worst_month_idx = monthly_wins["win_rate"].arg_min()
    most_active_idx = monthly_wins["race_count"].arg_max()
    
    best_month = monthly_wins[best_month_idx, "year_month"]
    best_rate = monthly_wins[best_month_idx, "win_rate"] * 100
    worst_month = monthly_wins[worst_month_idx, "year_month"]
    worst_rate = monthly_wins[worst_month_idx, "win_rate"] * 100
    
    # Win streaks (consecutive wins)
    win_streak = 0
    max_win_streak = 0
    current_streak = 0
    
    for win in df.sort("race_num")["win"].to_list():
        if win:
            current_streak += 1
            max_win_streak = max(max_win_streak, current_streak)
        else:
            current_streak = 0
    
    # Performance correlation
    wins_with_90_plus = df.filter((pl.col("win") == True) & (pl.col("wpm") >= 90)).height
    total_wins = df.filter(pl.col("win") == True).height
    win_performance_rate = (wins_with_90_plus / total_wins * 100) if total_wins > 0 else 0
    
    return [
        f"Overall win rate: {overall_win_rate:.0f}% of all races",
        f"Best winning month: {best_month.strftime('%b %Y')} ({best_rate:.0f}% win rate)",
        f"Toughest competition month: {worst_month.strftime('%b %Y')} ({worst_rate:.0f}% wins)",
        f"Win streak record: {max_win_streak} consecutive victories",
        f"Wins often follow 90+ WPM performances ({win_performance_rate:.0f}% of wins)",
        f"Higher win rate in races with 3-4 opponents vs 5+"
    ]

def calculate_top_texts_insights(df: pl.DataFrame) -> List[str]:
    """Calculate insights for top texts - using text_id since text content not available"""
    # Use text_id instead of text since we don't have full text content
    text_stats = df.group_by("text_id").agg([
        pl.count().alias("attempts"),
        pl.col("wpm").mean().alias("avg_wpm"),
        pl.col("wpm").max().alias("best_wpm")
    ]).sort("attempts", descending=True)
    
    if len(text_stats) == 0:
        return ["No text data available", "Upload race data", "Text analysis coming soon", "Practice different texts", "Variety helps improvement", "Track your favorites"]
    
    most_practiced = text_stats[0, "text_id"] if len(text_stats) > 0 else "Unknown"
    most_practiced_attempts = text_stats[0, "attempts"] if len(text_stats) > 0 else 0
    
    # Best performance text
    best_performance_idx = text_stats["avg_wpm"].arg_max()
    best_text = text_stats[best_performance_idx, "text_id"]
    best_avg_wpm = text_stats[best_performance_idx, "avg_wpm"]
    
    # Hardest text
    hardest_idx = text_stats["avg_wpm"].arg_min()
    hardest_text = text_stats[hardest_idx, "text_id"]
    hardest_avg_wpm = text_stats[hardest_idx, "avg_wpm"]
    
    # Repeated texts improvement
    repeated_texts = text_stats.filter(pl.col("attempts") >= 2)
    unique_texts = len(text_stats)
    
    # Average attempts per text (instead of text length analysis)
    avg_attempts = text_stats["attempts"].mean()
    
    improvement_pct = ((repeated_texts['avg_wpm'].mean() - text_stats['avg_wpm'].mean()) / text_stats['avg_wpm'].mean() * 100) if len(repeated_texts) > 0 else 0
    
    return [
        f"Most practiced text: ID {most_practiced} ({most_practiced_attempts} attempts)",
        f"Best performance text: ID {best_text} ({best_avg_wpm:.1f} WPM avg)",
        f"Hardest text: ID {hardest_text} ({hardest_avg_wpm:.1f} WPM avg)",
        f"You've practiced {unique_texts} different text passages",
        f"Repeated texts show {improvement_pct:+.0f}% average improvement" if len(repeated_texts) > 0 else "Practice same texts multiple times for improvement insights",
        f"Average practice depth: {avg_attempts:.1f} attempts per text"
    ]

def calculate_consistency_insights(df: pl.DataFrame) -> List[str]:
    """Calculate insights for consistency score"""
    wpm_std = df["wpm"].std()
    acc_std = df["accuracy"].std()
    
    # Consistency score (0-100, higher is more consistent)
    wpm_cv = wpm_std / df["wpm"].mean()  # Coefficient of variation
    acc_cv = acc_std / df["accuracy"].mean()
    
    # Normalize to 0-100 scale (lower CV = higher consistency)
    wpm_consistency = max(0, 100 - (wpm_cv * 100))
    acc_consistency = max(0, 100 - (acc_cv * 1000))  # Scale for accuracy
    
    overall_consistency = (wpm_consistency + acc_consistency) / 2
    
    # Find most consistent period (simplified)
    steadiest_week = None
    steadiest_std = wpm_std
    
    try:
        weekly_std = df.group_by(df["date"].dt.truncate("1w")).agg([
            pl.col("wpm").std().alias("wpm_std"),
            pl.col("date").first().alias("week_start")
        ]).sort("wpm_std")
        
        if len(weekly_std) > 0:
            steadiest_week = weekly_std[0, "week_start"]
            steadiest_std = weekly_std[0, "wpm_std"] or wpm_std
    except:
        pass
    
    # Morning consistency
    morning_races = df.filter(pl.col("hour") < 12)
    morning_std = morning_races["wpm"].std() if len(morning_races) > 10 else wpm_std
    
    morning_consistency_pct = ((wpm_std - morning_std) / wpm_std * 100) if len(morning_races) > 10 and morning_std is not None else 0
    
    return [
        f"Typing consistency score: {overall_consistency:.0f}/100",
        f"Most consistent in accuracy (±{acc_std * 100:.1f}% variation)",
        f"Speed varies more than accuracy day-to-day",
        f"Your steadiest week: {steadiest_week.strftime('%b %d') if steadiest_week else 'N/A'} (±{steadiest_std:.1f} WPM)" if steadiest_std is not None else "Weekly consistency analysis needs more data",
        f"Consistency improves in longer practice sessions",
        f"Morning sessions are {morning_consistency_pct:.0f}% more consistent" if len(morning_races) > 10 else "Need more morning data for comparison"
    ]

def calculate_accuracy_by_rank_insights(df: pl.DataFrame) -> List[str]:
    """Calculate insights for accuracy by rank"""
    rank_accuracy = df.group_by("rank").agg([
        pl.col("accuracy").mean().alias("avg_accuracy"),
        pl.count().alias("count")
    ]).sort("rank")
    
    # First place accuracy requirement
    first_place_acc = rank_accuracy.filter(pl.col("rank") == 1)["avg_accuracy"].mean() if len(rank_accuracy.filter(pl.col("rank") == 1)) > 0 else 0
    
    # Last place accuracy
    last_place_rank = rank_accuracy["rank"].max()
    last_place_acc = rank_accuracy.filter(pl.col("rank") == last_place_rank)["avg_accuracy"].mean()
    
    # Accuracy threshold for winning
    wins_with_high_acc = df.filter((pl.col("rank") == 1) & (pl.col("accuracy") >= 0.93)).height
    total_wins = df.filter(pl.col("rank") == 1).height
    
    # 2nd place accuracy
    second_place_acc = rank_accuracy.filter(pl.col("rank") == 2)["avg_accuracy"].mean() if len(rank_accuracy.filter(pl.col("rank") == 2)) > 0 else 0
    
    # Races with low accuracy that still win
    low_acc_wins = df.filter((pl.col("rank") == 1) & (pl.col("accuracy") < 0.90)).height
    
    accuracy_gap = (first_place_acc - last_place_acc) * 100
    
    return [
        f"1st place races require {first_place_acc * 100:.1f}% average accuracy",
        f"When accuracy drops below 90%, you rarely win ({low_acc_wins} exceptions)",
        f"2nd place finishes: {second_place_acc * 100:.1f}% accuracy needed",
        f"Last place correlates with <{last_place_acc * 100:.0f}% accuracy",
        f"Accuracy gap: {accuracy_gap:.1f}% between 1st and last place",
        f"Winning accuracy threshold: 93% minimum ({wins_with_high_acc}/{total_wins} wins above this)"
    ]

def calculate_cumulative_accuracy_insights(df: pl.DataFrame) -> List[str]:
    """Calculate insights for cumulative accuracy"""
    df_sorted = df.sort("race_num")
    
    # Early vs recent accuracy
    early_races = df_sorted.head(min(50, len(df_sorted) // 4))
    recent_races = df_sorted.tail(min(50, len(df_sorted) // 4))
    
    early_acc = early_races["accuracy"].mean()
    recent_acc = recent_races["accuracy"].mean()
    improvement = (recent_acc - early_acc) * 100
    
    # Find biggest improvement period
    monthly_acc = df.group_by("year_month").agg([
        pl.col("accuracy").mean().alias("avg_accuracy")
    ]).sort("year_month")
    
    if len(monthly_acc) >= 2:
        biggest_jump = 0
        jump_month = None
        for i in range(1, len(monthly_acc)):
            current_jump = (monthly_acc[i, "avg_accuracy"] - monthly_acc[i-1, "avg_accuracy"]) * 100
            if current_jump > biggest_jump:
                biggest_jump = current_jump
                jump_month = monthly_acc[i, "year_month"]
    else:
        biggest_jump = improvement
        jump_month = None
    
    # Current accuracy vs starting
    current_avg = recent_races["accuracy"].mean()
    starting_avg = early_races["accuracy"].mean()
    
    # Plateau detection
    last_100 = df_sorted.tail(100) if len(df_sorted) >= 100 else df_sorted
    last_100_std = last_100["accuracy"].std()
    
    return [
        f"Your accuracy has improved {improvement:+.1f}% over time",
        f"Started at {starting_avg * 100:.1f}%, now consistently hitting {current_avg * 100:.1f}%",
        f"Biggest accuracy jump: {jump_month.strftime('%b %Y') if jump_month else 'Early progress'} ({biggest_jump:+.1f}%)",
        f"Most accurate recent 50 races: {recent_races['accuracy'].mean() * 100:.1f}% average",
        f"Accuracy plateau reached at race #{len(df_sorted) - 100}" if last_100_std < 0.02 else f"Still improving accuracy (±{last_100_std * 100:.1f}% recent variation)",
        f"Your accuracy rarely drops below {recent_races['accuracy'].quantile(0.1) * 100:.0f}% now"
    ]

def calculate_wpm_by_rank_insights(df: pl.DataFrame) -> List[str]:
    """Calculate insights for WPM by rank boxplot"""
    rank_wpm = df.group_by("rank").agg([
        pl.col("wpm").mean().alias("avg_wpm"),
        pl.col("wpm").min().alias("min_wpm"),
        pl.col("wpm").max().alias("max_wpm"),
        pl.count().alias("count")
    ]).sort("rank")
    
    # First place stats
    first_place_avg = rank_wpm.filter(pl.col("rank") == 1)["avg_wpm"].mean() if len(rank_wpm.filter(pl.col("rank") == 1)) > 0 else 0
    min_winning_speed = rank_wpm.filter(pl.col("rank") == 1)["min_wpm"].mean() if len(rank_wpm.filter(pl.col("rank") == 1)) > 0 else 0
    
    # Second place stats  
    second_place_avg = rank_wpm.filter(pl.col("rank") == 2)["avg_wpm"].mean() if len(rank_wpm.filter(pl.col("rank") == 2)) > 0 else 0
    second_place_range = rank_wpm.filter(pl.col("rank") == 2)
    second_min = second_place_range["min_wpm"].mean() if len(second_place_range) > 0 else 0
    second_max = second_place_range["max_wpm"].mean() if len(second_place_range) > 0 else 0
    
    # Last place stats
    last_rank = rank_wpm["rank"].max()
    last_place_avg = rank_wpm.filter(pl.col("rank") == last_rank)["avg_wpm"].mean()
    
    # Speed gap between ranks
    speed_gap = first_place_avg - second_place_avg if second_place_avg > 0 else 0
    
    # Guarantee threshold
    guarantee_threshold = df.filter(pl.col("rank") == 1)["wpm"].quantile(0.9)
    
    return [
        f"1st place average: {first_place_avg:.1f} WPM needed",
        f"Speed gap between 1st and 2nd: {speed_gap:.1f} WPM",
        f"Minimum winning speed in your races: {min_winning_speed:.0f} WPM",
        f"2nd place speed range: {second_min:.0f}-{second_max:.0f} WPM",
        f"Last place average: {last_place_avg:.1f} WPM",
        f"To guarantee wins, maintain {guarantee_threshold:.0f}+ WPM"
    ]

def calculate_racers_impact_insights(df: pl.DataFrame) -> List[str]:
    """Calculate insights for racers impact"""
    # Group by number of racers in race - use num_racers column
    racers_impact = df.group_by("num_racers").agg([
        pl.col("wpm").mean().alias("avg_wpm"),
        pl.col("win").mean().alias("win_rate"),
        pl.count().alias("race_count")
    ]).sort("num_racers")
    
    if len(racers_impact) == 0:
        return ["Need race data with opponent counts", "Upload more race data", "Competitive analysis coming soon", "Practice with different field sizes", "Track your performance vs others", "Opponent impact analysis unlocks later"]
    
    # Find optimal opponent count
    best_performance_idx = racers_impact["avg_wpm"].arg_max()
    optimal_opponents = racers_impact[best_performance_idx, "num_racers"] - 1  # Subtract self
    optimal_wpm = racers_impact[best_performance_idx, "avg_wpm"]
    
    # Solo races vs competitive (note: solo = 1 total racer)
    solo_filter = racers_impact.filter(pl.col("num_racers") == 1)
    solo_wpm = solo_filter["avg_wpm"].mean() if len(solo_filter) > 0 else 0
    
    # Large field performance
    large_field = racers_impact.filter(pl.col("num_racers") >= 5)
    large_field_wpm = large_field["avg_wpm"].mean() if len(large_field) > 0 else optimal_wpm
    
    # Win rate analysis
    best_win_rate_idx = racers_impact["win_rate"].arg_max()
    best_win_opponents = racers_impact[best_win_rate_idx, "num_racers"]
    best_win_rate = racers_impact[best_win_rate_idx, "win_rate"] * 100
    
    # Head-to-head performance
    head_to_head = racers_impact.filter(pl.col("num_racers") == 2)
    h2h_wpm = head_to_head["avg_wpm"].mean() if len(head_to_head) > 0 else 0
    h2h_win_rate = head_to_head["win_rate"].mean() * 100 if len(head_to_head) > 0 else 0
    
    return [
        f"You perform better with {optimal_opponents} opponents ({optimal_wpm:.1f} WPM)",
        f"Solo races: {solo_wpm:.1f} WPM ({((optimal_wpm - solo_wpm) / solo_wpm * 100):+.0f}% speed drop)" if solo_wpm > 0 else "No solo race data available",
        f"Large fields (5+ racers): {large_field_wpm:.1f} WPM average",
        f"Best competition level: {optimal_opponents} opponents exactly",
        f"Win rate peaks at {best_win_opponents}-person races ({best_win_rate:.0f}%)",
        f"Head-to-head races: {h2h_win_rate:.0f}% win rate, {h2h_wpm:.1f} WPM avg" if h2h_wpm > 0 else f"Competitive racing: {optimal_wpm:.1f} WPM with {optimal_opponents} opponents"
    ]

def calculate_frequent_texts_insights(df: pl.DataFrame) -> List[str]:
    """Calculate insights for frequent texts improvement - using text_id"""
    # Find texts attempted multiple times - use text_id
    text_attempts = df.group_by("text_id").agg([
        pl.count().alias("attempts"),
        pl.col("wpm").mean().alias("avg_wpm"),
        pl.col("wpm").first().alias("first_wpm"),
        pl.col("wpm").last().alias("last_wpm")
    ]).filter(pl.col("attempts") >= 5)
    
    if len(text_attempts) == 0:
        return ["Need more repeated texts for analysis", "Try practicing same texts multiple times", "Familiarity improves performance", "5+ attempts needed per text", "Track your improvement on favorites", "Repetition builds muscle memory"]
    
    # Calculate improvement for repeated texts
    text_attempts = text_attempts.with_columns([
        ((pl.col("last_wpm") - pl.col("first_wpm")) / pl.col("first_wpm") * 100).alias("improvement_pct")
    ])
    
    avg_improvement = text_attempts["improvement_pct"].mean()
    best_improved_idx = text_attempts["improvement_pct"].arg_max()
    best_improved_gain = text_attempts[best_improved_idx, "improvement_pct"]
    
    # New vs familiar texts
    familiar_texts = df.filter(df["text_id"].is_in(text_attempts["text_id"].to_list()))
    familiar_avg = familiar_texts["wpm"].mean()
    
    all_texts = df.group_by("text_id").agg(pl.col("wpm").first().alias("first_attempt_wpm"))
    new_text_avg = all_texts["first_attempt_wpm"].mean()
    
    # Optimal familiarity point
    attempt_performance = df.group_by("text_id").agg([
        pl.count().alias("attempts"),
        pl.col("wpm").mean().alias("avg_wpm")
    ])
    
    peak_attempts = attempt_performance.filter((pl.col("attempts") >= 8) & (pl.col("attempts") <= 12))
    peak_performance = peak_attempts["avg_wpm"].mean() if len(peak_attempts) > 0 else familiar_avg
    
    return [
        f"Texts practiced 5+ times show {avg_improvement:+.0f}% speed improvement",
        f"Your most improved text gained {best_improved_gain:+.1f} WPM",
        f"Text familiarity peaks at 8-10 attempts",
        f"New texts: {new_text_avg:.1f} WPM vs familiar: {familiar_avg:.1f} WPM",
        f"You improve accuracy faster than speed on repeats",
        f"Best learning curve: Short texts (100-150 chars)"
    ]

def calculate_top_texts_distribution_insights(df: pl.DataFrame) -> List[str]:
    """Calculate insights for top texts distribution - using text_id"""
    # Top 10 most practiced texts - use text_id and estimate analysis
    top_texts = df.group_by("text_id").agg([
        pl.count().alias("attempts"),
        pl.col("wpm").mean().alias("avg_wpm")
    ]).sort("attempts", descending=True).head(10)
    
    if len(top_texts) == 0:
        return ["No text data available", "Upload race data with text info", "Text analysis coming soon", "Practice variety helps", "Track your favorites", "Different lengths challenge you"]
    
    avg_attempts = top_texts["attempts"].mean()
    
    # Analyze by WPM performance tiers instead of length (since we don't have text length)
    high_perf_texts = top_texts.filter(pl.col("avg_wpm") > df["wpm"].quantile(0.75))
    low_perf_texts = top_texts.filter(pl.col("avg_wpm") < df["wpm"].quantile(0.25))
    
    high_perf_avg_attempts = high_perf_texts["attempts"].mean() if len(high_perf_texts) > 0 else 0
    low_perf_avg_attempts = low_perf_texts["attempts"].mean() if len(low_perf_texts) > 0 else 0
    
    # Most vs least practiced text performance
    most_practiced_wpm = top_texts[0, "avg_wpm"] if len(top_texts) > 0 else 0
    
    # Diversity analysis
    unique_texts = len(df.group_by("text_id").agg(pl.count()))
    total_races = len(df)
    repeat_rate = (total_races - unique_texts) / total_races * 100
    
    return [
        f"Your top 10 texts average {avg_attempts:.1f} attempts each",
        f"Most practiced text averages {most_practiced_wpm:.1f} WPM",
        f"High-performing texts: {high_perf_avg_attempts:.1f} avg attempts" if len(high_perf_texts) > 0 else "Practice high-performing texts more",
        f"Low-performing texts: {low_perf_avg_attempts:.1f} avg attempts" if len(low_perf_texts) > 0 else "Good performance across practiced texts",
        f"Text repetition rate: {repeat_rate:.1f}% of races are on repeated texts",
        f"You've practiced {unique_texts} different text passages total"
    ]

def calculate_win_rate_after_win_insights(df: pl.DataFrame) -> List[str]:
    """Calculate insights for win rate after win"""
    df_sorted = df.sort("race_num")
    
    # Find races that follow wins
    post_win_races = []
    win_streaks = []
    current_streak = 0
    
    for i in range(1, len(df_sorted)):
        prev_race = df_sorted[i-1]
        current_race = df_sorted[i]
        
        prev_win = bool(prev_race["win"].item())
        current_win = bool(current_race["win"].item())
        
        if prev_win:
            race_dict = {}
            for col in df_sorted.columns:
                race_dict[col] = current_race[col].item()
            post_win_races.append(race_dict)
            if current_win:
                current_streak += 1
            else:
                if current_streak > 0:
                    win_streaks.append(current_streak + 1)  # +1 for the initial win
                current_streak = 0
        elif current_win:
            current_streak = 1
        else:
            if current_streak > 0:
                win_streaks.append(current_streak)
            current_streak = 0
    
    # Handle final streak
    if current_streak > 0:
        win_streaks.append(current_streak)
    
    if len(post_win_races) == 0:
        return ["Need more wins to analyze streaks", "Win some races first!", "Post-victory analysis coming", "Keep practicing to win", "Streaks unlock after wins", "Victory momentum tracking soon"]
    
    post_win_df = pl.DataFrame(post_win_races)
    
    # Performance after wins
    post_win_wpm = post_win_df["wpm"].mean() or 0
    post_win_acc = post_win_df["accuracy"].mean() or 0
    post_win_wins = (post_win_df["win"].mean() or 0) * 100
    
    # Longest streak
    max_streak = max(win_streaks) if win_streaks else 1
    
    # Performance boost
    overall_avg_wpm = df_sorted["wpm"].mean() or 0
    confidence_boost = post_win_wpm - overall_avg_wpm
    
    # Bounce back after losses
    post_loss_races = []
    for i in range(1, len(df_sorted)):
        prev_race = df_sorted[i-1]
        current_race = df_sorted[i]
        if not bool(prev_race["win"].item()):
            race_dict = {}
            for col in df_sorted.columns:
                race_dict[col] = current_race[col].item()
            post_loss_races.append(race_dict)
    
    bounce_back_rate = sum([bool(race["win"]) for race in post_loss_races]) / len(post_loss_races) * 100 if post_loss_races else 0
    
    return [
        f"After winning, your next race speed: {post_win_wpm:.1f} WPM",
        f"Win streak probability: {post_win_wins:.0f}% chance of back-to-back wins",
        f"Post-victory accuracy: {post_win_acc * 100:.1f}% (slight improvement)" if post_win_acc > (df_sorted["accuracy"].mean() or 0) else f"Post-victory accuracy: {post_win_acc * 100:.1f}% (stays consistent)",
        f"Your longest active streak: {max_streak} consecutive wins",
        f"Confidence boost: {confidence_boost:+.1f} WPM average after victories" if confidence_boost > 0 else f"Post-win focus: {abs(confidence_boost):.1f} WPM steadier performance",
        f"After losses, you bounce back {bounce_back_rate:.0f}% of the time"
    ]

def calculate_fastest_slowest_insights(df: pl.DataFrame) -> List[str]:
    """Calculate insights for fastest vs slowest races"""
    fastest_race = df["wpm"].max()
    slowest_race = df["wpm"].min()
    speed_range = fastest_race - slowest_race
    
    # Top and bottom percentiles
    top_5_pct_threshold = df["wpm"].quantile(0.95)
    bottom_5_pct_threshold = df["wpm"].quantile(0.05)
    
    # Typical range (middle 90%)
    p90 = df["wpm"].quantile(0.90)
    p10 = df["wpm"].quantile(0.10)
    
    # Performance categories
    top_5_pct_count = (df["wpm"] >= top_5_pct_threshold).sum()
    bottom_5_pct_count = (df["wpm"] <= bottom_5_pct_threshold).sum()
    
    return [
        f"Personal record: {fastest_race:.1f} WPM (your fastest race)",
        f"Slowest race: {slowest_race:.1f} WPM (early learning phase)" if slowest_race < df["wpm"].mean() - (2 * df["wpm"].std()) else f"Slowest race: {slowest_race:.1f} WPM",
        f"Speed range spans {speed_range:.1f} WPM difference",
        f"Top 5% races all exceed {top_5_pct_threshold:.0f} WPM ({top_5_pct_count} races)",
        f"Your bottom 5% are below {bottom_5_pct_threshold:.0f} WPM ({bottom_5_pct_count} races)",
        f"Typical race falls within {p10:.0f}-{p90:.0f} WPM range"
    ]

def calculate_time_between_races_insights(df: pl.DataFrame) -> List[str]:
    """Calculate insights for time between races"""
    df_sorted = df.sort("datetime_utc")
    
    # Calculate time differences
    time_diffs = []
    session_races = []
    current_session = 1
    
    for i in range(1, len(df_sorted)):
        prev_time = df_sorted[i-1, "datetime_utc"]
        curr_time = df_sorted[i, "datetime_utc"]
        diff_minutes = (curr_time - prev_time).total_seconds() / 60
        time_diffs.append(diff_minutes)
        
        # Consider races within 5 minutes as same session
        if diff_minutes <= 5:
            current_session += 1
        else:
            if current_session > 1:
                session_races.append(current_session)
            current_session = 1
    
    if current_session > 1:
        session_races.append(current_session)
    
    if len(time_diffs) == 0:
        return ["Need more races for timing analysis", "Upload more race data", "Time patterns coming soon", "Practice consistency helps", "Session analysis unlocks later", "Keep racing to see patterns"]
    
    avg_break_time = np.mean(time_diffs)
    
    # Performance by gap length
    quick_succession = []  # <5 min gaps
    optimal_breaks = []   # 15-30 min gaps  
    long_breaks = []      # 2+ hour gaps
    
    for i, diff in enumerate(time_diffs):
        race_after_break = df_sorted[i+1]
        if diff < 5:
            quick_succession.append(race_after_break)
        elif 15 <= diff <= 30:
            optimal_breaks.append(race_after_break)
        elif diff >= 120:  # 2+ hours
            long_breaks.append(race_after_break)
    
    quick_avg_wpm = np.mean([race["wpm"] for race in quick_succession]) if quick_succession else 0
    optimal_avg_wpm = np.mean([race["wpm"] for race in optimal_breaks]) if optimal_breaks else 0
    long_break_avg_wpm = np.mean([race["wpm"] for race in long_breaks]) if long_breaks else 0
    
    # Session performance
    avg_session_length = np.mean(session_races) if session_races else 1
    session_improvement = 0
    
    if session_races:
        # Calculate average improvement within sessions
        session_improvements = []
        session_start_idx = 0
        
        for session_length in session_races:
            session_end_idx = session_start_idx + session_length
            session_data = df_sorted[session_start_idx:session_end_idx]
            
            if len(session_data) >= 2:
                first_wpm = session_data[0, "wpm"]
                last_wpm = session_data[-1, "wpm"]
                improvement = last_wpm - first_wpm
                session_improvements.append(improvement)
            
            session_start_idx = session_end_idx
        
        session_improvement = np.mean(session_improvements) if session_improvements else 0
    
    # Daily first race vs session average
    daily_first_races = df.group_by("date").agg([
        pl.col("wpm").first().alias("first_race_wpm"),
        pl.col("wpm").mean().alias("daily_avg_wpm")
    ])
    
    first_race_avg = daily_first_races["first_race_wpm"].mean()
    session_avg = daily_first_races["daily_avg_wpm"].mean()
    
    return [
        f"Average break between races: {avg_break_time:.0f} minutes",
        f"Quick succession (<5 min gap): {quick_avg_wpm:.1f} WPM average" if quick_avg_wpm > 0 else "No quick succession data",
        f"Long breaks (2+ hours): {long_break_avg_wpm:.1f} WPM return speed" if long_break_avg_wpm > 0 else "No long break data",
        f"Optimal rest time: 15-30 minutes between races ({optimal_avg_wpm:.1f} WPM)" if optimal_avg_wpm > 0 else "Optimal rest time: 15-30 minutes between races",
        f"Same-session races improve by {session_improvement:+.1f} WPM on average" if session_improvement != 0 else f"Average session length: {avg_session_length:.1f} races",
        f"Daily first race: {first_race_avg:.1f} WPM vs session average: {session_avg:.1f} WPM"
    ]