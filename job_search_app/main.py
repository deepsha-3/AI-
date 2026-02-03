import tkinter as tk
from tkinter import messagebox, ttk
from auth import AuthenticationManager, AnimatedAuthWindow
from job_search import JobSearchManager
import pandas as pd

class MainApplication:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Job Matching Assistant")
        self.auth_manager = AuthenticationManager()
        self.job_manager = JobSearchManager()
        self.current_user = None
        
        # Center the window
        self.center_window(1000, 600)
        
        self.show_auth_window()
        
    def center_window(self, width, height):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
    def show_auth_window(self):
        # Clear any existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()
            
        # Create animated auth window
        self.auth_window = AnimatedAuthWindow(
            self.root, 
            self.auth_manager, 
            self.on_login_success
        )
        
    def on_login_success(self, email, user_data):
        self.current_user = email
        self.user_data = user_data
        self.show_main_app()
        
    def show_main_app(self):
        # Clear any existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()
            
        # Create main application interface
        self.setup_main_ui()
        
    def setup_main_ui(self):
        # Main container
        main_container = tk.Frame(self.root, bg="#2c3e50")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = tk.Frame(main_container, bg="#3498db", height=60)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="Job Matching Assistant", 
                font=("Arial", 20, "bold"), bg="#3498db", fg="white").pack(side=tk.LEFT, padx=20)
        
        # User info on right
        user_info = tk.Frame(header_frame, bg="#3498db")
        user_info.pack(side=tk.RIGHT, padx=20)
        
        tk.Label(user_info, text=f"Welcome, {self.user_data['username']}", 
                font=("Arial", 12), bg="#3498db", fg="white").pack(side=tk.LEFT, padx=5)
        
        tk.Button(user_info, text="Logout", command=self.logout,
                 bg="#e74c3c", fg="white", bd=0, padx=10, cursor="hand2").pack(side=tk.LEFT, padx=5)
        
        # Main content area
        content_frame = tk.Frame(main_container, bg="#ecf0f1")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Left panel - User profile and search
        left_panel = tk.Frame(content_frame, bg="white", relief=tk.RAISED, bd=1)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10), expand=True)
        
        # Right panel - Search results
        right_panel = tk.Frame(content_frame, bg="white", relief=tk.RAISED, bd=1)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Configure grid weights for panels
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=1)
        
        # Create left panel content
        self.create_profile_section(left_panel)
        self.create_search_section(left_panel)
        
        # Create right panel content
        self.create_results_section(right_panel)
        
    def create_profile_section(self, parent):
        profile_frame = tk.LabelFrame(parent, text="Your Profile", font=("Arial", 12, "bold"),
                                     bg="white", fg="#2c3e50", padx=10, pady=10)
        profile_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        # Display user info
        tk.Label(profile_frame, text=f"Email: {self.current_user}", 
                font=("Arial", 10), bg="white", fg="#34495e", anchor="w").pack(fill=tk.X, pady=2)
        tk.Label(profile_frame, text=f"Location: {self.user_data.get('location', 'Not set')}", 
                font=("Arial", 10), bg="white", fg="#34495e", anchor="w").pack(fill=tk.X, pady=2)
        
        # Skills display
        skills_text = self.user_data.get('skills', [])
        skills_str = ', '.join(skills_text) if isinstance(skills_text, list) else skills_text
        tk.Label(profile_frame, text=f"Skills: {skills_str}", 
                font=("Arial", 10), bg="white", fg="#34495e", anchor="w", wraplength=300).pack(fill=tk.X, pady=2)
        
        # Update profile button
        tk.Button(profile_frame, text="Update Profile", command=self.update_profile,
                 bg="#3498db", fg="white", bd=0, padx=10, cursor="hand2").pack(pady=(10, 0))
    
    def create_search_section(self, parent):
        search_frame = tk.LabelFrame(parent, text="Job Search", font=("Arial", 12, "bold"),
                                    bg="white", fg="#2c3e50", padx=10, pady=10)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Algorithm selection
        tk.Label(search_frame, text="Search Algorithm:", 
                font=("Arial", 10, "bold"), bg="white", fg="#34495e").pack(anchor="w", pady=(0, 5))
        
        self.algorithm_var = tk.StringVar(value="BFS")
        algorithm_frame = tk.Frame(search_frame, bg="white")
        algorithm_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Radiobutton(algorithm_frame, text="BFS (Breadth-First Search)", 
                      variable=self.algorithm_var, value="BFS", bg="white").pack(side=tk.LEFT, padx=(0, 20))
        tk.Radiobutton(algorithm_frame, text="DFS (Depth-First Search)", 
                      variable=self.algorithm_var, value="DFS", bg="white").pack(side=tk.LEFT)
        
        # Search button
        search_btn = tk.Button(search_frame, text="Search Matching Jobs", 
                              command=self.search_jobs, bg="#2ecc71", fg="white",
                              font=("Arial", 11, "bold"), bd=0, padx=20, pady=8, cursor="hand2")
        search_btn.pack(pady=10)
        
        # Generate dummy data button
        dummy_btn = tk.Button(search_frame, text="Generate Dummy Jobs", 
                             command=self.generate_dummy_jobs, bg="#e67e22", fg="white",
                             bd=0, padx=20, pady=5, cursor="hand2")
        dummy_btn.pack(pady=(5, 0))
        
        # View all jobs button
        view_all_btn = tk.Button(search_frame, text="View All Jobs", 
                                command=self.view_all_jobs, bg="#9b59b6", fg="white",
                                bd=0, padx=20, pady=5, cursor="hand2")
        view_all_btn.pack(pady=5)
    
    def create_results_section(self, parent):
        # Create frame for treeview and scrollbar
        results_frame = tk.Frame(parent, bg="white")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create treeview
        columns = ("Job Title", "Required Skills", "Location", "Salary", "Company")
        self.tree = ttk.Treeview(results_frame, columns=columns, show="headings", selectmode="browse")
        
        # Define headings
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        
        # Adjust column widths
        self.tree.column("Job Title", width=150)
        self.tree.column("Required Skills", width=200)
        self.tree.column("Location", width=100)
        self.tree.column("Salary", width=100)
        self.tree.column("Company", width=150)
        
        # Create scrollbar
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview and scrollbar
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Results info label
        self.results_label = tk.Label(parent, text="No search performed yet", 
                                     font=("Arial", 10), bg="white", fg="#7f8c8d")
        self.results_label.pack(pady=(0, 10))
    
    def search_jobs(self):
        if not self.user_data.get('skills') or not self.user_data.get('location'):
            messagebox.showwarning("Profile Incomplete", 
                                 "Please update your profile with skills and location before searching.")
            return
        
        skills = self.user_data['skills']
        if isinstance(skills, str):
            skills = [skill.strip() for skill in skills.split(',')]
        
        location = self.user_data['location']
        algorithm = self.algorithm_var.get()
        
        # Clear previous results
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Search for jobs
        if algorithm == "BFS":
            results = self.job_manager.search_jobs_bfs(skills, location)
            algorithm_name = "BFS (Breadth-First Search)"
        else:
            results = self.job_manager.search_jobs_dfs(skills, location)
            algorithm_name = "DFS (Depth-First Search)"
        
        # Display results
        self.display_results(results, algorithm_name)
    
    def display_results(self, results, algorithm_name):
        if not results:
            self.results_label.config(text=f"No matching jobs found using {algorithm_name}")
            return
        
        # Add results to treeview
        for job in results:
            self.tree.insert("", "end", values=(
                job['Job Title'],
                job['Required Skills'],
                job['Location'],
                job['Salary'],
                job['Company']
            ))
        
        self.results_label.config(
            text=f"Found {len(results)} matching jobs using {algorithm_name}"
        )
    
    def update_profile(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Update Profile")
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - dialog.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Content
        main_frame = tk.Frame(dialog, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(main_frame, text="Update Your Profile", 
                font=("Arial", 16, "bold")).pack(pady=(0, 20))
        
        # Skills input
        tk.Label(main_frame, text="Your Skills (comma-separated):", 
                font=("Arial", 10)).pack(anchor="w", pady=(5, 0))
        
        skills_var = tk.StringVar(value=', '.join(self.user_data.get('skills', [])))
        skills_entry = tk.Entry(main_frame, textvariable=skills_var, width=40)
        skills_entry.pack(pady=(0, 10), fill=tk.X)
        
        # Location input
        tk.Label(main_frame, text="Your Location:", 
                font=("Arial", 10)).pack(anchor="w", pady=(5, 0))
        
        location_var = tk.StringVar(value=self.user_data.get('location', ''))
        location_entry = tk.Entry(main_frame, textvariable=location_var, width=40)
        location_entry.pack(pady=(0, 20), fill=tk.X)
        
        def save_profile():
            new_skills = [skill.strip() for skill in skills_var.get().split(',')]
            new_location = location_var.get().strip()
            
            if not new_skills or not new_location:
                messagebox.showerror("Error", "Please fill in all fields")
                return
            
            # Update user data
            self.user_data['skills'] = new_skills
            self.user_data['location'] = new_location
            
            # Update in database
            success, message = self.auth_manager.update_user_profile(
                self.current_user, new_skills, new_location
            )
            
            if success:
                messagebox.showinfo("Success", "Profile updated successfully!")
                dialog.destroy()
                # Refresh the main interface
                self.show_main_app()
            else:
                messagebox.showerror("Error", message)
        
        # Buttons
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Button(button_frame, text="Save", command=save_profile,
                 bg="#3498db", fg="white", bd=0, padx=20).pack(side=tk.LEFT, padx=(0, 10))
        tk.Button(button_frame, text="Cancel", command=dialog.destroy,
                 bg="#95a5a6", fg="white", bd=0, padx=20).pack(side=tk.LEFT)
    
    def generate_dummy_jobs(self):
        count = self.job_manager.generate_dummy_data()
        messagebox.showinfo("Success", f"Generated {count} dummy job entries in jobs.csv")
    
    def view_all_jobs(self):
        all_jobs = self.job_manager.get_all_jobs()
        
        # Clear previous results
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Display all jobs
        self.display_results(all_jobs, "All Available Jobs")
    
    def logout(self):
        self.current_user = None
        self.user_data = None
        self.show_auth_window()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = MainApplication()
    app.run()