import pandas as pd
import numpy as np

def process_water_quality_data(file_path):
    # Read the CSV file
    print(f"Reading data from {file_path}...")
    df = pd.read_csv(file_path)
    
    # Clean and parse the data
    print("Cleaning and parsing data...")
    
    # Filter rows with both Sample Date and Turbidity
    df = df[df["Sample Date"].notna() & df["Turbidity (NTU)"].notna()]
    
    # Parse dates
    df["Date"] = pd.to_datetime(df["Sample Date"], errors='coerce')
    df = df.dropna(subset=["Date"])  # Drop rows with invalid dates
    
    # Extract year and month
    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month
    
    # Parse turbidity values
    df["Turbidity"] = df["Turbidity (NTU)"].apply(lambda x: 
        float(''.join(c for c in str(x) if c.isdigit() or c == '.')) 
        if pd.notna(x) else np.nan)
    df = df.dropna(subset=["Turbidity"])  # Drop rows with invalid turbidity
    
    # Aggregate by year and month
    print("Aggregating turbidity by year and month...")
    monthly_avg = df.groupby(["Year", "Month"])["Turbidity"].mean().reset_index()
    
    # Convert to wide format for easier interpolation
    turbidity_wide = monthly_avg.pivot(index="Year", columns="Month", values="Turbidity")
    
    # Interpolate missing months (if 3 or fewer are missing)
    print("Interpolating missing months (if 3 or fewer are missing)...")
    processed_data = []
    complete_years = []
    
    for year, row in turbidity_wide.iterrows():
        missing_months = row.isna().sum()
        
        if missing_months <= 3:
            complete_years.append(int(year))
            interpolated_row = row.interpolate(method='linear', limit_direction='both')
            
            # Add data for each month
            for month in range(1, 13):
                if month in interpolated_row.index:
                    processed_data.append({
                        "Year": int(year),
                        "Month": month,
                        "Turbidity": float(interpolated_row[month]),
                        "Interpolated": pd.isna(row[month]) if month in row.index else True
                    })
        else:
            print(f"Dropping year {int(year)} with {missing_months} missing months")
    
    # Create the final processed dataframe
    processed_df = pd.DataFrame(processed_data)
    
    # Add month names for readability
    month_names = {
        1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
        7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
    }
    processed_df["MonthName"] = processed_df["Month"].map(month_names)
    
    # Sort by year and month
    processed_df = processed_df.sort_values(["Year", "Month"])
    
    print(f"Processing complete. Found data for {len(complete_years)} complete years.")
    
    # Save to CSV
    output_file = 'processed_turbidity_data.csv'
    processed_df.to_csv(output_file, index=False)
    print(f"Saved processed data to {output_file}")
    
    return processed_df, complete_years

# Usage
file_path = "Drinking_Water_Quality_Distribution_Monitoring_Data_20250313.csv"
processed_data, complete_years = process_water_quality_data(file_path)

print("\nYears with complete data (including interpolated months):")
print(sorted(complete_years))