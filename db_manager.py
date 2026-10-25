import sqlite3
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


# =========================================================
# DATABASE CONFIGURATION
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"

DATA_DIR.mkdir(
    parents=True,
    exist_ok=True
)

DATABASE_PATH = DATA_DIR / "resume_agent.db"


# =========================================================
# DATABASE MANAGER
# =========================================================

class DatabaseManager:
    """
    Central SQLite database manager.
    """

    def __init__(
        self,
        database_path: str = str(DATABASE_PATH)
    ):

        self.database_path = database_path

        self.initialize_database()


    # =====================================================
    # CONNECTION
    # =====================================================

    def get_connection(
        self
    ) -> sqlite3.Connection:
        """
        Create a SQLite connection.
        """

        connection = sqlite3.connect(
            self.database_path,
            check_same_thread=False
        )

        connection.row_factory = sqlite3.Row

        connection.execute(
            "PRAGMA foreign_keys = ON"
        )

        return connection


    # =====================================================
    # INITIALIZE DATABASE
    # =====================================================

    def initialize_database(
        self
    ):
        """
        Create all required tables.
        """

        connection = self.get_connection()

        cursor = connection.cursor()

        # -------------------------------------------------
        # USERS
        # -------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                username TEXT UNIQUE NOT NULL,

                email TEXT UNIQUE NOT NULL,

                password_hash TEXT NOT NULL,

                full_name TEXT,

                created_at TEXT NOT NULL,

                last_login TEXT

            )
            """
        )

        # -------------------------------------------------
        # RESUMES
        # -------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS resumes (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                file_name TEXT,

                resume_text TEXT,

                target_role TEXT,

                created_at TEXT NOT NULL,

                FOREIGN KEY (
                    user_id
                )
                REFERENCES users(id)

                ON DELETE CASCADE

            )
            """
        )

        # -------------------------------------------------
        # JOB DESCRIPTIONS
        # -------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS job_descriptions (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                job_title TEXT,

                company_name TEXT,

                job_text TEXT,

                created_at TEXT NOT NULL,

                FOREIGN KEY (
                    user_id
                )
                REFERENCES users(id)

                ON DELETE CASCADE

            )
            """
        )

        # -------------------------------------------------
        # ANALYSES
        # -------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS analyses (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                resume_id INTEGER,

                job_id INTEGER,

                analysis_type TEXT NOT NULL,

                result_json TEXT,

                created_at TEXT NOT NULL,

                FOREIGN KEY (
                    user_id
                )
                REFERENCES users(id)

                ON DELETE CASCADE,

                FOREIGN KEY (
                    resume_id
                )
                REFERENCES resumes(id)

                ON DELETE SET NULL,

                FOREIGN KEY (
                    job_id
                )
                REFERENCES job_descriptions(id)

                ON DELETE SET NULL

            )
            """
        )

        # -------------------------------------------------
        # SKILL GAPS
        # -------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS skill_gaps (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                resume_id INTEGER,

                job_id INTEGER,

                match_percentage REAL DEFAULT 0,

                matched_skills TEXT,

                partial_skills TEXT,

                missing_skills TEXT,

                analysis_json TEXT,

                created_at TEXT NOT NULL,

                FOREIGN KEY (
                    user_id
                )
                REFERENCES users(id)

                ON DELETE CASCADE,

                FOREIGN KEY (
                    resume_id
                )
                REFERENCES resumes(id)

                ON DELETE SET NULL,

                FOREIGN KEY (
                    job_id
                )
                REFERENCES job_descriptions(id)

                ON DELETE SET NULL

            )
            """
        )

        # -------------------------------------------------
        # ROADMAPS
        # -------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS roadmaps (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                skill_gap_id INTEGER,

                target_role TEXT,

                roadmap_json TEXT,

                created_at TEXT NOT NULL,

                FOREIGN KEY (
                    user_id
                )
                REFERENCES users(id)

                ON DELETE CASCADE,

                FOREIGN KEY (
                    skill_gap_id
                )
                REFERENCES skill_gaps(id)

                ON DELETE SET NULL

            )
            """
        )

        # -------------------------------------------------
        # REPORTS
        # -------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                resume_id INTEGER,

                report_name TEXT,

                file_path TEXT,

                created_at TEXT NOT NULL,

                FOREIGN KEY (
                    user_id
                )
                REFERENCES users(id)

                ON DELETE CASCADE,

                FOREIGN KEY (
                    resume_id
                )
                REFERENCES resumes(id)

                ON DELETE SET NULL

            )
            """
        )

        connection.commit()

        connection.close()


    # =====================================================
    # PASSWORD HASH
    # =====================================================

    @staticmethod
    def hash_password(
        password: str
    ) -> str:
        """
        Hash a password using SHA-256.

        Note:
        For a production application, use a dedicated
        password hashing algorithm such as bcrypt or Argon2.
        """

        return hashlib.sha256(
            password.encode(
                "utf-8"
            )
        ).hexdigest()


    # =====================================================
    # CREATE USER
    # =====================================================

    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        full_name: str = ""
    ) -> Dict[str, Any]:
        """
        Register a new user.
        """

        username = username.strip()

        email = email.strip().lower()

        full_name = full_name.strip()

        if not username:

            return {
                "success": False,
                "error": "Username is required."
            }

        if not email:

            return {
                "success": False,
                "error": "Email is required."
            }

        if not password:

            return {
                "success": False,
                "error": "Password is required."
            }

        connection = self.get_connection()

        cursor = connection.cursor()

        try:

            password_hash = self.hash_password(
                password
            )

            created_at = datetime.now().isoformat(
                timespec="seconds"
            )

            cursor.execute(
                """
                INSERT INTO users (
                    username,
                    email,
                    password_hash,
                    full_name,
                    created_at
                )

                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    username,
                    email,
                    password_hash,
                    full_name,
                    created_at
                )
            )

            connection.commit()

            user_id = cursor.lastrowid

            return {
                "success": True,
                "user_id": user_id,
                "message": "Registration successful."
            }

        except sqlite3.IntegrityError as error:

            error_message = str(
                error
            ).lower()

            if "username" in error_message:

                message = (
                    "Username already exists."
                )

            elif "email" in error_message:

                message = (
                    "Email already exists."
                )

            else:

                message = (
                    "User already exists."
                )

            return {
                "success": False,
                "error": message
            }

        finally:

            connection.close()


    # =====================================================
    # AUTHENTICATE USER
    # =====================================================

    def authenticate_user(
        self,
        username_or_email: str,
        password: str
    ) -> Optional[Dict[str, Any]]:
        """
        Authenticate a user using username or email.
        """

        username_or_email = (
            username_or_email.strip()
        )

        password_hash = self.hash_password(
            password
        )

        connection = self.get_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE
                (
                    username = ?
                    OR email = ?
                )
                AND password_hash = ?
            """,
            (
                username_or_email,
                username_or_email.lower(),
                password_hash
            )
        )

        row = cursor.fetchone()

        if not row:

            connection.close()

            return None

        last_login = datetime.now().isoformat(
            timespec="seconds"
        )

        cursor.execute(
            """
            UPDATE users
            SET last_login = ?
            WHERE id = ?
            """,
            (
                last_login,
                row["id"]
            )
        )

        connection.commit()

        user = dict(
            row
        )

        user.pop(
            "password_hash",
            None
        )

        connection.close()

        return user


    # =====================================================
    # GET USER
    # =====================================================

    def get_user(
        self,
        user_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get user by ID.
        """

        connection = self.get_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                username,
                email,
                full_name,
                created_at,
                last_login
            FROM users
            WHERE id = ?
            """,
            (
                user_id,
            )
        )

        row = cursor.fetchone()

        connection.close()

        if row:

            return dict(
                row
            )

        return None


    # =====================================================
    # SAVE RESUME
    # =====================================================

    def save_resume(
        self,
        user_id: int,
        file_name: str,
        resume_text: str,
        target_role: str = ""
    ) -> int:
        """
        Save uploaded resume.
        """

        connection = self.get_connection()

        cursor = connection.cursor()

        created_at = datetime.now().isoformat(
            timespec="seconds"
        )

        cursor.execute(
            """
            INSERT INTO resumes (
                user_id,
                file_name,
                resume_text,
                target_role,
                created_at
            )

            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                file_name,
                resume_text,
                target_role,
                created_at
            )
        )

        connection.commit()

        resume_id = cursor.lastrowid

        connection.close()

        return resume_id


    # =====================================================
    # GET RESUME
    # =====================================================

    def get_resume(
        self,
        resume_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get resume by ID.
        """

        connection = self.get_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM resumes
            WHERE id = ?
            """,
            (
                resume_id,
            )
        )

        row = cursor.fetchone()

        connection.close()

        if row:

            return dict(
                row
            )

        return None


    # =====================================================
    # GET USER RESUMES
    # =====================================================

    def get_user_resumes(
        self,
        user_id: int
    ) -> List[Dict[str, Any]]:
        """
        Get all resumes belonging to a user.
        """

        connection = self.get_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM resumes
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (
                user_id,
            )
        )

        rows = cursor.fetchall()

        connection.close()

        return [
            dict(row)
            for row in rows
        ]


    # =====================================================
    # SAVE JOB DESCRIPTION
    # =====================================================

    def save_job_description(
        self,
        user_id: int,
        job_title: str,
        job_text: str,
        company_name: str = ""
    ) -> int:
        """
        Save a target job description.
        """

        connection = self.get_connection()

        cursor = connection.cursor()

        created_at = datetime.now().isoformat(
            timespec="seconds"
        )

        cursor.execute(
            """
            INSERT INTO job_descriptions (
                user_id,
                job_title,
                company_name,
                job_text,
                created_at
            )

            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                job_title,
                company_name,
                job_text,
                created_at
            )
        )

        connection.commit()

        job_id = cursor.lastrowid

        connection.close()

        return job_id


    # =====================================================
    # GET JOB
    # =====================================================

    def get_job(
        self,
        job_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get job description.
        """

        connection = self.get_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM job_descriptions
            WHERE id = ?
            """,
            (
                job_id,
            )
        )

        row = cursor.fetchone()

        connection.close()

        if row:

            return dict(
                row
            )

        return None


    # =====================================================
    # SAVE ANALYSIS
    # =====================================================

    def save_analysis(
        self,
        user_id: int,
        analysis_type: str,
        result: Dict[str, Any],
        resume_id: Optional[int] = None,
        job_id: Optional[int] = None
    ) -> int:
        """
        Save an AI analysis result.
        """

        connection = self.get_connection()

        cursor = connection.cursor()

        created_at = datetime.now().isoformat(
            timespec="seconds"
        )

        result_json = json.dumps(
            result,
            ensure_ascii=False
        )

        cursor.execute(
            """
            INSERT INTO analyses (
                user_id,
                resume_id,
                job_id,
                analysis_type,
                result_json,
                created_at
            )

            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                resume_id,
                job_id,
                analysis_type,
                result_json,
                created_at
            )
        )

        connection.commit()

        analysis_id = cursor.lastrowid

        connection.close()

        return analysis_id


    # =====================================================
    # GET ANALYSES
    # =====================================================

    def get_user_analyses(
        self,
        user_id: int,
        analysis_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get user's saved analyses.
        """

        connection = self.get_connection()

        cursor = connection.cursor()

        if analysis_type:

            cursor.execute(
                """
                SELECT *
                FROM analyses
                WHERE
                    user_id = ?
                    AND analysis_type = ?
                ORDER BY created_at DESC
                """,
                (
                    user_id,
                    analysis_type
                )
            )

        else:

            cursor.execute(
                """
                SELECT *
                FROM analyses
                WHERE user_id = ?
                ORDER BY created_at DESC
                """,
                (
                    user_id,
                )
            )

        rows = cursor.fetchall()

        connection.close()

        results = []

        for row in rows:

            item = dict(
                row
            )

            try:

                item["result"] = json.loads(
                    item["result_json"]
                )

            except (
                json.JSONDecodeError,
                TypeError
            ):

                item["result"] = {}

            results.append(
                item
            )

        return results


    # =====================================================
    # SAVE SKILL GAP
    # =====================================================

    def save_skill_gap(
        self,
        user_id: int,
        match_percentage: float,
        matched_skills: List[str],
        missing_skills: List[str],
        partial_skills: Optional[List[str]] = None,
        analysis: Optional[Dict[str, Any]] = None,
        resume_id: Optional[int] = None,
        job_id: Optional[int] = None
    ) -> int:
        """
        Save skill gap analysis.
        """

        connection = self.get_connection()

        cursor = connection.cursor()

        created_at = datetime.now().isoformat(
            timespec="seconds"
        )

        partial_skills = (
            partial_skills or []
        )

        analysis = (
            analysis or {}
        )

        cursor.execute(
            """
            INSERT INTO skill_gaps (
                user_id,
                resume_id,
                job_id,
                match_percentage,
                matched_skills,
                partial_skills,
                missing_skills,
                analysis_json,
                created_at
            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                resume_id,
                job_id,
                float(match_percentage),
                json.dumps(
                    matched_skills
                ),
                json.dumps(
                    partial_skills
                ),
                json.dumps(
                    missing_skills
                ),
                json.dumps(
                    analysis,
                    ensure_ascii=False
                ),
                created_at
            )
        )

        connection.commit()

        skill_gap_id = cursor.lastrowid

        connection.close()

        return skill_gap_id


    # =====================================================
    # GET SKILL GAP
    # =====================================================

    def get_skill_gap(
        self,
        skill_gap_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve skill gap analysis.
        """

        connection = self.get_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM skill_gaps
            WHERE id = ?
            """,
            (
                skill_gap_id,
            )
        )

        row = cursor.fetchone()

        connection.close()

        if not row:

            return None

        result = dict(
            row
        )

        result[
            "matched_skills"
        ] = json_load_list(
            result.get(
                "matched_skills"
            )
        )

        result[
            "partial_skills"
        ] = json_load_list(
            result.get(
                "partial_skills"
            )
        )

        result[
            "missing_skills"
        ] = json_load_list(
            result.get(
                "missing_skills"
            )
        )

        result[
            "analysis"
        ] = json_load_dict(
            result.get(
                "analysis_json"
            )
        )

        return result


    # =====================================================
    # GET USER SKILL GAPS
    # =====================================================

    def get_user_skill_gaps(
        self,
        user_id: int
    ) -> List[Dict[str, Any]]:
        """
        Get all skill gap analyses for a user.
        """

        connection = self.get_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM skill_gaps
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (
                user_id,
            )
        )

        rows = cursor.fetchall()

        connection.close()

        results = []

        for row in rows:

            result = dict(
                row
            )

            result[
                "matched_skills"
            ] = json_load_list(
                result.get(
                    "matched_skills"
                )
            )

            result[
                "partial_skills"
            ] = json_load_list(
                result.get(
                    "partial_skills"
                )
            )

            result[
                "missing_skills"
            ] = json_load_list(
                result.get(
                    "missing_skills"
                )
            )

            results.append(
                result
            )

        return results


    # =====================================================
    # SAVE ROADMAP
    # =====================================================

    def save_roadmap(
        self,
        user_id: int,
        target_role: str,
        roadmap: Dict[str, Any],
        skill_gap_id: Optional[int] = None
    ) -> int:
        """
        Save personalized learning roadmap.
        """

        connection = self.get_connection()

        cursor = connection.cursor()

        created_at = datetime.now().isoformat(
            timespec="seconds"
        )

        roadmap_json = json.dumps(
            roadmap,
            ensure_ascii=False
        )

        cursor.execute(
            """
            INSERT INTO roadmaps (
                user_id,
                skill_gap_id,
                target_role,
                roadmap_json,
                created_at
            )

            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                skill_gap_id,
                target_role,
                roadmap_json,
                created_at
            )
        )

        connection.commit()

        roadmap_id = cursor.lastrowid

        connection.close()

        return roadmap_id


    # =====================================================
    # GET ROADMAP
    # =====================================================

    def get_roadmap(
        self,
        roadmap_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve roadmap.
        """

        connection = self.get_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM roadmaps
            WHERE id = ?
            """,
            (
                roadmap_id,
            )
        )

        row = cursor.fetchone()

        connection.close()

        if not row:

            return None

        result = dict(
            row
        )

        result[
            "roadmap"
        ] = json_load_dict(
            result.get(
                "roadmap_json"
            )
        )

        return result


    # =====================================================
    # GET USER ROADMAPS
    # =====================================================

    def get_user_roadmaps(
        self,
        user_id: int
    ) -> List[Dict[str, Any]]:
        """
        Get all roadmaps for a user.
        """

        connection = self.get_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM roadmaps
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (
                user_id,
            )
        )

        rows = cursor.fetchall()

        connection.close()

        results = []

        for row in rows:

            result = dict(
                row
            )

            result[
                "roadmap"
            ] = json_load_dict(
                result.get(
                    "roadmap_json"
                )
            )

            results.append(
                result
            )

        return results


    # =====================================================
    # SAVE REPORT
    # =====================================================

    def save_report(
        self,
        user_id: int,
        report_name: str,
        file_path: str,
        resume_id: Optional[int] = None
    ) -> int:
        """
        Save generated report metadata.
        """

        connection = self.get_connection()

        cursor = connection.cursor()

        created_at = datetime.now().isoformat(
            timespec="seconds"
        )

        cursor.execute(
            """
            INSERT INTO reports (
                user_id,
                resume_id,
                report_name,
                file_path,
                created_at
            )

            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                resume_id,
                report_name,
                file_path,
                created_at
            )
        )

        connection.commit()

        report_id = cursor.lastrowid

        connection.close()

        return report_id


    # =====================================================
    # GET REPORTS
    # =====================================================

    def get_user_reports(
        self,
        user_id: int
    ) -> List[Dict[str, Any]]:
        """
        Get report history for a user.
        """

        connection = self.get_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM reports
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (
                user_id,
            )
        )

        rows = cursor.fetchall()

        connection.close()

        return [
            dict(row)
            for row in rows
        ]


    # =====================================================
    # DASHBOARD STATISTICS
    # =====================================================

    def get_dashboard_stats(
        self,
        user_id: int
    ) -> Dict[str, int]:
        """
        Return dashboard statistics.
        """

        connection = self.get_connection()

        cursor = connection.cursor()

        # -------------------------------------------------
        # Resumes
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM resumes
            WHERE user_id = ?
            """,
            (
                user_id,
            )
        )

        resume_count = cursor.fetchone()[0]

        # -------------------------------------------------
        # Analyses
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM analyses
            WHERE user_id = ?
            """,
            (
                user_id,
            )
        )

        analysis_count = cursor.fetchone()[0]

        # -------------------------------------------------
        # Skill gaps
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM skill_gaps
            WHERE user_id = ?
            """,
            (
                user_id,
            )
        )

        skill_gap_count = cursor.fetchone()[0]

        # -------------------------------------------------
        # Roadmaps
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM roadmaps
            WHERE user_id = ?
            """,
            (
                user_id,
            )
        )

        roadmap_count = cursor.fetchone()[0]

        # -------------------------------------------------
        # Reports
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM reports
            WHERE user_id = ?
            """,
            (
                user_id,
            )
        )

        report_count = cursor.fetchone()[0]

        connection.close()

        return {

            "resumes": resume_count,

            "analyses": analysis_count,

            "skill_gaps": skill_gap_count,

            "roadmaps": roadmap_count,

            "reports": report_count
        }


    # =====================================================
    # DELETE RESUME
    # =====================================================

    def delete_resume(
        self,
        resume_id: int,
        user_id: int
    ) -> bool:
        """
        Delete a resume belonging to the user.
        """

        connection = self.get_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM resumes
            WHERE
                id = ?
                AND user_id = ?
            """,
            (
                resume_id,
                user_id
            )
        )

        connection.commit()

        deleted = (
            cursor.rowcount > 0
        )

        connection.close()

        return deleted


    # =====================================================
    # DELETE REPORT
    # =====================================================

    def delete_report(
        self,
        report_id: int,
        user_id: int
    ) -> bool:
        """
        Delete report metadata.
        """

        connection = self.get_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM reports
            WHERE
                id = ?
                AND user_id = ?
            """,
            (
                report_id,
                user_id
            )
        )

        connection.commit()

        deleted = (
            cursor.rowcount > 0
        )

        connection.close()

        return deleted


# =========================================================
# JSON HELPERS
# =========================================================

def json_load_list(
    value: Any
) -> List[Any]:
    """
    Safely decode JSON list.
    """

    if not value:

        return []

    if isinstance(
        value,
        list
    ):

        return value

    try:

        result = json.loads(
            value
        )

        if isinstance(
            result,
            list
        ):

            return result

    except (
        json.JSONDecodeError,
        TypeError
    ):

        pass

    return []


def json_load_dict(
    value: Any
) -> Dict[str, Any]:
    """
    Safely decode JSON dictionary.
    """

    if not value:

        return {}

    if isinstance(
        value,
        dict
    ):

        return value

    try:

        result = json.loads(
            value
        )

        if isinstance(
            result,
            dict
        ):

            return result

    except (
        json.JSONDecodeError,
        TypeError
    ):

        pass

    return {}


# =========================================================
# SINGLETON DATABASE INSTANCE
# =========================================================

db = DatabaseManager()


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    print("=" * 70)
    print("AI RESUME & SKILL GAP AGENT")
    print("SQLite Database Manager Test")
    print("=" * 70)

    database = DatabaseManager()

    print(
        "\nDatabase:"
    )

    print(
        database.database_path
    )

    # -----------------------------------------------------
    # Create test user
    # -----------------------------------------------------

    print(
        "\nCreating test user..."
    )

    result = database.create_user(
        username="demo_user",
        email="demo@example.com",
        password="demo123",
        full_name="Demo User"
    )

    print(
        result
    )

    # -----------------------------------------------------
    # Login
    # -----------------------------------------------------

    print(
        "\nTesting authentication..."
    )

    user = database.authenticate_user(
        username_or_email="demo_user",
        password="demo123"
    )

    if user:

        print(
            "✅ Authentication successful."
        )

        print(
            user
        )

        user_id = user["id"]

    else:

        print(
            "❌ Authentication failed."
        )

        raise SystemExit

    # -----------------------------------------------------
    # Save resume
    # -----------------------------------------------------

    print(
        "\nSaving resume..."
    )

    resume_id = database.save_resume(
        user_id=user_id,
        file_name="demo_resume.docx",
        resume_text=(
            "Python Developer with experience "
            "in SQL and Machine Learning."
        ),
        target_role="Data Scientist"
    )

    print(
        f"Resume ID: {resume_id}"
    )

    # -----------------------------------------------------
    # Save job
    # -----------------------------------------------------

    print(
        "\nSaving job description..."
    )

    job_id = database.save_job_description(
        user_id=user_id,
        job_title="Data Scientist",
        company_name="Demo Company",
        job_text=(
            "Looking for Python, SQL, "
            "Machine Learning and Statistics."
        )
    )

    print(
        f"Job ID: {job_id}"
    )

    # -----------------------------------------------------
    # Save analysis
    # -----------------------------------------------------

    print(
        "\nSaving analysis..."
    )

    analysis_id = database.save_analysis(
        user_id=user_id,
        analysis_type="resume_analysis",
        result={
            "summary": "Strong Python background.",
            "skills": [
                "Python",
                "SQL"
            ]
        },
        resume_id=resume_id,
        job_id=job_id
    )

    print(
        f"Analysis ID: {analysis_id}"
    )

    # -----------------------------------------------------
    # Save skill gap
    # -----------------------------------------------------

    print(
        "\nSaving skill gap..."
    )

    skill_gap_id = database.save_skill_gap(
        user_id=user_id,
        resume_id=resume_id,
        job_id=job_id,
        match_percentage=66.7,
        matched_skills=[
            "Python",
            "SQL"
        ],
        partial_skills=[
            "Machine Learning"
        ],
        missing_skills=[
            "Statistics",
            "AWS"
        ]
    )

    print(
        f"Skill Gap ID: {skill_gap_id}"
    )

    # -----------------------------------------------------
    # Save roadmap
    # -----------------------------------------------------

    print(
        "\nSaving roadmap..."
    )

    roadmap_id = database.save_roadmap(
        user_id=user_id,
        skill_gap_id=skill_gap_id,
        target_role="Data Scientist",
        roadmap={
            "total_duration": "8 weeks",
            "priority_skills": [
                "Statistics",
                "Machine Learning"
            ]
        }
    )

    print(
        f"Roadmap ID: {roadmap_id}"
    )

    # -----------------------------------------------------
    # Dashboard
    # -----------------------------------------------------

    print(
        "\nDashboard statistics:"
    )

    stats = database.get_dashboard_stats(
        user_id
    )

    for key, value in stats.items():

        print(
            f"  {key}: {value}"
        )

    # -----------------------------------------------------
    # Reports
    # -----------------------------------------------------

    print(
        "\nSaving report metadata..."
    )

    report_id = database.save_report(
        user_id=user_id,
        resume_id=resume_id,
        report_name="Demo Career Report.docx",
        file_path="reports/demo_report.docx"
    )

    print(
        f"Report ID: {report_id}"
    )

    print(
        "\n" + "=" * 70
    )

    print(
        "Database test completed successfully."
    )

    print(
        "=" * 70
    )

