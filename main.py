from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai
import os, re, json
from datetime import datetime
from typing import Optional, List
from supabase import create_client

# ==================================================
# ENV
# ==================================================
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY missing")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Supabase env missing")

# ==================================================
# Gemini
# ==================================================
genai.configure(api_key=GEMINI_API_KEY)

# ==================================================
# Supabase
# ==================================================
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==================================================
# App
# ==================================================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ok for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================================================
# Utils
# ==================================================
def extract_json(text: str):
    text = re.sub(r"```(?:json)?", "", text)
    return json.loads(text.strip())

# ==================================================
# Models
# ==================================================
class GoogleUser(BaseModel):
    email: str
    name: str
    picture: Optional[str] = None

class Field(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    placeholder: Optional[str] = None
    type: Optional[str] = None
    label: Optional[str] = None

class FillRequest(BaseModel):
    user: GoogleUser
    fields: List[Field]

# ==================================================
# AUTH → Supabase UPSERT
# ==================================================
@app.post("/auth/google")
def google_auth(user: GoogleUser):
    supabase.table("profiles").upsert(
        {
            "email": user.email,
            "name": user.name,
            "picture": user.picture,
            "last_login": datetime.utcnow().isoformat(),
        },
        on_conflict="email",
    ).execute()

    return {"ok": True}

# ==================================================
# FETCH FULL STRUCTURED PROFILE
# ==================================================
def fetch_full_profile(email: str, profile_name: str = "Placement"):

    profile = (
        supabase.table("user_profiles")
        .select("id")
        .eq("email", email)
        .eq("profile_name", profile_name)
        .single()
        .execute()
    )

    if not profile.data:
        return None

    pid = profile.data["id"]

    personal = (
        supabase.table("profile_personal")
        .select("*")
        .eq("profile_id", pid)
        .single()
        .execute()
    ).data

    education = (
        supabase.table("profile_education")
        .select("*")
        .eq("profile_id", pid)
        .execute()
    ).data

    experience = (
        supabase.table("profile_experience")
        .select("*")
        .eq("profile_id", pid)
        .execute()
    ).data

    projects = (
        supabase.table("profile_projects")
        .select("*")
        .eq("profile_id", pid)
        .execute()
    ).data

    skills = (
        supabase.table("profile_skills")
        .select("*")
        .eq("profile_id", pid)
        .execute()
    ).data

    return {
        "personal": personal,
        "education": education,
        "experience": experience,
        "projects": projects,
        "skills": skills,
    }

# ==================================================
# AUTOFILL (DB → LLM → FORM)
# ==================================================
@app.post("/fill")
def autofill(req: FillRequest):

    # 1️⃣ Verify auth user exists
    user = (
        supabase.table("profiles")
        .select("email")
        .eq("email", req.user.email)
        .execute()
    )

    if not user.data:
        return {"error": "User not found"}

    # 2️⃣ Fetch authoritative profile
    profile_data = fetch_full_profile(req.user.email, "Placement")

    if not profile_data:
        return {"error": "Profile not found"}

    # 3️⃣ Build strict prompt
    prompt = f"""
You are a STRICT and CAREFUL form-filling engine.

Your task is to fill form fields using the user profile.
Accuracy is more important than completeness.

====================
CRITICAL RULES
====================

1. NEVER guess.
2. NEVER infer by position or order.
3. If a value does NOT strictly match the field requirement, return an EMPTY STRING "".
4. Returning "" is ALWAYS better than returning a wrong value.

====================
FIELD TYPE RULES
====================

• NAME fields:
  - Alphabetic only
  - No numbers
  - Max 50 characters

• EMAIL fields:
  - Must contain "@"
  - Must look like a valid email

• PHONE / MOBILE fields:
  - DIGITS ONLY
  - Minimum 8 digits
  - If value contains ANY letters → return ""

• SALARY / AMOUNT fields:
  - DIGITS ONLY
  - No text, no currency, no commas
  - If unsure → return ""

• GENDER fields:
  - Allowed values: Male, Female, Other
  - Anything else → ""

• SKILLS fields:
  - Return ALL skills together as a single comma-separated string
  - Example: "Python, C++, FastAPI, Next.js"
  - NEVER put skills into non-skill fields

• COMPANY / EMPLOYER fields:
  - Must be a company or organization name
  - Do NOT return technologies or frameworks
  - If unsure → ""

• DEGREE / EDUCATION fields:
  - Allowed examples: B.Tech, M.Tech, MSc, PhD

• DATE fields:
  - Format strictly as YYYY-MM-DD
  - If not sure → ""

• URL / LINKEDIN fields:
  - Must start with http, https, or www
  - Otherwise → ""

====================
INPUT
====================

USER PROFILE (SOURCE OF TRUTH):
{json.dumps(profile_data, indent=2)}

FORM FIELDS:
{json.dumps([f.dict() for f in req.fields], indent=2)}

====================
OUTPUT FORMAT
====================

Return ONLY valid JSON.
No explanation.
No markdown.
No extra text.

[
  {{
    "id": "<same id from input>",
    "name": "<same name from input>",
    "value": "<string or empty>"
  }}
]
"""

    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash-lite",
        generation_config={"temperature": 0},
    )

    response = model.generate_content(prompt)

    try:
        values = extract_json(response.text)
    except Exception as e:
        return {
            "error": "Gemini parse failed",
            "raw": response.text,
            "exception": str(e),
        }

    # 4️⃣ Log usage
    supabase.table("autofill_logs").insert(
        {
            "email": req.user.email,
            "fields": values,
            "created_at": datetime.utcnow().isoformat(),
        }
    ).execute()
    print(values)
    return {"values": values}
