import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from auth import AuthenticationManager, AnimatedAuthWindow
from job_search import JobSearchManager
import pandas as pd
import os
from datetime import datetime

class MainApplication:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Job Matching Assistant")
        self.auth_manager = AuthenticationManager()
        self.job_manager = JobSearchManager()
        self.current_user = None
        self.current_results = []
        self.current_algorithm = ""
        
        # Center the window
        self.center_window(1200, 700)
        
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
        main_container = tk.Frame(self.root, bg="#0a1929")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = tk.Frame(main_container, bg="#1e3a5f", height=60)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="🇳🇵 Job Matching Assistant - Nepal", 
                font=("Arial", 20, "bold"), bg="#1e3a5f", fg="white").pack(side=tk.LEFT, padx=20)
        
        # User info on right
        user_info = tk.Frame(header_frame, bg="#1e3a5f")
        user_info.pack(side=tk.RIGHT, padx=20)
        
        tk.Label(user_info, text=f"Welcome, {self.user_data['username']}", 
                font=("Arial", 12), bg="#1e3a5f", fg="white").pack(side=tk.LEFT, padx=5)
        
        tk.Button(user_info, text="Logout", command=self.logout,
                 bg="#c44536", fg="white", bd=0, padx=10, cursor="hand2").pack(side=tk.LEFT, padx=5)
        
        # Main content area
        content_frame = tk.Frame(main_container, bg="#e8edf5")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Left panel - User profile and search
        left_panel = tk.Frame(content_frame, bg="white", relief=tk.RAISED, bd=1)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10), expand=True)
        
        # Right panel - Search results and path visualization
        right_panel = tk.Frame(content_frame, bg="white", relief=tk.RAISED, bd=1)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Create left panel content
        self.create_profile_section(left_panel)
        self.create_search_section(left_panel)
        
        # Create right panel content
        self.create_results_section(right_panel)
        
    def create_profile_section(self, parent):
        profile_frame = tk.LabelFrame(parent, text="Your Profile", font=("Arial", 12, "bold"),
                                     bg="white", fg="#1e3a5f", padx=10, pady=10)
        profile_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        # Display user info
        tk.Label(profile_frame, text=f"Email: {self.current_user}", 
                font=("Arial", 10), bg="white", fg="#1e3a5f", anchor="w").pack(fill=tk.X, pady=2)
        tk.Label(profile_frame, text=f"Location: {self.user_data.get('location', 'Not set')}", 
                font=("Arial", 10), bg="white", fg="#1e3a5f", anchor="w").pack(fill=tk.X, pady=2)
        
        # Skills display
        skills_text = self.user_data.get('skills', [])
        skills_str = ', '.join(skills_text) if isinstance(skills_text, list) else skills_text
        tk.Label(profile_frame, text=f"Skills: {skills_str}", 
                font=("Arial", 10), bg="white", fg="#1e3a5f", anchor="w", wraplength=300).pack(fill=tk.X, pady=2)
        
        # Update profile button
        tk.Button(profile_frame, text="Update Profile", command=self.update_profile,
                 bg="#3d5a80", fg="white", bd=0, padx=10, cursor="hand2").pack(pady=(10, 0))
    
    def create_search_section(self, parent):
        search_frame = tk.LabelFrame(parent, text="Job Search", font=("Arial", 12, "bold"),
                                    bg="white", fg="#1e3a5f", padx=10, pady=10)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Algorithm selection
        tk.Label(search_frame, text="Search Algorithm:", 
                font=("Arial", 10, "bold"), bg="white", fg="#1e3a5f").pack(anchor="w", pady=(0, 5))
        
        self.algorithm_var = tk.StringVar(value="BFS")
        algorithm_frame = tk.Frame(search_frame, bg="white")
        algorithm_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Radiobutton(algorithm_frame, text="BFS (Breadth-First Search)", 
                      variable=self.algorithm_var, value="BFS", bg="white", fg="#1e3a5f").pack(side=tk.LEFT, padx=(0, 20))
        tk.Radiobutton(algorithm_frame, text="DFS (Depth-First Search)", 
                      variable=self.algorithm_var, value="DFS", bg="white", fg="#1e3a5f").pack(side=tk.LEFT)
        
        # Search button
        search_btn = tk.Button(search_frame, text="🔍 Search Matching Jobs", 
                              command=self.search_jobs, bg="#2d4a70", fg="white",
                              font=("Arial", 11, "bold"), bd=0, padx=20, pady=8, cursor="hand2")
        search_btn.pack(pady=10)
        
        # Generate Nepal jobs button
        nepal_btn = tk.Button(search_frame, text="🇳🇵 Generate Nepal Jobs", 
                             command=self.generate_nepal_jobs, bg="#1e3a5f", fg="white",
                             bd=0, padx=20, pady=5, cursor="hand2")
        nepal_btn.pack(pady=(5, 0))
        
        # View all jobs button
        view_all_btn = tk.Button(search_frame, text="📋 View All Jobs", 
                                command=self.view_all_jobs, bg="#3d5a80", fg="white",
                                bd=0, padx=20, pady=5, cursor="hand2")
        view_all_btn.pack(pady=5)
        
        # Download CSV button
        download_btn = tk.Button(search_frame, text="📥 Download as CSV", 
                                command=self.download_results, bg="#27ae60", fg="white",
                                bd=0, padx=20, pady=5, cursor="hand2")
        download_btn.pack(pady=5)
        
        # Show path button
        path_btn = tk.Button(search_frame, text="🛤️ Show Search Path", 
                            command=self.show_search_path, bg="#8e44ad", fg="white",
                            bd=0, padx=20, pady=5, cursor="hand2")
        path_btn.pack(pady=5)
    
    def create_results_section(self, parent):
        # Create notebook for tabs
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tab 1: Job Results
        results_tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(results_tab, text="Job Results")
        
        # Create treeview in results tab
        columns = ("Job Title", "Required Skills", "Location", "Salary", "Company", "Address")
        self.tree = ttk.Treeview(results_tab, columns=columns, show="headings", selectmode="browse")
        
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
        self.tree.column("Address", width=150)
        
        # Create scrollbar
        scrollbar = ttk.Scrollbar(results_tab, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview and scrollbar
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Tab 2: Search Path Visualization
        path_tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(path_tab, text="Search Path")
        
        # Create text widget for path visualization
        self.path_text = tk.Text(path_tab, wrap=tk.WORD, bg="white", fg="#1e3a5f", 
                                font=("Courier", 10))
        path_scrollbar = tk.Scrollbar(path_tab, command=self.path_text.yview)
        self.path_text.configure(yscrollcommand=path_scrollbar.set)
        
        self.path_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        path_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Results info label
        self.results_label = tk.Label(parent, text="No search performed yet", 
                                     font=("Arial", 10), bg="white", fg="#5d7a9e")
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
        
        # Clear path text
        self.path_text.delete(1.0, tk.END)
        
        # Search for jobs
        if algorithm == "BFS":
            results = self.job_manager.search_jobs_bfs(skills, location)
            algorithm_name = "BFS (Breadth-First Search)"
        else:
            results = self.job_manager.search_jobs_dfs(skills, location)
            algorithm_name = "DFS (Depth-First Search)"
        
        # Store results
        self.current_results = results
        self.current_algorithm = algorithm
        
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
                job['Company'],
                job.get('Address', 'N/A')
            ))
        
        # Show match scores and skills in path tab
        self.path_text.insert(tk.END, f"Search Algorithm: {algorithm_name}\n")
        self.path_text.insert(tk.END, f"Location: {self.user_data['location']}\n")
        self.path_text.insert(tk.END, f"Skills: {', '.join(self.user_data['skills'])}\n")
        self.path_text.insert(tk.END, "="*60 + "\n\n")
        
        for i, job in enumerate(results[:10], 1):  # Show first 10 jobs with details
            self.path_text.insert(tk.END, f"{i}. {job['Job Title']} at {job['Company']}\n")
            self.path_text.insert(tk.END, f"   Location: {job['Location']} ({job.get('Address', 'N/A')})\n")
            self.path_text.insert(tk.END, f"   Matching Skills: {', '.join(job.get('matching_skills', []))}\n")
            self.path_text.insert(tk.END, f"   Match Score: {job.get('match_score', 0)}/5\n")
            self.path_text.insert(tk.END, f"   Salary: {job['Salary']}\n")
            self.path_text.insert(tk.END, "-"*50 + "\n\n")
        
        self.results_label.config(
            text=f"Found {len(results)} matching jobs using {algorithm_name}"
        )
        self.notebook.select(0)  # Switch to results tab
    
    def show_search_path(self):
        if not self.current_results:
            messagebox.showwarning("No Search", "Please perform a search first to see the path.")
            return
        
        # Get search paths for current algorithm
        search_paths = self.job_manager.get_search_paths(self.current_algorithm)
        
        if not search_paths:
            self.path_text.delete(1.0, tk.END)
            self.path_text.insert(tk.END, "No search path data available.\n")
            self.path_text.insert(tk.END, "Please perform a new search to generate path data.\n")
            return
        
        self.path_text.delete(1.0, tk.END)
        self.path_text.insert(tk.END, f"🔍 {self.current_algorithm} SEARCH PATH VISUALIZATION\n")
        self.path_text.insert(tk.END, "="*60 + "\n\n")
        
        for i, path_info in enumerate(search_paths[:20], 1):  # Show first 20 paths
            node_id = path_info['node']
            path = path_info['path']
            match_score = path_info['match_score']
            skills = path_info['skills']
            
            self.path_text.insert(tk.END, f"Path {i} (Score: {match_score}/5)\n")
            self.path_text.insert(tk.END, f"Matching Skills: {', '.join(skills)}\n")
            self.path_text.insert(tk.END, "Path: ")
            
            for j, node in enumerate(path):
                if j == len(path) - 1:
                    self.path_text.insert(tk.END, f"{node} ★\n", "highlight")
                else:
                    self.path_text.insert(tk.END, f"{node} → ")
            
            self.path_text.insert(tk.END, "\n")
            
            # Get job details for the final node
            node_num = int(node_id.split('_')[1])
            if node_num < len(self.job_manager.jobs):
                job = self.job_manager.jobs.iloc[node_num]
                self.path_text.insert(tk.END, f"Final Job: {job['Job Title']} at {job['Company']}\n")
                self.path_text.insert(tk.END, f"Location: {job['Location']}\n")
                self.path_text.insert(tk.END, f"Required Skills: {job['Required Skills']}\n")
            
            self.path_text.insert(tk.END, "-"*50 + "\n\n")
        
        # Configure text tag for highlighting
        self.path_text.tag_configure("highlight", foreground="#c44536", font=("Courier", 10, "bold"))
        
        self.notebook.select(1)  # Switch to path tab
    
    def update_profile(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Update Profile")
        dialog.geometry("400x350")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - dialog.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Content
        main_frame = tk.Frame(dialog, padx=20, pady=20, bg="white")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(main_frame, text="Update Your Profile", 
                font=("Arial", 16, "bold"), bg="white", fg="#1e3a5f").pack(pady=(0, 20))
        
        # Skills input
        tk.Label(main_frame, text="Your Skills (comma-separated):", 
                font=("Arial", 10), bg="white", fg="#1e3a5f").pack(anchor="w", pady=(5, 0))
        
        skills_var = tk.StringVar(value=', '.join(self.user_data.get('skills', [])))
        skills_entry = tk.Entry(main_frame, textvariable=skills_var, width=40, 
                               highlightthickness=1, highlightcolor="#3d5a80")
        skills_entry.pack(pady=(0, 10), fill=tk.X)
        
        # Location input with Nepal cities suggestion
        tk.Label(main_frame, text="Your Location (Nepal City):", 
                font=("Arial", 10), bg="white", fg="#1e3a5f").pack(anchor="w", pady=(5, 0))
        
        location_var = tk.StringVar(value=self.user_data.get('location', ''))
        
        # Create a dropdown for Nepal cities
        nepal_cities = [
            "Kathmandu", "Pokhara", "Lalitpur", "Bhaktapur", "Biratnagar",
            "Birgunj", "Butwal", "Dharan", "Hetauda", "Janakpur",
            "Nepalgunj", "Itahari", "Tulsipur", "Bhimdatta", "Kalaiya",
            "Ghorahi", "Lekhnath", "Kirtipur", "Tilottama", "Birendranagar"
        ]
        
        location_combobox = ttk.Combobox(main_frame, textvariable=location_var, 
                                        values=nepal_cities, width=38)
        location_combobox.pack(pady=(0, 20), fill=tk.X)
        
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
        button_frame = tk.Frame(main_frame, bg="white")
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Button(button_frame, text="Save", command=save_profile,
                 bg="#3d5a80", fg="white", bd=0, padx=20).pack(side=tk.LEFT, padx=(0, 10))
        tk.Button(button_frame, text="Cancel", command=dialog.destroy,
                 bg="#95a5a6", fg="white", bd=0, padx=20).pack(side=tk.LEFT)
    
    def generate_nepal_jobs(self):
        count = self.job_manager.generate_nepal_jobs()
        messagebox.showinfo("Success", f"Generated {count} Nepal-specific job entries in jobs.csv")
    
    def view_all_jobs(self):
        all_jobs = self.job_manager.get_all_jobs()
        
        # Clear previous results
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Clear path text
        self.path_text.delete(1.0, tk.END)
        
        # Display all jobs
        for job in all_jobs:
            self.tree.insert("", "end", values=(
                job['Job Title'],
                job['Required Skills'],
                job['Location'],
                job['Salary'],
                job['Company'],
                job.get('Address', 'N/A')
            ))
        
        self.results_label.config(text=f"Showing {len(all_jobs)} total jobs")
        self.current_results = all_jobs
    
    def download_results(self):
        if not self.current_results:
            messagebox.showwarning("No Results", "No search results to download. Please perform a search first.")
            return
        
        # Ask user for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"job_results_{timestamp}.csv"
        
        # Open file dialog for saving
        desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
        file_path = filedialog.asksaveasfilename(
            initialdir=desktop_path,
            initialfile=default_filename,
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                # Prepare data for CSV
                export_data = []
                for job in self.current_results:
                    export_data.append({
                        'Job Title': job.get('Job Title', ''),
                        'Required Skills': job.get('Required Skills', ''),
                        'Location': job.get('Location', ''),
                        'Salary': job.get('Salary', ''),
                        'Company': job.get('Company', ''),
                        'Address': job.get('Address', 'N/A'),
                        'Match Score': job.get('match_score', 'N/A'),
                        'Matching Skills': ', '.join(job.get('matching_skills', [])),
                        'Search Algorithm': self.current_algorithm if hasattr(self, 'current_algorithm') else 'N/A'
                    })
                
                # Convert to DataFrame and save
                df = pd.DataFrame(export_data)
                df.to_csv(file_path, index=False, encoding='utf-8')
                
                messagebox.showinfo("Success", f"Results exported successfully to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export results: {str(e)}")
    
    def logout(self):
        self.current_user = None
        self.user_data = None
        self.current_results = []
        self.show_auth_window()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = MainApplication()
    app.run()
    