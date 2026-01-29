# Mock Test Question Timer - Complete Documentation

## Overview
The **Mock Test Question Timer** is a background-running GUI application designed to help students track time spent on each question during mock tests. It provides a popup interface for managing time limits across different question types and automatically logs all data to CSV files for analysis and review.

---

## Features

### 1. **Three Main Configuration Options**

#### Option 1: Test Description
- Enter a descriptive name for your mock test
- Examples: "JEE Main 2024 - Physics Section", "NEET Biology Mock"
- This name appears in all CSV logs for easy identification

#### Option 2: Time Limits by Category
Define customizable time allocations for different question types:
- **Thinking**: Time for understanding the problem (default: 2 min)
- **Solving**: Time for mathematical/logical work (default: 2 min)
- **Applying**: Time for applying concepts (default: 2 min)
- **Verification**: Time for checking answers (default: 2 min)

Each category time can be set from 1 to 30 minutes. These become the benchmark times for your test session.

#### Option 3: GUI Theme Selection
Choose from three professional themes:
- **Light**: Clean white background with dark text (default)
- **Dark**: Dark background for reduced eye strain
- **Professional**: Blue-tinted professional appearance

---

## System Architecture

### Components

```
Mock Test Timer System
├── GUI Interface (Tkinter-based)
│   ├── Initial Setup Screen
│   ├── Timer Interface
│   └── Theme Manager
├── Background Timer (Threading)
├── CSV Logging System
└── Data Management
```

### Data Flow

```
User Input
    ↓
Test Session Created
    ↓
CSV File Initialized
    ↓
Question Timer Started
    ↓
Question Data Recorded
    ↓
CSV Logged
    ↓
Statistics Updated
```

---

## How to Use

### Starting the Application

```bash
python mock_test_timer_gui.py
```

### Initial Setup (First Screen)

1. **Enter Test Description**
   - Type your test name (e.g., "Mathematics Mock Test")

2. **Set Time Limits**
   - Adjust the spinbox values for each category
   - Values must be between 1-30 minutes

3. **Select Theme**
   - Choose your preferred visual theme
   - Preview changes in real-time

4. **Click "Start Test Session"**
   - Application initializes CSV log file
   - Transitions to timer interface

### During Test Session

#### Timer Interface Features:

**Question Details Section:**
- **Question Number**: Auto-increments after each save
- **Time Category**: Select which type this question is (Thinking/Solving/Applying/Verification)
- **Question Theme**: Subject area (Algebra, Geometry, etc.) - can be customized
- **Notes**: Add any observations or formulas used

**Timer Controls:**
- **▶ Start Timer**: Begin timing the question
- **⏸ Pause Timer**: Temporarily pause without stopping
- **⏹ Stop & Save**: Record the question time and save to CSV
- **🔄 Reset Timer**: Clear timer without saving

**Session Statistics:**
- Live count of recorded questions
- Total time spent (in MM:SS format)

### Saving Question Data

When you click **"Stop & Save"**:
1. Timer is recorded in minutes
2. Data is appended to CSV file
3. Question number auto-increments
4. Timer resets for next question
5. Notification confirms save

### Ending Session

Click **"End Session"** to:
- Stop the current timer
- Save all remaining data
- Return to initial setup screen
- All data remains in CSV for future reference

---

## CSV File Format

### Location
```
mock_test_logs/mock_test_YYYYMMDD_HHMMSS.csv
```

### Structure

```csv
Session Info,Test Name,Started: 2024-01-29T14:30:00
[blank line]
Question #,Time Category,Allocated (min),Actual (min),Timestamp,Theme,Notes
1,Thinking,2,2.5,2024-01-29T14:31:00,Algebra,"Used quadratic formula"
2,Solving,2,3.2,2024-01-29T14:35:30,Geometry,"Had to draw diagram"
3,Applying,2,1.8,2024-01-29T14:39:00,Trigonometry,""
```

### Column Descriptions

| Column | Purpose | Example |
|--------|---------|---------|
| Question # | Question identifier | 1, 2, 3... |
| Time Category | Question type | Thinking, Solving, etc. |
| Allocated (min) | Benchmark time for category | 2 |
| Actual (min) | Time spent (decimal) | 2.5 |
| Timestamp | When saved | ISO 8601 format |
| Theme | Subject/topic | Algebra, Geometry |
| Notes | User observations | "Used formula X" |

---

## Data Analysis After Test

### View Log File
- Click **"View Log File"** to open CSV in default application
- Use Excel/Google Sheets for analysis

### Analysis Ideas

1. **Time Efficiency**
   - Compare actual vs. allocated time
   - Identify weak areas (higher time)
   - Find strengths (lower time)

2. **Pattern Recognition**
   - Which themes take longer?
   - Are certain categories consistently over time?

3. **Performance Metrics**
   - Total test time
   - Questions attempted
   - Time per question average

### Sample Analysis Formula (Excel)
```
=AVERAGEIFS(D:D, B:B, "Thinking")
// Gives average time for "Thinking" category

=COUNTIF(F:F, "Algebra")
// Counts all Algebra questions

=SUM(D:D)
// Total time across all questions
```

---

## Technical Details

### Dependencies
```python
tkinter          # GUI framework (built-in)
threading        # Background timer
csv              # CSV logging
datetime         # Timestamps
pathlib          # File operations
json             # Configuration (future)
dataclasses      # Data models
```

### Classes

#### `MockTestTimerGUI`
Main application class handling:
- UI rendering
- Event management
- Data storage
- File operations

#### `TestSession`
Dataclass storing:
- Session ID (timestamp-based)
- Test description
- Creation timestamp

#### `QuestionRecord`
Dataclass storing:
- Question number
- Category and time
- Theme and notes
- Timestamp

#### `TimeCategory`
Dataclass storing:
- Category name
- Allocated time

### Threading Model
- Main thread: UI management
- Timer thread: Background time tracking
- Non-blocking: Application remains responsive

---

## File Structure

```
D:\GitHub\MyRepo\
├── mock_test_timer_gui.py          # Main application
├── mock_test_timer_documentation.md # This file
├── mock_test_logs/                 # Auto-created folder
│   ├── mock_test_20240129_143000.csv
│   ├── mock_test_20240129_150000.csv
│   └── ...
└── demogui.ipynb                   # Jupyter notebook demo
```

---

## Advanced Features

### Customization

#### Adding New Categories
Edit the `categories` list in `show_initial_setup()`:
```python
categories = ["Thinking", "Solving", "Applying", "Verification", "Review"]
```

#### Adding Themes
Expand `self.themes` dictionary with new color schemes:
```python
"Ocean": {
    "bg": "#1a3a52",
    "fg": "#e0f2ff",
    "button_bg": "#2d5a7b",
    "button_fg": "#e0f2ff",
    "accent": "#4da6ff"
}
```

#### Custom Question Types
Modify the Combobox values in `show_timer_interface()`:
```python
values=["Algebra", "Geometry", "Chemistry", "Physics", "Biology"]
```

---

## Troubleshooting

### Issue: Timer not starting
**Solution**: Ensure threading is working. Check that no other process is blocking the application.

### Issue: CSV file not found
**Solution**: Look for `mock_test_logs/` folder in the directory where you run the script. Create it manually if missing.

### Issue: Theme not applying
**Solution**: Select theme again or restart the application.

### Issue: Data not saving to CSV
**Solution**: Ensure you have write permissions in the `mock_test_logs/` directory. Check file path.

---

## Best Practices

1. **Before Test**
   - Set realistic time limits based on your pace
   - Choose a comfortable theme
   - Provide clear test description

2. **During Test**
   - Pause timer if reading question multiple times
   - Use notes to track strategy changes
   - Save promptly after each question

3. **After Test**
   - Export CSV to spreadsheet software
   - Analyze patterns
   - Adjust time limits for next session

---

## Future Enhancements

- [ ] Real-time analytics dashboard
- [ ] Multi-session comparison
- [ ] Graphical performance charts
- [ ] Export to PDF reports
- [ ] Cloud sync capability
- [ ] Mobile companion app
- [ ] Difficulty rating for questions
- [ ] Custom alarms/notifications

---

## Version Information

- **Version**: 1.0
- **Release Date**: January 2024
- **Python**: 3.8+
- **OS**: Windows, macOS, Linux

---

## Support & Feedback

For issues, feature requests, or contributions, please refer to your project repository.

---

## License

This application is provided as-is for educational purposes.

---

**Happy studying! 📚⏱️**
