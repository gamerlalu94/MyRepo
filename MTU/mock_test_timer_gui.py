"""
Mock Test Question Timer GUI
A background-running application that allows users to track time spent on each question
during mock tests with customizable time limits for different question types.

The application opens as a popup window and logs all data to a text file for analysis.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import os
from datetime import datetime
from pathlib import Path
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import winsound


@dataclass
class TimeCategory:
    """Represents a category of time (e.g., Thinking, Solving, Applying)"""
    name: str
    allocated_minutes: int


@dataclass
class TestSession:
    """Represents a mock test session"""
    session_id: str
    test_description: str
    created_at: str
    default_time_per_question: int = 2
    max_time_per_question: int = 5
    total_duration_minutes: int = 180


@dataclass
class QuestionRecord:
    """Represents a single question record"""
    session_id: str
    question_number: int
    time_category: str
    allocated_time: int
    actual_time: int
    timestamp: str
    theme: str
    notes: str


class MockTestTimerGUI:
    """Main GUI application for mock test timer"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Mock Test Question Timer")
        self.root.geometry("900x900")
        self.root.resizable(False, False)
        
        # Data storage
        self.current_session = None
        self.time_categories = []
        self.question_records = []
        self.csv_file = None
        self.current_theme = tk.StringVar(value="Light")
        self.current_question_num = 1
        self.mini_window = None
        self.mini_window_timer_label = None
        self.floating_window_category_vars = {}
        
        # Timer
        self.timer_running = False
        self.elapsed_seconds = 0
        self.timer_thread = None
        self.session_elapsed_seconds = 0
        self.session_timer_running = False
        
        # Initialize UI
        self.setup_themes()
        self.show_initial_setup()
        
    def setup_themes(self):
        """Setup different themes for the GUI"""
        self.themes = {
            "Light": {
                "bg": "#ffffff",
                "fg": "#000000",
                "button_bg": "#e0e0e0",
                "button_fg": "#000000",
                "accent": "#0066cc"
            },
            "Dark": {
                "bg": "#2b2b2b",
                "fg": "#ffffff",
                "button_bg": "#404040",
                "button_fg": "#ffffff",
                "accent": "#66b3ff"
            },
            "Professional": {
                "bg": "#f5f5f5",
                "fg": "#333333",
                "button_bg": "#007acc",
                "button_fg": "#ffffff",
                "accent": "#005a9c"
            }
        }
        
    def apply_theme(self, theme_name):
        """Apply selected theme to the entire GUI"""
        theme = self.themes.get(theme_name, self.themes["Light"])
        self.root.configure(bg=theme["bg"])
        self.current_theme.set(theme_name)
        
    def show_initial_setup(self):
        """Show the initial setup screen - simplified with just description and theme"""
        self.clear_window()
        
        # Get current theme colors
        theme = self.themes.get(self.current_theme.get(), self.themes["Light"])
        
        # Header
        header = tk.Label(
            self.root,
            text="Mock Test Question Timer",
            font=("Arial", 24, "bold"),
            bg=theme["bg"],
            fg=theme["fg"]
        )
        header.pack(pady=20)
        
        subtitle = tk.Label(
            self.root,
            text="Configure your test and begin",
            font=("Arial", 12),
            bg=theme["bg"],
            fg=theme["fg"]
        )
        subtitle.pack(pady=(0, 30))
        
        # Option 1: Test Description
        frame1 = ttk.LabelFrame(self.root, text="Test Description", padding=15)
        frame1.pack(fill="x", padx=20, pady=10)
        
        tk.Label(frame1, text="Enter test name/description:").pack(anchor="w")
        self.test_desc_var = tk.StringVar()
        desc_entry = ttk.Entry(frame1, textvariable=self.test_desc_var, width=50)
        desc_entry.pack(fill="x", pady=5)
        
        # Option 2: Maximum Time Per Question
        frame_max_time = ttk.LabelFrame(self.root, text="Maximum Time Per Question", padding=15)
        frame_max_time.pack(fill="x", padx=20, pady=10)
        
        time_row = tk.Frame(frame_max_time)
        time_row.pack(fill="x", pady=5)
        tk.Label(time_row, text="Set maximum time (in minutes):", width=30, anchor="w").pack(side="left")
        self.max_time_var = tk.IntVar(value=5)
        max_time_spinbox = ttk.Spinbox(
            time_row, from_=1, to=60, textvariable=self.max_time_var, width=10
        )
        max_time_spinbox.pack(side="left", padx=10)
        tk.Label(time_row, text="minutes", anchor="w").pack(side="left")
        
        # Total Test Duration
        frame_total_time = ttk.LabelFrame(self.root, text="Total Test Duration", padding=15)
        frame_total_time.pack(fill="x", padx=20, pady=10)
        
        total_time_row = tk.Frame(frame_total_time)
        total_time_row.pack(fill="x", pady=5)
        tk.Label(total_time_row, text="Total test duration:", width=30, anchor="w").pack(side="left")
        
        self.total_duration_var = tk.StringVar(value="180")
        ttk.Radiobutton(
            total_time_row,
            text="3 Hours (180 min)",
            variable=self.total_duration_var,
            value="180"
        ).pack(side="left", padx=10)
        
        ttk.Radiobutton(
            total_time_row,
            text="2.5 Hours (150 min)",
            variable=self.total_duration_var,
            value="150"
        ).pack(side="left", padx=10)
        
        ttk.Radiobutton(
            total_time_row,
            text="Custom",
            variable=self.total_duration_var,
            value="custom"
        ).pack(side="left", padx=10)
        
        custom_time_row = tk.Frame(frame_total_time)
        custom_time_row.pack(fill="x", pady=5)
        tk.Label(custom_time_row, text="Custom duration (minutes):", width=30, anchor="w").pack(side="left")
        self.custom_duration_var = tk.IntVar(value=180)
        ttk.Spinbox(
            custom_time_row, from_=1, to=480, textvariable=self.custom_duration_var, width=10
        ).pack(side="left", padx=10)
        
        # Option 3: Theme Selection
        frame2 = ttk.LabelFrame(self.root, text="GUI Theme", padding=15)
        frame2.pack(fill="x", padx=20, pady=10)
        
        tk.Label(frame2, text="Choose your preferred theme:").pack(anchor="w", pady=(0, 10))
        
        theme_frame = tk.Frame(frame2)
        theme_frame.pack(fill="x")
        
        for theme_name in self.themes.keys():
            ttk.Radiobutton(
                theme_frame,
                text=theme_name,
                variable=self.current_theme,
                value=theme_name,
                command=lambda t=theme_name: self.apply_theme(t)
            ).pack(side="left", padx=10)
        
        # Start Button
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=30)
        
        ttk.Button(
            button_frame,
            text="▶ START TEST SESSION",
            command=self.start_session
        ).pack(side="left", padx=10)
        
        ttk.Button(
            button_frame,
            text="Exit",
            command=self.root.quit
        ).pack(side="left", padx=10)
    
    def start_session(self):
        """Start a new test session"""
        test_desc = self.test_desc_var.get().strip()
        
        if not test_desc:
            messagebox.showerror("Error", "Please enter a test description")
            return
        
        # Get total duration
        duration_choice = self.total_duration_var.get()
        if duration_choice == "custom":
            total_minutes = self.custom_duration_var.get()
        else:
            total_minutes = int(duration_choice)
        
        # Create session with max time and total duration
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_session = TestSession(
            session_id=session_id,
            test_description=test_desc,
            created_at=datetime.now().isoformat(),
            max_time_per_question=self.max_time_var.get(),
            total_duration_minutes=total_minutes
        )
        
        # Setup text file for logging
        self.setup_text_file()
        
        # Start session timer
        self.session_elapsed_seconds = 0
        self.session_timer_running = True
        self.start_session_timer()
        
        # Show 75 questions interface
        self.show_75_questions_interface()
    
    def setup_text_file(self):
        """Setup text file for logging question data"""
        log_dir = Path("mock_test_logs")
        log_dir.mkdir(exist_ok=True)
        
        filename = f"mock_test_{self.current_session.session_id}.txt"
        self.text_file = log_dir / filename
        
        # Write header
        with open(self.text_file, 'w') as f:
            f.write("="*80 + "\n")
            f.write("MOCK TEST QUESTION TIMER - SESSION LOG\n")
            f.write("="*80 + "\n\n")
            f.write(f"Test Description: {self.current_session.test_description}\n")
            f.write(f"Session ID: {self.current_session.session_id}\n")
            f.write(f"Started: {self.current_session.created_at}\n")
            f.write(f"Maximum Time per Question: {self.current_session.max_time_per_question} minutes\n")
            f.write(f"Total Test Duration: {self.current_session.total_duration_minutes} minutes\n")
            f.write("\n" + "="*80 + "\n")
            f.write("QUESTION DETAILS\n")
            f.write("="*80 + "\n\n")
    
    def show_75_questions_interface(self):
        """Show interface for 75 questions with category checklist"""
        self.clear_window()
        
        # Get current theme colors
        theme = self.themes.get(self.current_theme.get(), self.themes["Light"])
        self.root.configure(bg=theme["bg"])
        
        # Header
        header_frame = tk.Frame(self.root, bg=theme["accent"])
        header_frame.pack(fill="x", padx=0, pady=0)
        
        tk.Label(
            header_frame,
            text=f"Test: {self.current_session.test_description} | Questions: 1-75",
            font=("Arial", 14, "bold"),
            bg=theme["accent"],
            fg="white"
        ).pack(anchor="w", padx=15, pady=10)
        
        # Miniature status form for current question
        mini_frame = tk.Frame(self.root, bg=theme["button_bg"], relief="raised", bd=2)
        mini_frame.pack(fill="x", padx=10, pady=5)
        
        mini_left = tk.Frame(mini_frame, bg=theme["button_bg"])
        mini_left.pack(side="left", fill="x", expand=True, padx=10, pady=8)
        
        tk.Label(
            mini_left,
            text="Current Question:",
            font=("Arial", 9, "bold"),
            bg=theme["button_bg"],
            fg=theme["button_fg"]
        ).pack(side="left", padx=5)
        
        self.mini_question_label = tk.Label(
            mini_left,
            text="Q1",
            font=("Arial", 11, "bold"),
            bg="#0066cc",
            fg="white",
            padx=8,
            pady=2
        )
        self.mini_question_label.pack(side="left", padx=5)
        
        tk.Label(
            mini_left,
            text="Time:",
            font=("Arial", 9),
            bg=theme["button_bg"],
            fg=theme["button_fg"]
        ).pack(side="left", padx=5)
        
        self.mini_timer_label = tk.Label(
            mini_left,
            text="00:00",
            font=("Arial", 10, "bold"),
            bg=theme["button_bg"],
            fg=theme["button_fg"]
        )
        self.mini_timer_label.pack(side="left", padx=5)
        
        tk.Label(
            mini_left,
            text="Categories:",
            font=("Arial", 9),
            bg=theme["button_bg"],
            fg=theme["button_fg"]
        ).pack(side="left", padx=5)
        
        self.mini_categories_label = tk.Label(
            mini_left,
            text="None",
            font=("Arial", 9, "italic"),
            bg=theme["button_bg"],
            fg=theme["button_fg"]
        )
        self.mini_categories_label.pack(side="left", padx=5)
        
        tk.Label(
            mini_left,
            text="Total Time:",
            font=("Arial", 9),
            bg=theme["button_bg"],
            fg=theme["button_fg"]
        ).pack(side="left", padx=5)
        
        self.mini_total_time_label = tk.Label(
            mini_left,
            text="00:00",
            font=("Arial", 10, "bold"),
            bg=theme["button_bg"],
            fg="#FF6B6B"
        )
        self.mini_total_time_label.pack(side="left", padx=5)
        
        # Main scrollable frame for 75 questions
        canvas_frame = tk.Frame(self.root, bg=theme["bg"])
        canvas_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.questions_canvas = tk.Canvas(canvas_frame, bg=theme["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.questions_canvas.yview)
        scrollable_frame = tk.Frame(self.questions_canvas, bg=theme["bg"])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: self.questions_canvas.configure(scrollregion=self.questions_canvas.bbox("all"))
        )
        
        self.questions_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        self.questions_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Store question widgets for later access
        self.question_widgets = {}
        self.question_data = {}
        
        # Create 75 question blocks
        for q_num in range(1, 76):
            self.create_question_block(scrollable_frame, q_num, theme)
        
        self.questions_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Enable mouse scroll
        self.questions_canvas.bind_all("<MouseWheel>", lambda e: self.on_mousewheel(e))
        self.questions_canvas.bind_all("<Button-4>", lambda e: self.on_mousewheel(e))
        self.questions_canvas.bind_all("<Button-5>", lambda e: self.on_mousewheel(e))
        
        # Initialize miniature form
        self.update_miniature_form(1)
        
        # Footer buttons
        footer_frame = tk.Frame(self.root, bg=theme["bg"])
        footer_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(
            footer_frame,
            text="💾 Save All",
            command=self.save_all_questions
        ).pack(side="left", padx=5)
        
        ttk.Button(
            footer_frame,
            text="📄 View Log",
            command=self.view_log_file
        ).pack(side="left", padx=5)
        
        ttk.Button(
            footer_frame,
            text="🏁 End Session",
            command=self.end_session
        ).pack(side="left", padx=5)
        
        # Auto-launch floating window when session starts
        self.root.after(500, self.open_floating_window)
    
    def create_question_block(self, parent, question_num, theme):
        """Create a question block with category checklist and timer"""
        # Main question frame
        q_frame = tk.Frame(parent, bg=theme["bg"], bd=2, relief="solid")
        q_frame.pack(fill="x", pady=5, padx=5)
        
        # Question header with colored tag
        header = tk.Frame(q_frame, bg=theme["bg"])
        header.pack(fill="x", padx=5, pady=5)
        
        # Question number label (will change color based on selection)
        self.question_widgets[f"q{question_num}_label"] = tk.Label(
            header,
            text=f" Q{question_num} ",
            font=("Arial", 10, "bold"),
            bg=theme["accent"],
            fg="white",
            padx=8,
            pady=4
        )
        self.question_widgets[f"q{question_num}_label"].pack(side="left", padx=5)
        
        # Timer display for this question
        timer_label = tk.Label(
            header,
            text="00:00",
            font=("Arial", 10, "bold"),
            bg=theme["bg"],
            fg=theme["fg"],
            padx=8,
            pady=4
        )
        timer_label.pack(side="left", padx=5)
        
        # Category checklist
        checklist_frame = tk.Frame(q_frame, bg=theme["bg"])
        checklist_frame.pack(fill="x", padx=20, pady=5)
        
        categories = ["Thinking", "Solving", "Applying", "Verification"]
        category_colors = {"Thinking": "#FF6B6B", "Solving": "#4ECDC4", "Applying": "#45B7D1", "Verification": "#FFA07A"}
        
        self.question_data[question_num] = {
            "categories": {},
            "notes": "",
            "time_spent": 0,
            "timer_running": False,
            "elapsed_seconds": 0,
            "timer_label": timer_label,
            "beep_played": False
        }
        
        for category in categories:
            var = tk.BooleanVar(value=False)
            self.question_data[question_num]["categories"][category] = var
            
            cb = tk.Checkbutton(
                checklist_frame,
                text=category,
                variable=var,
                command=lambda qn=question_num: self.update_question_color(qn, theme)
            )
            cb.pack(side="left", padx=5)
        
        # Time spent and notes
        details_frame = tk.Frame(q_frame, bg=theme["bg"])
        details_frame.pack(fill="x", padx=20, pady=5)
        
        tk.Label(details_frame, text="Time (min):", bg=theme["bg"], fg=theme["fg"]).pack(side="left", padx=5)
        time_var = tk.StringVar(value="0")
        self.question_data[question_num]["time_var"] = time_var
        ttk.Entry(details_frame, textvariable=time_var, width=5).pack(side="left", padx=5)
        
        # Timer control buttons
        ttk.Button(
            details_frame,
            text="▶",
            command=lambda qn=question_num: self.start_question_timer(qn)
        ).pack(side="left", padx=2)
        
        ttk.Button(
            details_frame,
            text="⏸",
            command=lambda qn=question_num: self.pause_question_timer(qn)
        ).pack(side="left", padx=2)
        
        ttk.Button(
            details_frame,
            text="⏹",
            command=lambda qn=question_num: self.stop_question_timer(qn)
        ).pack(side="left", padx=2)
        
        # Notes section with templates
        notes_section = tk.Frame(q_frame, bg=theme["bg"])
        notes_section.pack(fill="x", padx=20, pady=5)
        
        tk.Label(notes_section, text="Notes:", bg=theme["bg"], fg=theme["fg"]).pack(side="left", padx=5)
        notes_var = tk.StringVar()
        self.question_data[question_num]["notes_var"] = notes_var
        notes_entry = ttk.Entry(notes_section, textvariable=notes_var, width=25)
        notes_entry.pack(side="left", padx=5)
        
        # Quick template buttons
        templates = ["Maths", "Chemistry", "Physics", "Biology", "History"]
        for template in templates:
            ttk.Button(
                notes_section,
                text=template,
                width=8,
                command=lambda t=template, nv=notes_var: nv.set(t)
            ).pack(side="left", padx=2)
    
    def update_question_color(self, question_num, theme):
        """Update question tag color based on selected categories"""
        selected_categories = [
            cat for cat, var in self.question_data[question_num]["categories"].items()
            if var.get()
        ]
        
        # Color map
        color_map = {
            "Thinking": "#FF6B6B",
            "Solving": "#4ECDC4",
            "Applying": "#45B7D1",
            "Verification": "#FFA07A"
        }
        
        if selected_categories:
            # Use first selected category color
            bg_color = color_map.get(selected_categories[0], theme["accent"])
        else:
            bg_color = theme["accent"]
        
        label = self.question_widgets.get(f"q{question_num}_label")
        if label:
            label.config(bg=bg_color)
    
    def start_question_timer(self, question_num):
        """Start timer for a specific question"""
        if not self.question_data[question_num]["timer_running"]:
            self.question_data[question_num]["timer_running"] = True
            self.question_data[question_num]["beep_played"] = False
            self.run_question_timer(question_num)
    
    def start_session_timer(self):
        """Start the overall session timer"""
        self.session_timer_running = True
        self.run_session_timer()
    
    def run_session_timer(self):
        """Run the overall session timer and check if total time is reached"""
        if self.session_timer_running and self.current_session:
            self.session_elapsed_seconds += 1
            
            # Check if total time exceeded
            if self.session_elapsed_seconds >= (self.current_session.total_duration_minutes * 60):
                self.session_timer_running = False
                self.end_test_automatically()
                return
            
            # Schedule next update
            self.root.after(1000, self.run_session_timer)
    
    def end_test_automatically(self):
        """Automatically end the test when time is up"""
        self.session_timer_running = False
        
        # Save all data
        try:
            self.save_all_questions()
        except:
            pass
        
        # Show completion message
        msg = f"📋 THE PAPER HAS ENDED\n\n" \
              f"Total Duration: {self.current_session.total_duration_minutes} minutes\n\n" \
              f"Session data saved at:\n\n{self.text_file}"
        messagebox.showinfo("Test Completed", msg)
        
        # Ask if user wants to start new session
        if messagebox.askyesno("Continue", "Would you like to start a new session?"):
            self.show_initial_setup()
        else:
            self.root.quit()
    
    def pause_question_timer(self, question_num):
        """Pause timer for a specific question"""
        self.question_data[question_num]["timer_running"] = False
    
    def stop_question_timer(self, question_num):
        """Stop timer and auto-start next question's timer"""
        self.question_data[question_num]["timer_running"] = False
        self.update_timer_display(question_num)
        
        # Close current floating window
        if self.mini_window and self.mini_window.winfo_exists():
            self.mini_window.destroy()
            self.mini_window = None
        
        # Update miniature form to show next question
        next_question = question_num + 1
        if next_question <= 75 and next_question in self.question_data:
            # Scroll to next question
            self.questions_canvas.yview_moveto((next_question - 1) / 75.0)
            # Update miniature form
            self.update_miniature_form(next_question)
            # Auto-start next question's timer
            self.start_question_timer(next_question)
            # Create new floating window for next question
            self.root.after(100, self.open_floating_window)
    
    def update_miniature_form(self, question_num):
        """Update the miniature status form for the current question"""
        self.current_question_num = question_num
        if question_num in self.question_data:
            q_data = self.question_data[question_num]
            
            # Update question label
            self.mini_question_label.config(text=f"Q{question_num}")
            
            # Update timer display to show current question's time
            elapsed = q_data["elapsed_seconds"]
            minutes = elapsed // 60
            seconds = elapsed % 60
            timer_text = f"{minutes:02d}:{seconds:02d}"
            self.mini_timer_label.config(text=timer_text)
            
            # Update categories display
            selected_cats = [
                cat for cat, var in q_data["categories"].items()
                if var.get()
            ]
            cats_text = ", ".join(selected_cats) if selected_cats else "None"
            self.mini_categories_label.config(text=cats_text)
            
            # Update total time across all questions
            self.update_total_time_display()
            
            # Update floating window if it exists
            if self.mini_window and self.mini_window.winfo_exists():
                # Update floating window timer display
                if self.mini_window_timer_label:
                    self.mini_window_timer_label.config(text=timer_text)
    
    def update_total_time_display(self):
        """Calculate and update total time spent on all questions"""
        total_seconds = 0
        for q_num in range(1, 76):
            if q_num in self.question_data:
                total_seconds += self.question_data[q_num]["elapsed_seconds"]
        
        total_minutes = total_seconds // 60
        total_secs = total_seconds % 60
        total_time_text = f"{total_minutes:02d}:{total_secs:02d}"
        self.mini_total_time_label.config(text=total_time_text)
    
    def update_floating_category(self, question_num, category, var):
        """Update category in question data when checked in floating window"""
        if question_num in self.question_data:
            if category in self.question_data[question_num]["categories"]:
                self.question_data[question_num]["categories"][category].set(var.get())
    
    def open_floating_window(self):
        """Open a floating window with timer controls"""
        # Destroy old window if it exists
        if self.mini_window and self.mini_window.winfo_exists():
            self.mini_window.destroy()
        
        self.mini_window = tk.Toplevel(self.root)
        self.mini_window.title(f"Question {self.current_question_num}")
        self.mini_window.geometry("380x280")
        self.mini_window.resizable(True, True)
        self.mini_window.attributes('-topmost', True)  # Keep on top
        
        # Get current theme
        theme = self.themes.get(self.current_theme.get(), self.themes["Light"])
        self.mini_window.configure(bg=theme["bg"])
        
        # Categories checklist
        categories_frame = tk.Frame(self.mini_window, bg=theme["bg"])
        categories_frame.pack(fill="x", padx=10, pady=5)
        
        categories = ["Thinking", "Solving", "Applying"]
        self.floating_window_category_vars = {}
        
        for category in categories:
            var = tk.BooleanVar(value=False)
            self.floating_window_category_vars[category] = var
            
            ttk.Checkbutton(
                categories_frame,
                text=category,
                variable=var,
                command=lambda qn=self.current_question_num, cat=category, v=var: self.update_floating_category(qn, cat, v)
            ).pack(side="left", padx=5)
        
        # Time info frame
        time_info_frame = tk.Frame(self.mini_window, bg=theme["bg"])
        time_info_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(
            time_info_frame,
            text="Question Time:",
            font=("Arial", 9),
            bg=theme["bg"],
            fg=theme["fg"]
        ).pack(side="left", padx=5)
        
        self.floating_q_time_label = tk.Label(
            time_info_frame,
            text="00:00",
            font=("Arial", 10, "bold"),
            bg=theme["bg"],
            fg=theme["accent"]
        )
        self.floating_q_time_label.pack(side="left", padx=5)
        
        tk.Label(
            time_info_frame,
            text="Total Time:",
            font=("Arial", 9),
            bg=theme["bg"],
            fg=theme["fg"]
        ).pack(side="left", padx=15)
        
        self.floating_total_time_label = tk.Label(
            time_info_frame,
            text="00:00",
            font=("Arial", 10, "bold"),
            bg=theme["bg"],
            fg="#FF6B6B"
        )
        self.floating_total_time_label.pack(side="left", padx=5)
        
        # Timer display (large)
        timer_frame = tk.Frame(self.mini_window, bg=theme["bg"])
        timer_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.mini_window_timer_label = tk.Label(
            timer_frame,
            text="00:00",
            font=("Arial", 40, "bold"),
            bg=theme["bg"],
            fg=theme["accent"]
        )
        self.mini_window_timer_label.pack(anchor="center", expand=True)
        
        # Control buttons
        button_frame = tk.Frame(self.mini_window, bg=theme["bg"])
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(
            button_frame,
            text="⏸ Pause",
            command=lambda: self.pause_question_timer(self.current_question_num)
        ).pack(side="left", padx=5, fill="x", expand=True)
        
        ttk.Button(
            button_frame,
            text="⏹ Stop",
            command=lambda: self.stop_question_timer(self.current_question_num)
        ).pack(side="left", padx=5, fill="x", expand=True)
        
        # Position window at top right
        self.mini_window.geometry("+1200+50")
    
    def update_floating_window_timer(self, question_num, timer_text):
        """Update the floating window timer display and time info"""
        if self.mini_window and self.mini_window.winfo_exists():
            # Update question timer
            self.mini_window_timer_label.config(text=timer_text)
            self.floating_q_time_label.config(text=timer_text)
            
            # Update total time
            total_seconds = 0
            for q_num in range(1, 76):
                if q_num in self.question_data:
                    total_seconds += self.question_data[q_num]["elapsed_seconds"]
            
            total_minutes = total_seconds // 60
            total_secs = total_seconds % 60
            total_time_text = f"{total_minutes:02d}:{total_secs:02d}"
            self.floating_total_time_label.config(text=total_time_text)
    
    def run_question_timer(self, question_num):
        """Run the timer in background"""
        if self.question_data[question_num]["timer_running"]:
            self.question_data[question_num]["elapsed_seconds"] += 1
            
            elapsed_minutes = self.question_data[question_num]["elapsed_seconds"] / 60
            max_minutes = self.current_session.max_time_per_question
            
            # Check if time exceeded and play beep
            if elapsed_minutes > max_minutes and not self.question_data[question_num]["beep_played"]:
                self.question_data[question_num]["beep_played"] = True
                try:
                    winsound.Beep(1000, 500)  # 1000 Hz for 500 ms
                except:
                    pass
            
            self.update_timer_display(question_num)
            
            # Schedule next update
            self.root.after(1000, self.run_question_timer, question_num)
    
    def update_timer_display(self, question_num):
        """Update the timer display label"""
        elapsed = self.question_data[question_num]["elapsed_seconds"]
        minutes = elapsed // 60
        seconds = elapsed % 60
        
        timer_text = f"{minutes:02d}:{seconds:02d}"
        
        # Change color if exceeded
        max_minutes = self.current_session.max_time_per_question
        elapsed_minutes = elapsed / 60
        
        if elapsed_minutes > max_minutes:
            self.question_data[question_num]["timer_label"].config(fg="#FF6B6B")  # Red for exceeded
        else:
            self.question_data[question_num]["timer_label"].config(fg="#000000")  # Black for normal
        
        self.question_data[question_num]["timer_label"].config(text=timer_text)
        
        # Update floating window if it's for the current question
        if question_num == self.current_question_num:
            self.mini_timer_label.config(text=timer_text)
            self.update_floating_window_timer(question_num, timer_text)
            # Update total time display
            self.update_total_time_display()
    
    def save_all_questions(self):
        """Save all question data to text file"""
        try:
            with open(self.text_file, 'a') as f:
                for q_num in range(1, 76):
                    if q_num in self.question_data:
                        q_data = self.question_data[q_num]
                        selected_cats = [
                            cat for cat, var in q_data["categories"].items()
                            if var.get()
                        ]
                        
                        time_spent = q_data.get("time_var", tk.StringVar()).get() or "0"
                        notes = q_data.get("notes_var", tk.StringVar()).get() or ""
                        beep_alert = "Yes" if q_data.get("beep_played", False) else "No"
                        
                        f.write(f"Question {q_num}:\n")
                        f.write(f"  Categories: {', '.join(selected_cats) if selected_cats else 'None'}\n")
                        f.write(f"  Time Spent: {time_spent} minutes\n")
                        f.write(f"  Time Exceeded Alert: {beep_alert}\n")
                        f.write(f"  Notes: {notes}\n")
                        f.write(f"  Timestamp: {datetime.now().isoformat()}\n")
                        f.write("-" * 40 + "\n\n")
                
                f.write("\n" + "="*80 + "\n")
                f.write(f"Session ended: {datetime.now().isoformat()}\n")
                f.write("="*80 + "\n")
            
            messagebox.showinfo("Success", f"All data saved to:\n\n{self.text_file.parent}\n\nFile: {self.text_file.name}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {str(e)}")
    
    def view_log_file(self):
        """Open the log file in default application"""
        if self.text_file and self.text_file.exists():
            os.startfile(self.text_file)
        else:
            messagebox.showerror("Error", "Log file not found")
    
    def end_session(self):
        """End the current session"""
        self.session_timer_running = False  # Stop the session timer
        if messagebox.askyesno("Confirm", "Save all data and end session?"):
            self.save_all_questions()
            # Show directory path
            msg = f"Session data saved at:\n\n{self.text_file}\n\nWould you like to start a new session?"
            if messagebox.askyesno("Session Ended", msg):
                self.show_initial_setup()
            else:
                self.root.quit()
    
    def on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        if event.num == 5 or event.delta < 0:
            self.questions_canvas.yview_scroll(3, "units")
        elif event.num == 4 or event.delta > 0:
            self.questions_canvas.yview_scroll(-3, "units")
    
    def clear_window(self):
        """Clear all widgets from the window"""
        for widget in self.root.winfo_children():
            widget.destroy()


def main():
    """Main entry point"""
    root = tk.Tk()
    app = MockTestTimerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
