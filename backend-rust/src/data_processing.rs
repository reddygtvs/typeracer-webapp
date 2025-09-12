use polars::prelude::*;
use std::io::Cursor;

pub fn process_csv_data(csv_data: &str) -> PolarsResult<DataFrame> {
    // Read CSV from string - using the correct API
    let cursor = Cursor::new(csv_data);
    let df = CsvReadOptions::default()
        .with_has_header(true)
        .into_reader_with_file_handle(cursor)
        .finish()?;

    // Process the data similar to the Python version
    let processed_df = df
        .lazy()
        .with_columns([
            // Rename columns to match Python version
            col("Race #").alias("race_num"),
            col("WPM").alias("wpm"),
            col("Accuracy").alias("accuracy"),
            col("Rank").alias("rank"),
            col("# Racers").alias("num_racers"),
            col("Text ID").alias("text_id"),
            // Parse datetime - simplified for now, we'll improve later
            col("Date/Time (UTC)").alias("datetime_utc"),
        ])
        .with_columns([
            // Create win column (1 if rank == 1, else 0)  
            (col("rank").eq(lit(1))).cast(DataType::Int32).alias("win"),
        ])
        .sort(["race_num"], SortMultipleOptions::default())
        .collect()?;

    Ok(processed_df)
}