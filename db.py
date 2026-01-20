from supabase import create_client
from dotenv import load_dotenv
import os

# ==================================================
# ENV
# ==================================================
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==================================================
# BASIC INFO (EDIT THIS FROM YOUR RESUME)
# ==================================================
EMAIL = "pratik110301@gmail.com"
PROFILE_NAME = "Placement"  # can be Job / ML / Research later

# ==================================================
# 1️⃣ CREATE USER PROFILE
# ==================================================
profile = supabase.table("user_profiles").upsert(
    {
        "email": EMAIL,
        "profile_name": PROFILE_NAME,
        "is_active": True,
    },
    on_conflict="email,profile_name",
).execute()

profile_id = profile.data[0]["id"]
print("Profile created:", profile_id)

# ==================================================
# 2️⃣ PERSONAL DETAILS
# ==================================================
supabase.table("profile_personal").upsert({
    "profile_id": profile_id,
    "first_name": "Pratik",
    "middle_name": None,
    "last_name": "Mahajan",
    "email": EMAIL,
    "phone": "9876543210",
    "gender": "Male",
}, on_conflict="profile_id").execute()

# ==================================================
# 3️⃣ EDUCATION
# ==================================================
education_rows = [
    {
        "profile_id": profile_id,
        "degree": "M.Tech",
        "specialization": "Mechanical Engineering",
        "institute": "IIT Bombay",
        "university": "IIT Bombay",
        "year_of_passing": 2025,
        "cpi": 8.34,
    },
    {
        "profile_id": profile_id,
        "degree": "B.Tech",
        "specialization": "Mechanical Engineering",
        "institute": "Your UG College",
        "university": "Your University",
        "year_of_passing": 2023,
        "cpi": 8.10,
    },
]

supabase.table("profile_education").insert(education_rows).execute()

# ==================================================
# 4️⃣ EXPERIENCE
# ==================================================
experience_rows = [
    {
        "profile_id": profile_id,
        "company": "ValuAI",
        "role": "Machine Learning Intern",
        "location": "Remote",
        "start_date": "2024-05-01",
        "end_date": "2024-07-01",
        "description": "Worked on LLM-powered document intelligence and embeddings.",
    },
    {
        "profile_id": profile_id,
        "company": "Slothpay",
        "role": "Backend Developer Intern",
        "location": "Remote",
        "start_date": "2023-06-01",
        "end_date": "2023-08-01",
        "description": "Built FastAPI backend and payment integrations.",
    },
]

supabase.table("profile_experience").insert(experience_rows).execute()

# ==================================================
# 5️⃣ PROJECTS
# ==================================================
project_rows = [
    {
        "profile_id": profile_id,
        "title": "Voice-driven CAD Agent",
        "description": "Speech-to-CAD system with stress analysis using FEniCS.",
        "technologies": "Python, FEniCS, Whisper, GPT",
    },
    {
        "profile_id": profile_id,
        "title": "Research Paper Explorer",
        "description": "FAISS-powered semantic search over research papers.",
        "technologies": "Python, FAISS, Sentence Transformers",
    },
]

supabase.table("profile_projects").insert(project_rows).execute()

# ==================================================
# 6️⃣ SKILLS
# ==================================================
skills = [
    ("Languages", "Python"),
    ("Languages", "C++"),
    ("Frameworks", "FastAPI"),
    ("Frameworks", "Next.js"),
    ("AI/ML", "LangGraph"),
    ("AI/ML", "Gemini"),
    ("Databases", "PostgreSQL"),
    ("Tools", "Git"),
    ("Tools", "Docker"),
]

skill_rows = [
    {"profile_id": profile_id, "category": cat, "skill": skill}
    for cat, skill in skills
]

supabase.table("profile_skills").insert(skill_rows).execute()

print("✅ Profile data inserted successfully")
