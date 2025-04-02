import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import pandas as pd
from datetime import datetime, timedelta
import os
import threading
import pystray
from PIL import Image, ImageDraw
import tempfile

class TimeTracker:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Time Tracker")
        self.root.geometry("250x400")
        
        # Initialize variables
        self.start_time = None
        self.end_time = None
        self.pause_start = None
        self.total_pause_time = timedelta()
        self.is_running = False
        self.is_paused = False
        self.is_minimized = False
        
        # Setup tray icon
        self.setup_tray()
        
        # Create GUI elements
        self.setup_gui()
        
        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
    def setup_tray(self):
        """Set up the system tray icon and menu"""
        # Create initial tray icon image (gray)
        self.icon_images = {
            'idle': self.create_colored_icon('gray'),
            'running': self.create_colored_icon('green'),
            'paused': self.create_colored_icon('yellow')
        }
        
        # Create the tray icon
        self.tray_icon = pystray.Icon("timetracker")
        self.tray_icon.icon = self.icon_images['idle']
        
        # Set up menu items
        self.tray_icon.menu = pystray.Menu(
            pystray.MenuItem("Show", self.show_window),
            pystray.MenuItem("Exit", self.exit_app)
        )
        
        # Set click action
        self.tray_icon.on_click = self.on_tray_click
        
        # Start tray icon in a separate thread
        threading.Thread(target=self.tray_icon.run, daemon=True).start()
        
    def create_colored_icon(self, color):
        """Create a colored circle icon"""
        image = Image.new('RGB', (64, 64), (255, 255, 255))
        dc = ImageDraw.Draw(image)
        
        # Pick the color
        if color == 'green':
            fill = (0, 180, 0)
        elif color == 'yellow':
            fill = (255, 204, 0)
        else:  # default gray
            fill = (128, 128, 128)
            
        # Draw a filled circle
        dc.ellipse((4, 4, 60, 60), fill=fill)
        
        return image
    
    def update_tray_icon(self):
        """Update the tray icon based on timer state"""
        if not self.is_running:
            self.tray_icon.icon = self.icon_images['idle']
        elif self.is_paused:
            self.tray_icon.icon = self.icon_images['paused']
        else:
            self.tray_icon.icon = self.icon_images['running']
    
    def on_tray_click(self, icon, button, time):
        """Handle tray icon clicks"""
        if button == 1:  # Left click
            self.show_window()
    
    def show_window(self):
        """Show the main window"""
        self.is_minimized = False
        self.root.deiconify()
        self.root.focus_force()
    
    def minimize_to_tray(self):
        """Minimize the app to system tray"""
        self.is_minimized = True
        self.root.withdraw()
    
    def exit_app(self):
        """Exit the application"""
        if self.is_running:
            # Ask for confirmation if timer is running
            if tk.messagebox.askyesno("Confirm Exit", "Timer is still running. Are you sure you want to exit?"):
                self.tray_icon.stop()
                self.root.destroy()
        else:
            self.tray_icon.stop()
            self.root.destroy()
    
    def on_close(self):
        """Handle window close event"""
        if self.is_running:
            # Ask for confirmation if timer is running
            if tk.messagebox.askyesno("Confirm", "Timer is still running. Do you want to minimize to tray instead of closing?"):
                self.minimize_to_tray()
            else:
                self.exit_app()
        else:
            self.exit_app()
    
    def format_time(self, td):
        """Convert timedelta to HH:MM:SS format"""
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours}h{minutes:02d}m{seconds:02d}s"
        elif minutes > 0:
            return f"{minutes}m{seconds:02d}s"
        else:
            return f"{seconds}s"
        
    def setup_gui(self):
        # Style configuration
        style = ttk.Style()
        style.configure("Large.TButton", padding=10, font=('Helvetica', 12))
        
        # Time display label
        self.time_label = ttk.Label(
            self.root,
            text="0s",
            font=('Helvetica', 24)
        )
        self.time_label.pack(pady=(20,0))
        
        # Pause time display label
        self.pause_label = ttk.Label(
            self.root,
            text="Pause: 0s",
            font=('Helvetica', 10)
        )
        self.pause_label.pack(pady=(0,20))
        
        # Buttons
        self.start_button = ttk.Button(
            self.root,
            text="Start",
            command=self.start_timer,
            style="Large.TButton"
        )
        self.start_button.pack(pady=10)
        
        self.pause_button = ttk.Button(
            self.root,
            text="Pause",
            command=self.pause_timer,
            style="Large.TButton",
            state="disabled"
        )
        self.pause_button.pack(pady=10)
        
        self.stop_button = ttk.Button(
            self.root,
            text="Stop",
            command=self.stop_timer,
            style="Large.TButton",
            state="disabled"
        )
        self.stop_button.pack(pady=10)
        
        # Minimize button
        self.minimize_button = ttk.Button(
            self.root,
            text="Minimize to Tray",
            command=self.minimize_to_tray
        )
        self.minimize_button.pack(pady=10)
        
        # Status label
        self.status_label = ttk.Label(
            self.root,
            text="Ready to start",
            font=('Helvetica', 10)
        )
        self.status_label.pack(pady=10)
        
    def update_time_display(self):
        if self.is_running:
            current_time = datetime.now()
            
            # Calculate pause time
            if self.is_paused:
                current_pause = current_time - self.pause_start
                total_pause = self.total_pause_time + current_pause
            else:
                total_pause = self.total_pause_time
            
            # Calculate elapsed time (total - pauses)
            elapsed_time = current_time - self.start_time - total_pause
            
            # Update displays with formatted time
            self.time_label.config(text=self.format_time(elapsed_time))
            self.pause_label.config(text=f"Pause: {self.format_time(total_pause)}")
            
            # Continue updating regardless of pause state
            self.root.after(1000, self.update_time_display)
    
    def start_timer(self):
        if not self.is_running:
            self.start_time = datetime.now()
            self.is_running = True
            self.total_pause_time = timedelta()
            self.start_button.config(state="disabled")
            self.pause_button.config(state="normal")
            self.stop_button.config(state="normal")
            self.status_label.config(text="Timer running")
            self.pause_label.config(text="Pause: 0s")
            self.update_time_display()
            self.update_tray_icon()
    
    def pause_timer(self):
        if self.is_running and not self.is_paused:
            self.pause_start = datetime.now()
            self.is_paused = True
            self.pause_button.config(text="Resume")
            self.status_label.config(text="Timer paused")
            self.update_tray_icon()
        elif self.is_running and self.is_paused:
            pause_end = datetime.now()
            self.total_pause_time += pause_end - self.pause_start
            self.is_paused = False
            self.pause_button.config(text="Pause")
            self.status_label.config(text="Timer running")
            self.update_time_display()
            self.update_tray_icon()
    
    def stop_timer(self):
        if self.is_running:
            self.end_time = datetime.now()
            if self.is_paused:
                # If stopped while paused, add the current pause time
                self.total_pause_time += self.end_time - self.pause_start
            
            # Prompt for comment
            comment = self.get_comment()
            
            # Save data with comment
            self.save_to_excel(comment)
            self.reset_timer()
    
    def get_comment(self):
        """Show dialog to get comment from user"""
        return simpledialog.askstring("Comment", "Enter a comment about this work session:", parent=self.root)
    
    def reset_timer(self):
        self.is_running = False
        self.is_paused = False
        self.start_time = None
        self.end_time = None
        self.total_pause_time = timedelta()
        self.time_label.config(text="0s")
        self.pause_label.config(text="Pause: 0s")
        self.start_button.config(state="normal")
        self.pause_button.config(state="disabled", text="Pause")
        self.stop_button.config(state="disabled")
        self.status_label.config(text="Ready to start")
        self.update_tray_icon()
    
    def get_total_seconds(self, td):
        return int(td.total_seconds())
    
    def format_time_hms(self, td):
        """Convert timedelta to standard HH:MM:SS format for Excel storage"""
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def save_to_excel(self, comment=""):
        filename = "time_tracking.xlsx"
        today = datetime.now()
        
        # Format for the sheet name: YYYY-MM (year and month only)
        month_sheet = today.strftime("%Y-%m")
        
        # Full date for the data record
        date_string = today.strftime("%Y-%m-%d")
        
        # Calculate total work time
        total_time = self.end_time - self.start_time
        work_time = total_time - self.total_pause_time
        
        # Create new DataFrame with current session data
        new_data = {
            'Start Time': [self.start_time.strftime("%H:%M:%S")],
            'End Time': [self.end_time.strftime("%H:%M:%S")],
            'Date': [date_string],
            'Pause Time': [self.format_time_hms(self.total_pause_time)],
            'Total Work Time': [self.format_time_hms(work_time)],
            'Comment': [comment if comment else ""]
        }
        new_df = pd.DataFrame(new_data)
        
        try:
            # Try to read existing Excel file
            with pd.ExcelWriter(filename, engine='openpyxl', mode='a') as writer:
                new_df.to_excel(writer, sheet_name=month_sheet, index=False)
        except FileNotFoundError:
            # If file doesn't exist, create new one
            new_df.to_excel(filename, sheet_name=month_sheet, index=False)
        except ValueError:
            # If sheet already exists, read it and append new data
            existing_df = pd.read_excel(filename, sheet_name=month_sheet)
            updated_df = pd.concat([existing_df, new_df], ignore_index=True)
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                updated_df.to_excel(writer, sheet_name=month_sheet, index=False)
        
        self.status_label.config(text=f"Data saved to Excel in sheet {month_sheet}!")
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = TimeTracker()
    app.run() 