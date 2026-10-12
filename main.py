from contextlib import asynccontextmanager
from pathlib import Path
import sqlite3
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "jobs.db"

def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with connect_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT NOT NULL,
            job_type TEXT NOT NULL,
            salary TEXT NOT NULL,
            description TEXT NOT NULL,
            skills TEXT NOT NULL,
            posted_days INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT NOT NULL,
            user_email TEXT NOT NULL,
            job_id INTEGER NOT NULL REFERENCES jobs(id),
            resume_name TEXT NOT NULL,
            cover_letter TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'APPLIED',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(user_email, job_id)
        );
        """)
        count = db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        if count == 0:
            seed = [
                ("Python Backend Developer", "Northstar Labs", "Chennai, India", "Full-time", "₹6–10 LPA",
                 "Build reliable APIs and backend services for a growing product team. Work with engineers to design, test, and monitor production services.",
                 "Python, FastAPI, SQL, REST APIs", 2),
                ("Junior Machine Learning Engineer", "BlueOrbit AI", "Bengaluru, India", "Full-time", "₹8–14 LPA",
                 "Help build and evaluate machine-learning pipelines, prepare datasets, and deploy models with support from senior ML engineers.",
                 "Python, Machine Learning, Pandas, Scikit-learn", 1),
                ("Frontend Developer Intern", "PixelCraft Studio", "Remote", "Internship", "₹15,000–25,000/month",
                 "Create accessible, responsive web interfaces and collaborate with designers and backend developers.",
                 "HTML, CSS, JavaScript, React", 3),
                ("Data Analyst", "InsightBridge", "Coimbatore, India", "Full-time", "₹4–7 LPA",
                 "Analyze business datasets, build dashboards, and communicate actionable findings to stakeholders.",
                 "SQL, Python, Excel, Power BI", 4),
                ("Cloud Support Associate", "SkyGrid Systems", "Hyderabad, India", "Full-time", "₹5–8 LPA",
                 "Support cloud workloads, investigate incidents, document fixes, and improve operational reliability.",
                 "Linux, Networking, AWS, Troubleshooting", 5),
                ("AI Research Intern", "Cognition Works", "Remote", "Internship", "₹20,000/month",
                 "Prototype AI experiments, review technical papers, and evaluate models under the guidance of a research team.",
                 "Python, Deep Learning, PyTorch, Research", 6),
            ]
            db.executemany("""INSERT INTO jobs
                (title, company, location, job_type, salary, description, skills, posted_days)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", seed)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="HireHub Recruitment API",
    description="Demo recruitment platform API. SQLite is used for local development; production can use managed PostgreSQL, Redis, a search engine, and a message broker.",
    version="1.0.0",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

class ApplicationCreate(BaseModel):
    user_name: str = Field(min_length=2, max_length=100)
    user_email: str = Field(min_length=5, max_length=200)
    resume_name: str = Field(min_length=1, max_length=200)
    cover_letter: str = Field(default="", max_length=2000)

def job_dict(row):
    item = dict(row)
    item["skills"] = [s.strip() for s in item["skills"].split(",") if s.strip()]
    return item

@app.get("/", include_in_schema=False)
def home():
    return FileResponse(BASE_DIR / "static" / "index.html")

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "HireHub API"}

@app.get("/api/jobs")
def search_jobs(
    q: str = Query(default="", max_length=100),
    location: str = Query(default="", max_length=100),
    job_type: str = Query(default="", max_length=40),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=50),
):
    where, params = [], []
    if q.strip():
        term = f"%{q.strip()}%"
        where.append("(title LIKE ? OR company LIKE ? OR skills LIKE ? OR description LIKE ?)")
        params.extend([term, term, term, term])
    if location.strip():
        where.append("location LIKE ?")
        params.append(f"%{location.strip()}%")
    if job_type.strip():
        where.append("job_type = ?")
        params.append(job_type.strip())
    clause = " WHERE " + " AND ".join(where) if where else ""
    with connect_db() as db:
        total = db.execute("SELECT COUNT(*) FROM jobs" + clause, params).fetchone()[0]
        rows = db.execute(
            "SELECT * FROM jobs" + clause + " ORDER BY posted_days ASC LIMIT ? OFFSET ?",
            params + [limit, (page - 1) * limit]
        ).fetchall()
    return {"items": [job_dict(r) for r in rows], "total": total, "page": page, "limit": limit}

@app.get("/api/jobs/{job_id}")
def get_job(job_id: int):
    with connect_db() as db:
        row = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    return job_dict(row)

@app.post("/api/jobs/{job_id}/applications", status_code=201)
def apply_for_job(job_id: int, payload: ApplicationCreate):
    with connect_db() as db:
        job = db.execute("SELECT id FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        try:
            cur = db.execute(
                """INSERT INTO applications (user_name, user_email, job_id, resume_name, cover_letter)
                   VALUES (?, ?, ?, ?, ?)""",
                (payload.user_name.strip(), payload.user_email.strip().lower(),
                 job_id, payload.resume_name.strip(), payload.cover_letter.strip())
            )
            app_id = cur.lastrowid
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=409, detail="You have already applied to this job with this email.")
        row = db.execute("""
            SELECT a.id, a.user_name, a.user_email, a.job_id, a.resume_name,
                   a.cover_letter, a.status, a.created_at, j.title AS job_title, j.company
            FROM applications a JOIN jobs j ON j.id = a.job_id WHERE a.id = ?
        """, (app_id,)).fetchone()
    return {"message": "Application submitted successfully", "application": dict(row)}

@app.get("/api/applications/{application_id}/status")
def application_status(application_id: int, email: str = Query(..., min_length=5)):
    with connect_db() as db:
        row = db.execute("""
            SELECT a.id AS application_id, a.status, a.created_at, j.title AS job_title, j.company
            FROM applications a JOIN jobs j ON j.id = a.job_id
            WHERE a.id = ? AND lower(a.user_email) = lower(?)
        """, (application_id, email.strip())).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Application not found for that ID and email.")
    return dict(row)

@app.get("/api/users/applications")
def application_history(email: str = Query(..., min_length=5)):
    with connect_db() as db:
        rows = db.execute("""
            SELECT a.id AS application_id, a.user_name, a.user_email, a.status, a.created_at,
                   j.id AS job_id, j.title AS job_title, j.company, j.location, j.job_type
            FROM applications a JOIN jobs j ON j.id = a.job_id
            WHERE lower(a.user_email) = lower(?)
            ORDER BY a.created_at DESC
        """, (email.strip(),)).fetchall()
    return {"items": [dict(r) for r in rows], "total": len(rows)}

# Demo-only endpoint to illustrate status changes. Protect with recruiter authentication in production.
@app.patch("/api/demo/applications/{application_id}/status")
def update_demo_status(application_id: int, status: str = Query(...)):
    allowed = {"APPLIED", "UNDER_REVIEW", "SHORTLISTED", "INTERVIEW", "SELECTED", "REJECTED"}
    normalized = status.strip().upper()
    if normalized not in allowed:
        raise HTTPException(status_code=400, detail=f"Status must be one of: {', '.join(sorted(allowed))}")
    with connect_db() as db:
        cur = db.execute("UPDATE applications SET status = ? WHERE id = ?", (normalized, application_id))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Application not found")
    return {"message": "Demo application status updated", "application_id": application_id, "status": normalized}
