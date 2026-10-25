import sqlite3
import hashlib
import secrets
import json
from pathlib import Path
from typing import Optional, List, Dict, Any


# =========================================================
# DATABASE CONFIGURATION
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"

DB_PATH = DATA_DIR / "resume_agent.db"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_connection():
    """
    Create and return a SQLite database connection.
    """

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = sqlite3.connect(
        str(DB_PATH)
    )

    connection.row_factory = sqlite3.Row

    return connection


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

def init_database():
    """
    Create all required database tables.
    """

    connection = get_connection()

    cursor = connection.cursor()

    # -----------------------------------------------------
    # USERS
    # -----------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # -----------------------------------------------------
    # RESUMES
    # -----------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            filename TEXT NOT NULL,
            resume_text TEXT NOT NULL,
            extracted_name TEXT,
            email TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )

    # -----------------------------------------------------
    # JOBS
    # -----------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            job_title TEXT,
            company TEXT,
            job_description TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )

    # -----------------------------------------------------
    # SKILLS
    # -----------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_name TEXT NOT NULL UNIQUE,
            category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # -----------------------------------------------------
    # RESUME SKILLS
    # -----------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS resume_skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resume_id INTEGER NOT NULL,
            skill_name TEXT NOT NULL,
            proficiency TEXT,
            FOREIGN KEY (resume_id) REFERENCES resumes(id)
        )
        """
    )

    # -----------------------------------------------------
    # JOB SKILLS
    # -----------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS job_skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            skill_name TEXT NOT NULL,
            importance TEXT,
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        )
        """
    )

    # -----------------------------------------------------
    # SKILL GAP ANALYSIS
    # -----------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS skill_gap_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resume_id INTEGER NOT NULL,
            job_id INTEGER NOT NULL,
            matched_skills TEXT,
            missing_skills TEXT,
            match_percentage REAL,
            analysis TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (resume_id) REFERENCES resumes(id),
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        )
        """
    )

    # -----------------------------------------------------
    # LEARNING ROADMAP
    # -----------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS learning_roadmaps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resume_id INTEGER NOT NULL,
            job_id INTEGER NOT NULL,
            roadmap TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (resume_id) REFERENCES resumes(id),
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        )
        """
    )

    connection.commit()

    connection.close()


# =========================================================
# PASSWORD HASHING
# =========================================================

def hash_password(
    password: str,
    salt: Optional[str] = None
):
    """
    Hash a password using PBKDF2-HMAC-SHA256.
    """

    if salt is None:
        salt = secrets.token_hex(16)

    password_bytes = password.encode(
        "utf-8"
    )

    salt_bytes = salt.encode(
        "utf-8"
    )

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password_bytes,
        salt_bytes,
        100_000
    )

    return (
        password_hash.hex(),
        salt
    )


def verify_password(
    password: str,
    stored_hash: str,
    salt: str
) -> bool:
    """
    Verify a password against its stored hash.
    """

    password_hash, _ = hash_password(
        password,
        salt
    )

    return secrets.compare_digest(
        password_hash,
        stored_hash
    )


# =========================================================
# USER REGISTRATION
# =========================================================

def register_user(
    username: str,
    email: str,
    password: str
) -> Dict[str, Any]:
    """
    Register a new user.
    """

    username = username.strip()

    email = email.strip().lower()

    if not username:
        return {
            "success": False,
            "message": "Username is required."
        }

    if not email:
        return {
            "success": False,
            "message": "Email is required."
        }

    if len(password) < 6:
        return {
            "success": False,
            "message": (
                "Password must contain at least "
                "6 characters."
            )
        }

    connection = get_connection()

    cursor = connection.cursor()

    # -----------------------------------------------------
    # Check username
    # -----------------------------------------------------

    cursor.execute(
        """
        SELECT id
        FROM users
        WHERE username = ?
        """,
        (username,)
    )

    if cursor.fetchone():

        connection.close()

        return {
            "success": False,
            "message": "Username already exists."
        }

    # -----------------------------------------------------
    # Check email
    # -----------------------------------------------------

    cursor.execute(
        """
        SELECT id
        FROM users
        WHERE email = ?
        """,
        (email,)
    )

    if cursor.fetchone():

        connection.close()

        return {
            "success": False,
            "message": "Email is already registered."
        }

    # -----------------------------------------------------
    # Hash password
    # -----------------------------------------------------

    password_hash, salt = hash_password(
        password
    )

    # -----------------------------------------------------
    # Insert user
    # -----------------------------------------------------

    cursor.execute(
        """
        INSERT INTO users (
            username,
            email,
            password_hash,
            salt
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            username,
            email,
            password_hash,
            salt
        )
    )

    user_id = cursor.lastrowid

    connection.commit()

    connection.close()

    return {
        "success": True,
        "message": "Registration successful.",
        "user_id": user_id
    }


# =========================================================
# USER LOGIN
# =========================================================

def authenticate_user(
    username_or_email: str,
    password: str
) -> Optional[Dict[str, Any]]:
    """
    Authenticate using username or email.
    """

    username_or_email = (
        username_or_email.strip()
    )

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE username = ?
        OR email = ?
        """,
        (
            username_or_email,
            username_or_email.lower()
        )
    )

    user = cursor.fetchone()

    connection.close()

    if user is None:
        return None

    valid_password = verify_password(
        password,
        user["password_hash"],
        user["salt"]
    )

    if not valid_password:
        return None

    return {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "created_at": user["created_at"]
    }


def login_user(
    username: str,
    password: str
) -> Optional[Dict[str, Any]]:
    """
    Compatibility function used by app.py.
    """

    return authenticate_user(
        username,
        password
    )


# =========================================================
# GET USER
# =========================================================

def get_user(
    user_id: int
) -> Optional[Dict[str, Any]]:

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            username,
            email,
            created_at
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    )

    user = cursor.fetchone()

    connection.close()

    return (
        dict(user)
        if user
        else None
    )


# =========================================================
# GENERIC INSERT
# =========================================================

def insert_record(
    table: str,
    data: Dict[str, Any]
) -> int:

    connection = get_connection()

    cursor = connection.cursor()

    columns = ", ".join(
        data.keys()
    )

    placeholders = ", ".join(
        ["?"] * len(data)
    )

    query = f"""
        INSERT INTO {table}
        ({columns})
        VALUES ({placeholders})
    """

    cursor.execute(
        query,
        tuple(data.values())
    )

    record_id = cursor.lastrowid

    connection.commit()

    connection.close()

    return record_id


# =========================================================
# RESUME FUNCTIONS
# =========================================================

def save_resume(
    filename: str,
    resume_text: str,
    extracted_name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    user_id: Optional[int] = None
) -> int:

    return insert_record(
        "resumes",
        {
            "user_id": user_id,
            "filename": filename,
            "resume_text": resume_text,
            "extracted_name": extracted_name,
            "email": email,
            "phone": phone
        }
    )


def get_resume(
    resume_id: int
) -> Optional[Dict[str, Any]]:

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM resumes
        WHERE id = ?
        """,
        (resume_id,)
    )

    row = cursor.fetchone()

    connection.close()

    return (
        dict(row)
        if row
        else None
    )


def get_all_resumes(
    user_id: Optional[int] = None
) -> List[Dict[str, Any]]:

    connection = get_connection()

    cursor = connection.cursor()

    if user_id is not None:

        cursor.execute(
            """
            SELECT *
            FROM resumes
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,)
        )

    else:

        cursor.execute(
            """
            SELECT *
            FROM resumes
            ORDER BY created_at DESC
            """
        )

    rows = cursor.fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]


# =========================================================
# JOB FUNCTIONS
# =========================================================

def save_job(
    job_title: str,
    company: str,
    job_description: str,
    user_id: Optional[int] = None
) -> int:

    return insert_record(
        "jobs",
        {
            "user_id": user_id,
            "job_title": job_title,
            "company": company,
            "job_description": job_description
        }
    )


def get_job(
    job_id: int
) -> Optional[Dict[str, Any]]:

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM jobs
        WHERE id = ?
        """,
        (job_id,)
    )

    row = cursor.fetchone()

    connection.close()

    return (
        dict(row)
        if row
        else None
    )


def get_all_jobs(
    user_id: Optional[int] = None
) -> List[Dict[str, Any]]:

    connection = get_connection()

    cursor = connection.cursor()

    if user_id is not None:

        cursor.execute(
            """
            SELECT *
            FROM jobs
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,)
        )

    else:

        cursor.execute(
            """
            SELECT *
            FROM jobs
            ORDER BY created_at DESC
            """
        )

    rows = cursor.fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]


# =========================================================
# SKILL FUNCTIONS
# =========================================================

def save_skill(
    skill_name: str,
    category: Optional[str] = None
) -> int:

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO skills
        (skill_name, category)
        VALUES (?, ?)
        """,
        (
            skill_name,
            category
        )
    )

    connection.commit()

    cursor.execute(
        """
        SELECT id
        FROM skills
        WHERE skill_name = ?
        """,
        (skill_name,)
    )

    row = cursor.fetchone()

    connection.close()

    return row["id"]


def get_all_skills() -> List[Dict[str, Any]]:

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM skills
        ORDER BY skill_name
        """
    )

    rows = cursor.fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]


# =========================================================
# RESUME SKILLS
# =========================================================

def save_resume_skill(
    resume_id: int,
    skill_name: str,
    proficiency: Optional[str] = None
) -> int:

    return insert_record(
        "resume_skills",
        {
            "resume_id": resume_id,
            "skill_name": skill_name,
            "proficiency": proficiency
        }
    )


def get_resume_skills(
    resume_id: int
) -> List[Dict[str, Any]]:

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM resume_skills
        WHERE resume_id = ?
        """,
        (resume_id,)
    )

    rows = cursor.fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]


# =========================================================
# JOB SKILLS
# =========================================================

def save_job_skill(
    job_id: int,
    skill_name: str,
    importance: Optional[str] = None
) -> int:

    return insert_record(
        "job_skills",
        {
            "job_id": job_id,
            "skill_name": skill_name,
            "importance": importance
        }
    )


def get_job_skills(
    job_id: int
) -> List[Dict[str, Any]]:

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM job_skills
        WHERE job_id = ?
        """,
        (job_id,)
    )

    rows = cursor.fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]


# =========================================================
# SKILL GAP ANALYSIS
# =========================================================

def save_skill_gap_analysis(
    resume_id: int,
    job_id: int,
    matched_skills: str,
    missing_skills: str,
    match_percentage: float,
    analysis: str
) -> int:

    return insert_record(
        "skill_gap_analysis",
        {
            "resume_id": resume_id,
            "job_id": job_id,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "match_percentage": match_percentage,
            "analysis": analysis
        }
    )


def get_skill_gap_analysis(
    resume_id: int,
    job_id: int
) -> Optional[Dict[str, Any]]:

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM skill_gap_analysis
        WHERE resume_id = ?
        AND job_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (
            resume_id,
            job_id
        )
    )

    row = cursor.fetchone()

    connection.close()

    return (
        dict(row)
        if row
        else None
    )


# =========================================================
# LEARNING ROADMAP
# =========================================================

def save_learning_roadmap(
    resume_id: int,
    job_id: int,
    roadmap: str
) -> int:

    return insert_record(
        "learning_roadmaps",
        {
            "resume_id": resume_id,
            "job_id": job_id,
            "roadmap": roadmap
        }
    )


def get_learning_roadmap(
    resume_id: int,
    job_id: int
) -> Optional[Dict[str, Any]]:

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM learning_roadmaps
        WHERE resume_id = ?
        AND job_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (
            resume_id,
            job_id
        )
    )

    row = cursor.fetchone()

    connection.close()

    return (
        dict(row)
        if row
        else None
    )


# =========================================================
# SAVE COMPLETE AI ANALYSIS
# =========================================================

def save_analysis(
    user_id: int,
    job_title: str,
    company_name: str,
    result: Dict[str, Any]
) -> int:
    """
    Save a complete AI analysis and connect it
    to the logged-in user.
    """

    # -----------------------------------------------------
    # Extract resume text if available
    # -----------------------------------------------------

    resume_text = result.get(
        "_resume_text",
        "AI analyzed resume"
    )

    if not isinstance(
        resume_text,
        str
    ):
        resume_text = "AI analyzed resume"

    # -----------------------------------------------------
    # Create resume record
    # -----------------------------------------------------

    resume_id = save_resume(
        filename="AI_Resume_Analysis",
        resume_text=resume_text,
        user_id=user_id
    )

    # -----------------------------------------------------
    # Create job record
    # -----------------------------------------------------

    job_id = save_job(
        job_title=job_title or "Target Role",
        company=company_name or "",
        job_description="AI Resume Skill Gap Analysis",
        user_id=user_id
    )

    # -----------------------------------------------------
    # Extract skill-gap section
    # -----------------------------------------------------

    skill_gap = result.get(
        "skill_gap",
        {}
    )

    if not isinstance(
        skill_gap,
        dict
    ):
        skill_gap = {}

    if isinstance(
        skill_gap.get("data"),
        dict
    ):
        skill_gap = skill_gap["data"]

    matched_skills = skill_gap.get(
        "matched_skills",
        []
    )

    missing_skills = skill_gap.get(
        "missing_skills",
        []
    )

    match_percentage = skill_gap.get(
        "match_percentage",
        0
    )

    # -----------------------------------------------------
    # Normalize values
    # -----------------------------------------------------

    if not isinstance(
        matched_skills,
        list
    ):
        matched_skills = [
            str(matched_skills)
        ]

    if not isinstance(
        missing_skills,
        list
    ):
        missing_skills = [
            str(missing_skills)
        ]

    try:
        match_percentage = float(
            match_percentage or 0
        )
    except (
        ValueError,
        TypeError
    ):
        match_percentage = 0.0

    # -----------------------------------------------------
    # Convert complete result to JSON
    # -----------------------------------------------------

    analysis_text = json.dumps(
        result,
        indent=2,
        ensure_ascii=False,
        default=str
    )

    # -----------------------------------------------------
    # Save analysis
    # -----------------------------------------------------

    analysis_id = save_skill_gap_analysis(
        resume_id=resume_id,
        job_id=job_id,
        matched_skills=json.dumps(
            matched_skills,
            ensure_ascii=False
        ),
        missing_skills=json.dumps(
            missing_skills,
            ensure_ascii=False
        ),
        match_percentage=match_percentage,
        analysis=analysis_text
    )

    return analysis_id


# =========================================================
# GET USER ANALYSIS HISTORY
# =========================================================

def get_user_analyses(
    user_id: int
) -> List[Dict[str, Any]]:
    """
    Return all analysis records belonging to a user.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            sga.id,
            sga.match_percentage,
            sga.analysis,
            sga.created_at,
            j.job_title,
            j.company,
            r.filename
        FROM skill_gap_analysis AS sga

        INNER JOIN resumes AS r
            ON sga.resume_id = r.id

        INNER JOIN jobs AS j
            ON sga.job_id = j.id

        WHERE r.user_id = ?

        ORDER BY sga.created_at DESC
        """,
        (user_id,)
    )

    rows = cursor.fetchall()

    connection.close()

    results = []

    for row in rows:

        analysis = row["analysis"]

        try:
            analysis = json.loads(
                analysis
            )

        except (
            json.JSONDecodeError,
            TypeError
        ):
            analysis = {}

        results.append(
            {
                "id": row["id"],
                "job_title": row["job_title"],
                "company_name": row["company"],
                "created_at": row["created_at"],
                "match_percentage": row[
                    "match_percentage"
                ],
                "filename": row["filename"],
                "result": analysis
            }
        )

    return results


# =========================================================
# DATABASE STATISTICS
# =========================================================

def get_statistics() -> Dict[str, int]:

    connection = get_connection()

    cursor = connection.cursor()

    tables = [
        "users",
        "resumes",
        "jobs",
        "skills",
        "skill_gap_analysis",
        "learning_roadmaps"
    ]

    statistics = {}

    for table in tables:

        cursor.execute(
            f"""
            SELECT COUNT(*) AS count
            FROM {table}
            """
        )

        row = cursor.fetchone()

        statistics[table] = row["count"]

    connection.close()

    return statistics


# =========================================================
# INITIALIZE DATABASE WHEN RUN DIRECTLY
# =========================================================

if __name__ == "__main__":

    init_database()

    print(
        "Database initialized successfully."
    )

    print(
        f"Database location: {DB_PATH}"
    )

    print(
        "\nDatabase statistics:"
    )

    statistics = get_statistics()

    for table, count in statistics.items():

        print(
            f"{table}: {count}"
        )

