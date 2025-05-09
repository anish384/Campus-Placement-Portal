import pymongo
from datetime import datetime, timedelta

# Connect to MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/StarterFlask")
db = client.get_database()
jobs_collection = db["jobs"]

# List of dummy job data (with standardized eligible_branches)
dummy_jobs = [
    {
        "title": "Software Engineer",
        "description": "Develop and maintain software applications using Python and JavaScript.",
        "company_name": "TechCorp",
        "location": "Bangalore, India",
        "job_type": "Full-time",
        "salary_range": "80000-120000",
        "min_cgpa": 7.0,
        "eligible_branches": ["Computer Science", "Information Technology", "Electronics"],
        "application_deadline": datetime.now() + timedelta(days=30),
        "created_at": datetime.now(),
        "recruiter_name": "John Doe",
        "company_logo": ""
    },
    {
        "title": "Data Analyst",
        "description": "Analyze large datasets and provide insights to business stakeholders.",
        "company_name": "DataInsights",
        "location": "Pune, India",
        "job_type": "Full-time",
        "salary_range": "70000-100000",
        "min_cgpa": 6.5,
        "eligible_branches": ["Computer Science", "Information Technology", "Electronics", "Mechanical"],
        "application_deadline": datetime.now() + timedelta(days=45),
        "created_at": datetime.now(),
        "recruiter_name": "Jane Smith",
        "company_logo": ""
    },
    {
        "title": "Frontend Developer",
        "description": "Build responsive and user-friendly web interfaces using React.js.",
        "company_name": "WebSolutions",
        "location": "Hyderabad, India",
        "job_type": "Full-time",
        "salary_range": "60000-90000",
        "min_cgpa": 6.0,
        "eligible_branches": ["Computer Science", "Information Technology"],
        "application_deadline": datetime.now() + timedelta(days=20),
        "created_at": datetime.now(),
        "recruiter_name": "Mike Johnson",
        "company_logo": ""
    },
    {
        "title": "DevOps Engineer",
        "description": "Implement and maintain CI/CD pipelines and cloud infrastructure.",
        "company_name": "CloudTech",
        "location": "Mumbai, India",
        "job_type": "Full-time",
        "salary_range": "90000-130000",
        "min_cgpa": 7.5,
        "eligible_branches": ["Computer Science", "Information Technology", "Electrical"],
        "application_deadline": datetime.now() + timedelta(days=60),
        "created_at": datetime.now(),
        "recruiter_name": "Sarah Williams",
        "company_logo": ""
    },
    {
        "title": "Intern",
        "description": "Internship opportunity for students to learn software development.",
        "company_name": "StartUpInc",
        "location": "Delhi, India",
        "job_type": "Internship",
        "salary_range": "10000-15000",
        "min_cgpa": 6.0,
        "eligible_branches": ["Computer Science", "Information Technology", "Electronics", "Electrical", "Mechanical"],
        "application_deadline": datetime.now() + timedelta(days=15),
        "created_at": datetime.now(),
        "recruiter_name": "David Brown",
        "company_logo": ""
    }
]

# Insert dummy data
try:
    result = jobs_collection.insert_many(dummy_jobs)
    print(f"Successfully inserted {len(result.inserted_ids)} documents into the jobs collection")
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    client.close()