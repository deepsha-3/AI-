import pandas as pd
import random
import os
from collections import deque
import csv
from datetime import datetime

class JobSearchManager:
    def __init__(self, jobs_file='jobs.csv'):
        self.jobs_file = jobs_file
        self.jobs = self.load_jobs()
        self.search_paths = {}  # Store search paths for each algorithm
    
    def load_jobs(self):
        """Load jobs from CSV file or create empty DataFrame"""
        if os.path.exists(self.jobs_file):
            try:
                jobs_df = pd.read_csv(self.jobs_file)
                if jobs_df.empty:
                    print(f"Note: {self.jobs_file} exists but is empty.")
                    return self.create_empty_jobs_df()
                print(f"Loaded {len(jobs_df)} jobs from {self.jobs_file}")
                return jobs_df
            except (pd.errors.EmptyDataError, pd.errors.ParserError):
                print(f"Note: {self.jobs_file} is corrupted or empty. Creating new job database.")
                return self.create_empty_jobs_df()
        else:
            print(f"Note: {self.jobs_file} not found. Will create when needed.")
            return self.create_empty_jobs_df()
    
    def create_empty_jobs_df(self):
        """Create an empty DataFrame with correct columns"""
        return pd.DataFrame(columns=[
            'Job Title', 'Required Skills', 'Location', 'Salary', 'Company', 'Address'
        ])
    
    def save_jobs(self):
        """Save jobs to CSV file"""
        try:
            self.jobs.to_csv(self.jobs_file, index=False)
            return True
        except Exception as e:
            print(f"Error saving jobs: {e}")
            return False
    
    def get_all_jobs(self):
        """Get all jobs"""
        if self.jobs.empty:
            return []
        
        return self.jobs.to_dict('records')
    
    def build_job_graph(self):
        """Build graph representation of jobs for BFS/DFS with path tracking"""
        graph = {}
        
        if self.jobs.empty:
            return graph
        
        for idx, job in self.jobs.iterrows():
            node_id = f"job_{idx}"
            job_dict = job.to_dict()
            graph[node_id] = {
                'data': job_dict,
                'neighbors': [],
                'path': []  # Store path to this node
            }
            
            # Connect jobs with similar required skills or same company/location
            for idx2, job2 in self.jobs.iterrows():
                if idx != idx2:
                    node_id2 = f"job_{idx2}"
                    
                    # Check if jobs share at least one required skill
                    skills1 = set(str(job['Required Skills']).lower().split(', '))
                    skills2 = set(str(job2['Required Skills']).lower().split(', '))
                    
                    # Check if jobs are in same location or same company
                    same_location = str(job['Location']).lower() == str(job2['Location']).lower()
                    same_company = str(job['Company']).lower() == str(job2['Company']).lower()
                    
                    # Connect if they share skills or are in same location/company
                    if skills1.intersection(skills2) or same_location or same_company:
                        if node_id2 not in graph[node_id]['neighbors']:
                            graph[node_id]['neighbors'].append(node_id2)
        
        return graph
    
    def search_jobs_bfs(self, user_skills, user_location, max_results=50):
        """Search jobs using BFS (Breadth-First Search) algorithm with path tracking"""
        if self.jobs.empty:
            print("No jobs available in database!")
            return []
        
        graph = self.build_job_graph()
        if not graph:
            return []
        
        user_skills_set = set([skill.strip().lower() for skill in user_skills])
        user_location = user_location.lower()
        
        matching_jobs = []
        visited = set()
        queue = deque()
        search_path = []
        
        # Start BFS from all job nodes
        for start_node in graph.keys():
            if start_node not in visited:
                queue.append((start_node, [start_node]))  # Store node with its path
                visited.add(start_node)
                
                while queue and len(matching_jobs) < max_results:
                    current_node, current_path = queue.popleft()
                    job_data = graph[current_node]['data']
                    
                    # Store the path for this node
                    graph[current_node]['path'] = current_path
                    
                    # Check if job matches user skills and location
                    job_skills = set(str(job_data['Required Skills']).lower().split(', '))
                    job_location = str(job_data['Location']).lower()
                    
                    # Calculate match score
                    skill_match_count = len(user_skills_set.intersection(job_skills))
                    location_match = (user_location in job_location or 
                                     'remote' in job_location or 
                                     'any' in job_location or
                                     user_location == job_location)
                    
                    # Add job if it matches location and has at least one matching skill
                    if location_match and skill_match_count > 0:
                        # Add match score and path to job data
                        job_data_with_extra = job_data.copy()
                        job_data_with_extra['match_score'] = skill_match_count
                        job_data_with_extra['search_path'] = current_path.copy()
                        job_data_with_extra['matching_skills'] = list(user_skills_set.intersection(job_skills))
                        matching_jobs.append(job_data_with_extra)
                        
                        # Add to search path visualization
                        search_path.append({
                            'node': current_node,
                            'path': current_path,
                            'match_score': skill_match_count,
                            'skills': list(user_skills_set.intersection(job_skills))
                        })
                    
                    # Add neighbors to queue with updated path
                    for neighbor in graph[current_node]['neighbors']:
                        if neighbor not in visited and len(matching_jobs) < max_results:
                            visited.add(neighbor)
                            new_path = current_path.copy()
                            new_path.append(neighbor)
                            queue.append((neighbor, new_path))
        
        # Store the search paths for display
        self.search_paths['BFS'] = search_path
        
        # Sort by match score (descending)
        matching_jobs.sort(key=lambda x: x.get('match_score', 0), reverse=True)
        
        return matching_jobs[:max_results]
    
    def search_jobs_dfs(self, user_skills, user_location, max_results=50, max_depth=5):
        """Search jobs using DFS (Depth-First Search) algorithm with path tracking"""
        if self.jobs.empty:
            print("No jobs available in database!")
            return []
        
        graph = self.build_job_graph()
        if not graph:
            return []
        
        user_skills_set = set([skill.strip().lower() for skill in user_skills])
        user_location = user_location.lower()
        
        matching_jobs = []
        visited = set()
        search_path = []
        
        def dfs(node_id, path, depth):
            if depth > max_depth or node_id in visited or len(matching_jobs) >= max_results:
                return
            
            visited.add(node_id)
            current_path = path + [node_id]
            job_data = graph[node_id]['data']
            
            # Store the path for this node
            graph[node_id]['path'] = current_path
            
            # Check if job matches user skills and location
            job_skills = set(str(job_data['Required Skills']).lower().split(', '))
            job_location = str(job_data['Location']).lower()
            
            # Calculate match score
            skill_match_count = len(user_skills_set.intersection(job_skills))
            location_match = (user_location in job_location or 
                             'remote' in job_location or 
                             'any' in job_location or
                             user_location == job_location)
            
            # Add job if it matches location and has at least one matching skill
            if location_match and skill_match_count > 0:
                # Add match score and path to job data
                job_data_with_extra = job_data.copy()
                job_data_with_extra['match_score'] = skill_match_count
                job_data_with_extra['search_path'] = current_path.copy()
                job_data_with_extra['matching_skills'] = list(user_skills_set.intersection(job_skills))
                matching_jobs.append(job_data_with_extra)
                
                # Add to search