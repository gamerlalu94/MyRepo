#!/usr/bin/env python3
"""
Sample CSV Generator for Mock Test Timer
Generates example test data to demonstrate CSV format and analysis
"""

import csv
from datetime import datetime, timedelta
from pathlib import Path

def create_sample_csv():
    """Create a sample CSV file for demonstration"""
    
    # Create logs directory if needed
    log_dir = Path("mock_test_logs")
    log_dir.mkdir(exist_ok=True)
    
    # Sample test data
    test_name = "JEE Main Physics - Full Length Mock"
    session_id = "20240129_143000"
    start_time = datetime(2024, 1, 29, 14, 30, 0)
    
    # Question data (question_num, category, allocated_min, actual_min, theme, notes)
    questions = [
        (1, "Thinking", 2, 2.5, "Optics", "Read problem carefully, understood concept"),
        (2, "Solving", 2, 3.2, "Mechanics", "Had to draw force diagram"),
        (3, "Applying", 2, 1.8, "Thermodynamics", "Straightforward application"),
        (4, "Verification", 2, 0.9, "Optics", "Quick cross-check"),
        (5, "Thinking", 2, 4.1, "Waves", "Complex setup, needed extra thought"),
        (6, "Solving", 2, 2.8, "Electricity", "Used circuit analysis method"),
        (7, "Applying", 2, 1.5, "Modern Physics", "Direct formula application"),
        (8, "Verification", 2, 1.2, "Mechanics", "Verified using alternate method"),
        (9, "Thinking", 2, 3.6, "Fluids", "Conceptually tricky problem"),
        (10, "Solving", 2, 2.1, "Oscillations", "Standard differential equation"),
        (11, "Applying", 2, 2.3, "Waves", "Applied superposition principle"),
        (12, "Verification", 2, 0.8, "Electricity", "Verified result"),
        (13, "Thinking", 2, 5.2, "Optics", "Lens formula, complex geometry"),
        (14, "Solving", 2, 3.8, "Mechanics", "Multi-step calculation"),
        (15, "Applying", 2, 1.9, "Thermodynamics", "Entropy calculation"),
    ]
    
    # Create CSV file
    csv_file = log_dir / f"mock_test_{session_id}_SAMPLE.csv"
    
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Write header section
        writer.writerow(["Session Info", test_name, f"Started: {start_time.isoformat()}"])
        writer.writerow([])  # Blank line
        
        # Write column headers
        writer.writerow([
            "Question #",
            "Time Category",
            "Allocated (min)",
            "Actual (min)",
            "Timestamp",
            "Theme",
            "Notes"
        ])
        
        # Write question data
        current_time = start_time
        for q_num, category, allocated, actual, theme, notes in questions:
            current_time += timedelta(minutes=actual + 1)  # Add time for actual question
            writer.writerow([
                q_num,
                category,
                allocated,
                actual,
                current_time.isoformat(),
                theme,
                notes
            ])
    
    print(f"✓ Sample CSV created: {csv_file}")
    return csv_file

def analyze_sample_csv():
    """Analyze the sample CSV and print statistics"""
    
    import sys
    try:
        import pandas as pd
        HAS_PANDAS = True
    except ImportError:
        HAS_PANDAS = False
    
    csv_file = Path("mock_test_logs/mock_test_20240129_143000_SAMPLE.csv")
    
    if HAS_PANDAS:
        # Read CSV, skipping the header rows
        df = pd.read_csv(csv_file, skiprows=2)
        
        print("\n" + "="*70)
        print("SAMPLE TEST ANALYSIS")
        print("="*70)
        
        print(f"\nTotal Questions: {len(df)}")
        print(f"Total Time: {df['Actual (min)'].sum():.2f} minutes ({int(df['Actual (min)'].sum())} min)")
        print(f"Average Time per Question: {df['Actual (min)'].mean():.2f} minutes")
        print(f"Fastest Question: {df['Actual (min)'].min():.2f} minutes (Q#{df.loc[df['Actual (min)'].idxmin(), 'Question #']:.0f})")
        print(f"Slowest Question: {df['Actual (min)'].max():.2f} minutes (Q#{df.loc[df['Actual (min)'].idxmax(), 'Question #']:.0f})")
        
        print("\n" + "-"*70)
        print("TIME BY CATEGORY")
        print("-"*70)
        category_stats = df.groupby('Time Category')['Actual (min)'].agg(['count', 'sum', 'mean'])
        category_stats.columns = ['Count', 'Total Time', 'Avg Time']
        print(category_stats.to_string())
        
        print("\n" + "-"*70)
        print("TIME BY THEME/SUBJECT")
        print("-"*70)
        theme_stats = df.groupby('Theme')['Actual (min)'].agg(['count', 'sum', 'mean'])
        theme_stats.columns = ['Count', 'Total Time', 'Avg Time']
        print(theme_stats.to_string())
        
        print("\n" + "-"*70)
        print("TIME EFFICIENCY (Actual vs Allocated)")
        print("-"*70)
        df['Difference'] = df['Actual (min)'] - df['Allocated (min)']
        df['Efficiency %'] = (df['Allocated (min)'] / df['Actual (min)']) * 100
        efficiency_df = df[['Question #', 'Time Category', 'Theme', 'Allocated (min)', 'Actual (min)', 'Difference', 'Efficiency %']]
        print(efficiency_df.to_string(index=False))
        
        print("\n" + "-"*70)
        print("PERFORMANCE INSIGHTS")
        print("-"*70)
        over_time = df[df['Actual (min)'] > df['Allocated (min)']]
        print(f"Questions over allocated time: {len(over_time)}/{len(df)}")
        print(f"Average time overage: {over_time['Difference'].mean():.2f} minutes")
        
        under_time = df[df['Actual (min)'] <= df['Allocated (min)']]
        if len(under_time) > 0:
            print(f"Questions within/under allocated time: {len(under_time)}/{len(df)}")
            print(f"Average time saved: {abs(under_time['Difference'].mean()):.2f} minutes")
        
        print("\n" + "="*70)
        
    else:
        # Simple analysis without pandas
        print("\nNote: Install pandas for enhanced analysis")
        print("pip install pandas")
        
        with open(csv_file, 'r') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            next(reader)  # Skip blank
            next(reader)  # Skip column names
            
            data = list(reader)
            if data:
                actual_times = [float(row[3]) for row in data]
                print(f"\nTotal Questions: {len(data)}")
                print(f"Total Time: {sum(actual_times):.2f} minutes")
                print(f"Average Time: {sum(actual_times)/len(data):.2f} minutes")
                print(f"Min Time: {min(actual_times):.2f} minutes")
                print(f"Max Time: {max(actual_times):.2f} minutes")

if __name__ == "__main__":
    # Create sample CSV
    create_sample_csv()
    
    # Analyze it
    analyze_sample_csv()
    
    print("\n💡 Tip: Replace 'SAMPLE' CSV with your actual test CSV for analysis!")
    print("📊 Use Excel or Google Sheets for more advanced analysis")
    print("📈 Compare multiple tests to track your progress over time\n")
