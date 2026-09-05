"""
Module 3: Database
-------------------
Handles SQLite connection and schema creation for the Resume Builder app.
All tables described in the spec (Users, Resume, Personal Details, Education,
Skills, Projects, Experience/Internships, Certifications, Achievements) live here.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.db")


def get_db():
    """Return a SQLite connection with row access by column name."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all tables if they do not already exist."""
    conn = get_db()
    cur = conn.cursor()

    # ---------- Users ----------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ---------- Resume (one row per resume a user creates) ----------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS resumes (
            resume_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT DEFAULT 'My Resume',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
    """)

    # ---------- Personal Details ----------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS personal_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resume_id INTEGER NOT NULL,
            full_name TEXT,
            email TEXT,
            phone TEXT,
            address TEXT,
            summary TEXT,
            photo TEXT,
            FOREIGN KEY (resume_id) REFERENCES resumes(resume_id) ON DELETE CASCADE
        )
    """)

    # ---------- Education ----------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS education (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resume_id INTEGER NOT NULL,
            degree TEXT,
            institution TEXT,
            year TEXT,
            grade TEXT,
            FOREIGN KEY (resume_id) REFERENCES resumes(resume_id) ON DELETE CASCADE
        )
    """)

    # ---------- Skills ----------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resume_id INTEGER NOT NULL,
            skill_name TEXT,
            FOREIGN KEY (resume_id) REFERENCES resumes(resume_id) ON DELETE CASCADE
        )
    """)

    # ---------- Projects ----------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resume_id INTEGER NOT NULL,
            title TEXT,
            description TEXT,
            tech_used TEXT,
            link TEXT,
            FOREIGN KEY (resume_id) REFERENCES resumes(resume_id) ON DELETE CASCADE
        )
    """)

    # ---------- Experience / Internships ----------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS experience (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resume_id INTEGER NOT NULL,
            company TEXT,
            role TEXT,
            duration TEXT,
            description TEXT,
            FOREIGN KEY (resume_id) REFERENCES resumes(resume_id) ON DELETE CASCADE
        )
    """)

    # ---------- Certifications ----------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS certifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resume_id INTEGER NOT NULL,
            name TEXT,
            issuer TEXT,
            year TEXT,
            FOREIGN KEY (resume_id) REFERENCES resumes(resume_id) ON DELETE CASCADE
        )
    """)

    # ---------- Achievements ----------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resume_id INTEGER NOT NULL,
            description TEXT,
            FOREIGN KEY (resume_id) REFERENCES resumes(resume_id) ON DELETE CASCADE
        )
    """)
        # Add created_at column to existing resumes table if it is missing
    columns = [row[1] for row in cur.execute("PRAGMA table_info(resumes)")]
    if "created_at" not in columns:
        cur.execute("ALTER TABLE resumes ADD COLUMN created_at TIMESTAMP")

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Helper functions used by app.py routes
# ---------------------------------------------------------------------------

def create_resume(user_id=None, title="My Resume"):
    conn = get_db()
    cur = conn.execute(
        """INSERT INTO resumes (user_id, title, created_at)
           VALUES (?, ?, datetime('now', '+5 hours', '+30 minutes'))""",
        (user_id, title)
    )
    conn.commit()
    resume_id = cur.lastrowid
    conn.close()
    return resume_id


def delete_resume(resume_id):
    conn = get_db()
    conn.execute("DELETE FROM resumes WHERE resume_id = ?", (resume_id,))
    conn.commit()
    conn.close()


def get_resume_data(resume_id):
    """Gather everything needed to render/preview/export a resume."""
    conn = get_db()
    data = {
        "resume_id": resume_id,
        "personal": conn.execute(
            "SELECT * FROM personal_details WHERE resume_id = ?", (resume_id,)
        ).fetchone(),
        "education": conn.execute(
            "SELECT * FROM education WHERE resume_id = ?", (resume_id,)
        ).fetchall(),
        "skills": conn.execute(
            "SELECT * FROM skills WHERE resume_id = ?", (resume_id,)
        ).fetchall(),
        "projects": conn.execute(
            "SELECT * FROM projects WHERE resume_id = ?", (resume_id,)
        ).fetchall(),
        "experience": conn.execute(
            "SELECT * FROM experience WHERE resume_id = ?", (resume_id,)
        ).fetchall(),
        "certifications": conn.execute(
            "SELECT * FROM certifications WHERE resume_id = ?", (resume_id,)
        ).fetchall(),
        "achievements": conn.execute(
            "SELECT * FROM achievements WHERE resume_id = ?", (resume_id,)
        ).fetchall(),
    }
    conn.close()
    return data
