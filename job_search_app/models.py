class User:
    def __init__(self, id=None, username="", email="", skills=None, location=""):
        self.id = id
        self.username = username
        self.email = email
        self.skills = skills or []
        self.location = location
    
    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "skills": self.skills,
            "location": self.location
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data.get("id"),
            username=data.get("username", ""),
            email=data.get("email", ""),
            skills=data.get("skills", []),
            location=data.get("location", "")
        )


class Job:
    def __init__(self, title="", required_skills="", location="", salary="", company=""):
        self.title = title
        self.required_skills = required_skills
        self.location = location
        self.salary = salary
        self.company = company
    
    def to_dict(self):
        return {
            "Job Title": self.title,
            "Required Skills": self.required_skills,
            "Location": self.location,
            "Salary": self.salary,
            "Company": self.company
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            title=data.get("Job Title", ""),
            required_skills=data.get("Required Skills", ""),
            location=data.get("Location", ""),
            salary=data.get("Salary", ""),
            company=data.get("Company", "")
        )