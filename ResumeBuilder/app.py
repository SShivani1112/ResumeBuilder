"""
app.py
------
Main Flask application. Wires together:
  Module 1: Home Page
  Module 2: Resume Form
  Module 4: Preview Resume
  Module 6: Download Resume
Module 3 (database) lives in db.py, Module 5 (PDF generation) in pdf_generator.py.
"""

import os
from flask import (
    Flask, render_template, request, redirect, url_for, session, send_file, flash
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

import db
import pdf_generator

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.secret_key = "dev-secret-key-change-me"  # replace in production
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

with app.app_context():
    db.init_db()


# ===========================================================================
# Module 1: Home Page
# ===========================================================================

@app.route("/")
def home():
    """Landing page. If logged in, show the user's existing resumes."""
    resumes = []
    if session.get("user_id"):
        conn = db.get_db()
        resumes = conn.execute(
            "SELECT * FROM resumes WHERE user_id = ? ORDER BY created_at DESC",
            (session["user_id"],)
        ).fetchall()
        conn.close()
    return render_template("index.html", resumes=resumes)


# --- Optional auth (Register / Login) ---

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("All fields are required.")
            return redirect(url_for("register"))

        conn = db.get_db()
        existing = conn.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            conn.close()
            flash("An account with that email already exists.")
            return redirect(url_for("register"))

        conn.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (name, email, generate_password_hash(password))
        )
        conn.commit()
        conn.close()
        flash("Account created. Please log in.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = db.get_db()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["user_id"]
            session["user_name"] = user["name"]
            return redirect(url_for("home"))

        flash("Invalid email or password.")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# ===========================================================================
# Module 2 + 3: Resume Form -> Store Data in Database
# ===========================================================================

@app.route("/create")
def create_resume():
    """Start a brand-new resume and jump into the form."""
    user_id = session.get("user_id")  # None if not logged in (login is optional)
    resume_id = db.create_resume(user_id=user_id)
    return redirect(url_for("form", resume_id=resume_id))


@app.route("/form/<int:resume_id>")
def form(resume_id):
    """Render the multi-section resume form, pre-filled with existing data."""
    data = db.get_resume_data(resume_id)
    return render_template("form.html", resume_id=resume_id, data=data)


@app.route("/form/<int:resume_id>/personal", methods=["POST"])
def save_personal(resume_id):
    full_name = request.form.get("full_name", "")
    email = request.form.get("email", "")
    phone = request.form.get("phone", "")
    address = request.form.get("address", "")
    summary = request.form.get("summary", "")

    photo_path = None
    file = request.files.get("photo")
    if file and file.filename:
        filename = secure_filename(f"resume_{resume_id}_{file.filename}")
        photo_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(photo_path)

    conn = db.get_db()
    existing = conn.execute(
        "SELECT id FROM personal_details WHERE resume_id = ?", (resume_id,)
    ).fetchone()

    if existing:
        if photo_path:
            conn.execute(
                """UPDATE personal_details SET full_name=?, email=?, phone=?, address=?,
                   summary=?, photo=? WHERE resume_id=?""",
                (full_name, email, phone, address, summary, photo_path, resume_id)
            )
        else:
            conn.execute(
                """UPDATE personal_details SET full_name=?, email=?, phone=?, address=?,
                   summary=? WHERE resume_id=?""",
                (full_name, email, phone, address, summary, resume_id)
            )
    else:
        conn.execute(
            """INSERT INTO personal_details
               (resume_id, full_name, email, phone, address, summary, photo)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (resume_id, full_name, email, phone, address, summary, photo_path)
        )
    conn.commit()
    conn.close()
    return redirect(url_for("form", resume_id=resume_id))


def _save_repeating_section(table, resume_id, columns):
    """
    Shared helper for sections that allow multiple entries
    (education, skills, projects, experience, certifications, achievements).
    Expects form fields named like columnname_1, columnname_2, ... for each row.
    """
    conn = db.get_db()
    conn.execute(f"DELETE FROM {table} WHERE resume_id = ?", (resume_id,))

    # Determine how many rows were submitted using the first column's fields
    count = 0
    while request.form.get(f"{columns[0]}_{count + 1}") is not None:
        count += 1

    for i in range(1, count + 1):
        values = [request.form.get(f"{col}_{i}", "") for col in columns]
        placeholders = ", ".join(["?"] * (len(columns) + 1))
        col_names = ", ".join(["resume_id"] + columns)
        conn.execute(
            f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})",
            [resume_id] + values
        )
    conn.commit()
    conn.close()


@app.route("/form/<int:resume_id>/education", methods=["POST"])
def save_education(resume_id):
    _save_repeating_section("education", resume_id, ["degree", "institution", "year", "grade"])
    return redirect(url_for("form", resume_id=resume_id))


@app.route("/form/<int:resume_id>/skills", methods=["POST"])
def save_skills(resume_id):
    _save_repeating_section("skills", resume_id, ["skill_name"])
    return redirect(url_for("form", resume_id=resume_id))


@app.route("/form/<int:resume_id>/projects", methods=["POST"])
def save_projects(resume_id):
    _save_repeating_section("projects", resume_id, ["title", "description", "tech_used", "link"])
    return redirect(url_for("form", resume_id=resume_id))


@app.route("/form/<int:resume_id>/experience", methods=["POST"])
def save_experience(resume_id):
    _save_repeating_section("experience", resume_id, ["company", "role", "duration", "description"])
    return redirect(url_for("form", resume_id=resume_id))


@app.route("/form/<int:resume_id>/certifications", methods=["POST"])
def save_certifications(resume_id):
    _save_repeating_section("certifications", resume_id, ["name", "issuer", "year"])
    return redirect(url_for("form", resume_id=resume_id))


@app.route("/form/<int:resume_id>/achievements", methods=["POST"])
def save_achievements(resume_id):
    _save_repeating_section("achievements", resume_id, ["description"])
    return redirect(url_for("form", resume_id=resume_id))


# ===========================================================================
# Module 4: Preview Resume
# ===========================================================================

@app.route("/preview/<int:resume_id>")
def preview(resume_id):
    data = db.get_resume_data(resume_id)
    return render_template("preview.html", resume_id=resume_id, data=data)


# --- Edit / Delete ---

@app.route("/edit/<int:resume_id>")
def edit_resume(resume_id):
    return redirect(url_for("form", resume_id=resume_id))


@app.route("/delete/<int:resume_id>", methods=["POST"])
def delete_resume_route(resume_id):
    db.delete_resume(resume_id)
    flash("Resume deleted.")
    return redirect(url_for("home"))


# ===========================================================================
# Module 5 + 6: Generate PDF -> Download Resume
# ===========================================================================

@app.route("/download/<int:resume_id>")
def download(resume_id):
    data = db.get_resume_data(resume_id)
    file_path = pdf_generator.generate_resume_pdf(resume_id, data)
    return send_file(file_path, as_attachment=True, download_name=f"resume_{resume_id}.pdf")


if __name__ == "__main__":
    app.run(debug=True)
