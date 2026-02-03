import pandas as pd
import random
import os
from collections import deque

class JobSearchManager:
    def __init__(self, jobs_file='jobs.csv'):
        self.jobs_file = jobs_file
        self.jobs = self.load_jobs()
    
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
            'Job Title', 'Required Skills', 'Location', 'Salary', 'Company'
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
        """Build graph representation of jobs for BFS/DFS"""
        graph = {}
        
        if self.jobs.empty:
            return graph
        
        for idx, job in self.jobs.iterrows():
            node_id = f"job_{idx}"
            job_dict = job.to_dict()
            graph[node_id] = {
                'data': job_dict,
                'neighbors': []
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
        """Search jobs using BFS (Breadth-First Search) algorithm"""
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
        
        # Start BFS from all job nodes
        for node_id in graph.keys():
            if node_id not in visited:
                queue.append(node_id)
                visited.add(node_id)
                
                while queue and len(matching_jobs) < max_results:
                    current_node = queue.popleft()
                    job_data = graph[current_node]['data']
                    
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
                        # Add match score to job data for sorting
                        job_data_with_score = job_data.copy()
                        job_data_with_score['match_score'] = skill_match_count
                        matching_jobs.append(job_data_with_score)
                    
                    # Add neighbors to queue
                    for neighbor in graph[current_node]['neighbors']:
                        if neighbor not in visited and len(matching_jobs) < max_results:
                            visited.add(neighbor)
                            queue.append(neighbor)
        
        # Sort by match score (descending)
        matching_jobs.sort(key=lambda x: x.get('match_score', 0), reverse=True)
        
        # Remove match_score before returning
        for job in matching_jobs:
            if 'match_score' in job:
                del job['match_score']
        
        return matching_jobs[:max_results]
    
    def search_jobs_dfs(self, user_skills, user_location, max_results=50, max_depth=5):
        """Search jobs using DFS (Depth-First Search) algorithm"""
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
        
        def dfs(node_id, depth):
            if depth > max_depth or node_id in visited or len(matching_jobs) >= max_results:
                return
            
            visited.add(node_id)
            job_data = graph[node_id]['data']
            
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
                # Add match score to job data for sorting
                job_data_with_score = job_data.copy()
                job_data_with_score['match_score'] = skill_match_count
                matching_jobs.append(job_data_with_score)
            
            # Recursively visit neighbors (DFS)
            for neighbor in graph[node_id]['neighbors']:
                if len(matching_jobs) < max_results:
                    dfs(neighbor, depth + 1)
        
        # Start DFS from all job nodes
        for node_id in graph.keys():
            if len(matching_jobs) < max_results:
                dfs(node_id, 0)
        
        # Sort by match score (descending)
        matching_jobs.sort(key=lambda x: x.get('match_score', 0), reverse=True)
        
        # Remove match_score before returning
        for job in matching_jobs:
            if 'match_score' in job:
                del job['match_score']
        
        return matching_jobs[:max_results]
    
    def generate_dummy_data(self, num_jobs=50):
        """Generate dummy job data"""
        print(f"\nGenerating {num_jobs} dummy job records...")
        
        job_titles = [
            "Software Engineer", "Data Scientist", "Web Developer",
            "DevOps Engineer", "UX Designer", "Product Manager",
            "Machine Learning Engineer", "Cloud Architect",
            "Cybersecurity Analyst", "Database Administrator",
            "Frontend Developer", "Backend Developer", "Full Stack Developer",
            "Mobile App Developer", "AI Researcher", "Network Engineer",
            "Systems Analyst", "QA Engineer", "Technical Writer",
            "Project Manager", "Scrum Master", "Business Analyst"
        ]
        
        skills = [
            "python", "java", "javascript", "react", "node.js",
            "sql", "aws", "docker", "kubernetes", "machine learning",
            "data analysis", "html", "css", "git", "rest api",
            "mongodb", "postgresql", "linux", "agile", "scrum",
            "typescript", "angular", "vue.js", "react native",
            "c++", "c#", "ruby", "php", "go", "rust",
            "tableau", "power bi", "excel", "data visualization",
            "tensorflow", "pytorch", "nlp", "computer vision"
        ]
        
        locations = [
            "New York", "San Francisco", "Austin", "Seattle",
            "Boston", "Chicago", "Los Angeles", "Remote",
            "London", "Berlin", "Toronto", "Singapore",
            "Bangalore", "Sydney", "Tokyo", "Paris",
            "Mumbai", "Dubai", "Amsterdam", "Berlin"
        ]
        
        companies = [
            "TechCorp", "DataSystems", "WebSolutions", "CloudTech",
            "InnovateInc", "FutureWorks", "DigitalDreams", "ByteMasters",
            "CodeCrafters", "AI Innovations", "CyberSecure", "NetWorks",
            "Google", "Microsoft", "Amazon", "Meta", "Apple",
            "Netflix", "Tesla", "SpaceX", "IBM", "Oracle",
            "Salesforce", "Adobe", "Intel", "NVIDIA", "AMD"
        ]
        
        jobs_data = []
        
        for i in range(num_jobs):
            title = random.choice(job_titles)
            num_skills = random.randint(2, 6)
            job_skills = random.sample(skills, num_skills)
            location = random.choice(locations)
            salary = f"${random.randint(60, 200)}k/year"
            company = random.choice(companies)
            
            jobs_data.append({
                'Job Title': title,
                'Required Skills': ', '.join(job_skills),
                'Location': location,
                'Salary': salary,
                'Company': company
            })
        
        self.jobs = pd.DataFrame(jobs_data)
        if self.save_jobs():
            print(f"Successfully generated {num_jobs} job records in {self.jobs_file}")
            return num_jobs
        else:
            print("Error: Could not save jobs to file")
            return 0