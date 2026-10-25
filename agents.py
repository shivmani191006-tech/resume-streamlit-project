from typing import Any, Dict, List, Optional

from db_manager import DatabaseManager
from resume_parsor import (
    parse_resume,
    extract_sections
)
from ollama_client import OllamaClient


# =========================================================
# AGENT CONFIGURATION
# =========================================================

DEFAULT_MODEL = "llama3.2"


class ResumeAnalysisAgent:
    """Small adapter exposing resume analysis as an agent result."""

    def __init__(self, model: str = DEFAULT_MODEL):
        self.ai = OllamaClient(model=model)

    def run(self, resume_text: str) -> Dict[str, Any]:
        result = self.ai.analyze_resume(resume_text)
        return {
            "success": result.get("success", False),
            "error": result.get("error"),
            "data": result.get("data")
        }


class SkillExtractionAgent:
    """Small adapter exposing skill extraction as an agent result."""

    def __init__(self, model: str = DEFAULT_MODEL):
        self.ai = OllamaClient(model=model)

    def run(self, resume_text: str) -> Dict[str, Any]:
        result = self.ai.extract_skills(resume_text)
        return {
            "success": result.get("success", False),
            "error": result.get("error"),
            "data": result.get("data")
        }


def flatten_skill_result(value: Any) -> List[str]:
    """Flatten nested skill categories into a unique list of strings."""

    flattened: List[str] = []

    def visit(item: Any) -> None:
        if isinstance(item, str):
            cleaned = item.strip()
            if cleaned:
                flattened.append(cleaned)
        elif isinstance(item, dict):
            for nested in item.values():
                visit(nested)
        elif isinstance(item, (list, tuple, set)):
            for nested in item:
                visit(nested)

    visit(value)
    return list(dict.fromkeys(flattened))


# =========================================================
# AGENT CLASS
# =========================================================

class ResumeSkillGapAgent:
    """
    Main agent for AI-powered resume and
    skill-gap analysis.
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        database: Optional[DatabaseManager] = None
    ):

        self.model = model

        self.db = (
            database
            if database is not None
            else DatabaseManager()
        )

        self.ai = OllamaClient(
            model=model
        )


    # =====================================================
    # AGENT STATUS
    # =====================================================

    def get_status(self) -> Dict[str, Any]:
        """
        Check the status of the AI agent.
        """

        ollama_status = (
            self.ai.check_connection()
        )

        model_available = False

        if ollama_status["success"]:

            model_available = (
                self.ai.model_exists(
                    self.model
                )
            )

        return {
            "agent": "Resume & Skill Gap Agent",
            "model": self.model,
            "ollama_connected": (
                ollama_status["success"]
            ),
            "model_available": model_available,
            "installed_models": (
                ollama_status.get(
                    "models",
                    []
                )
            )
        }


    # =====================================================
    # PARSE RESUME
    # =====================================================

    def parse_resume_file(
        self,
        file_name: str,
        file_bytes: bytes
    ) -> Dict[str, Any]:
        """
        Parse an uploaded resume file.
        """

        result = parse_resume(
            file_name=file_name,
            file_bytes=file_bytes
        )

        if not result["success"]:

            return {
                "success": False,
                "stage": "resume_parsing",
                "error": result.get(
                    "error",
                    "Resume parsing failed."
                )
            }

        sections = extract_sections(
            result["text"]
        )

        result["sections"] = sections

        return result


    # =====================================================
    # SAVE RESUME
    # =====================================================

    def save_resume(
        self,
        user_id: int,
        parsed_resume: Dict[str, Any],
        target_role: str = ""
    ) -> int:
        """
        Save parsed resume in SQLite.
        """

        if not parsed_resume.get(
            "success"
        ):

            raise ValueError(
                "Cannot save an invalid resume."
            )

        resume_id = self.db.save_resume(
            user_id=user_id,
            file_name=parsed_resume[
                "file_name"
            ],
            resume_text=parsed_resume[
                "text"
            ],
            target_role=target_role
        )

        return resume_id


    # =====================================================
    # RESUME ANALYSIS
    # =====================================================

    def analyze_resume(
        self,
        resume_text: str
    ) -> Dict[str, Any]:
        """
        Analyze resume using Ollama.
        """

        if not resume_text.strip():

            return {
                "success": False,
                "stage": "resume_analysis",
                "error": "Resume text is empty."
            }

        result = self.ai.analyze_resume(
            resume_text
        )

        if not result["success"]:

            return {
                "success": False,
                "stage": "resume_analysis",
                "error": result.get(
                    "error",
                    "Resume analysis failed."
                )
            }

        return {
            "success": True,
            "stage": "resume_analysis",
            "data": result.get(
                "data",
                {}
            ),
            "raw_response": result.get(
                "response",
                ""
            )
        }


    # =====================================================
    # SKILL EXTRACTION
    # =====================================================

    def extract_skills(
        self,
        resume_text: str
    ) -> Dict[str, Any]:
        """
        Extract skills from the resume.
        """

        result = self.ai.extract_skills(
            resume_text
        )

        if not result["success"]:

            return {
                "success": False,
                "stage": "skill_extraction",
                "error": result.get(
                    "error",
                    "Skill extraction failed."
                )
            }

        return {
            "success": True,
            "stage": "skill_extraction",
            "data": result.get(
                "data",
                {}
            )
        }


    # =====================================================
    # JOB DESCRIPTION ANALYSIS
    # =====================================================

    def analyze_job(
        self,
        job_description: str
    ) -> Dict[str, Any]:
        """
        Analyze a target job description.
        """

        if not job_description.strip():

            return {
                "success": False,
                "stage": "job_analysis",
                "error": (
                    "Job description cannot be empty."
                )
            }

        result = self.ai.analyze_job_description(
            job_description
        )

        if not result["success"]:

            return {
                "success": False,
                "stage": "job_analysis",
                "error": result.get(
                    "error",
                    "Job analysis failed."
                )
            }

        return {
            "success": True,
            "stage": "job_analysis",
            "data": result.get(
                "data",
                {}
            )
        }


    # =====================================================
    # SAVE JOB
    # =====================================================

    def save_job(
        self,
        user_id: int,
        job_title: str,
        job_description: str,
        company_name: str = ""
    ) -> int:
        """
        Save target job description.
        """

        return self.db.save_job_description(
            user_id=user_id,
            job_title=job_title,
            company_name=company_name,
            job_text=job_description
        )


    # =====================================================
    # SKILL GAP ANALYSIS
    # =====================================================

    def analyze_skill_gap(
        self,
        resume_text: str,
        job_description: str
    ) -> Dict[str, Any]:
        """
        Compare resume against target job.
        """

        if not resume_text.strip():

            return {
                "success": False,
                "stage": "skill_gap",
                "error": "Resume text is empty."
            }

        if not job_description.strip():

            return {
                "success": False,
                "stage": "skill_gap",
                "error": (
                    "Job description is empty."
                )
            }

        result = self.ai.analyze_skill_gap(
            resume_text=resume_text,
            job_description=job_description
        )

        if not result["success"]:

            return {
                "success": False,
                "stage": "skill_gap",
                "error": result.get(
                    "error",
                    "Skill gap analysis failed."
                )
            }

        data = result.get(
            "data",
            {}
        )

        return {
            "success": True,
            "stage": "skill_gap",
            "data": data
        }


    # =====================================================
    # SAVE SKILL GAP
    # =====================================================

    def save_skill_gap(
        self,
        user_id: int,
        skill_gap: Dict[str, Any],
        resume_id: Optional[int] = None,
        job_id: Optional[int] = None
    ) -> int:
        """
        Save skill gap result to SQLite.
        """

        data = skill_gap.get(
            "data",
            skill_gap
        )

        match_percentage = safe_float(
            data.get(
                "match_percentage",
                0
            )
        )

        matched_skills = ensure_list(
            data.get(
                "matched_skills",
                []
            )
        )

        partial_skills = ensure_list(
            data.get(
                "partial_skills",
                []
            )
        )

        missing_skills = ensure_list(
            data.get(
                "missing_skills",
                []
            )
        )

        return self.db.save_skill_gap(
            user_id=user_id,
            resume_id=resume_id,
            job_id=job_id,
            match_percentage=match_percentage,
            matched_skills=matched_skills,
            partial_skills=partial_skills,
            missing_skills=missing_skills,
            analysis=data
        )


    # =====================================================
    # RESUME IMPROVEMENTS
    # =====================================================

    def improve_resume(
        self,
        resume_text: str,
        job_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate resume improvement recommendations.
        """

        result = self.ai.generate_resume_improvements(
            resume_text=resume_text,
            job_description=job_description
        )

        if not result["success"]:

            return {
                "success": False,
                "stage": "resume_improvement",
                "error": result.get(
                    "error",
                    "Resume improvement failed."
                )
            }

        return {
            "success": True,
            "stage": "resume_improvement",
            "data": result.get(
                "data",
                {}
            )
        }


    # =====================================================
    # CAREER RECOMMENDATIONS
    # =====================================================

    def recommend_careers(
        self,
        resume_text: str
    ) -> Dict[str, Any]:
        """
        Recommend career paths.
        """

        result = self.ai.recommend_careers(
            resume_text
        )

        if not result["success"]:

            return {
                "success": False,
                "stage": "career_recommendation",
                "error": result.get(
                    "error",
                    "Career recommendation failed."
                )
            }

        return {
            "success": True,
            "stage": "career_recommendation",
            "data": result.get(
                "data",
                {}
            )
        }


    # =====================================================
    # LEARNING ROADMAP
    # =====================================================

    def generate_roadmap(
        self,
        missing_skills: List[str],
        target_role: str,
        experience_level: str = "beginner"
    ) -> Dict[str, Any]:
        """
        Generate a personalized learning roadmap.
        """

        missing_skills = ensure_list(
            missing_skills
        )

        if not missing_skills:

            return {
                "success": True,
                "stage": "learning_roadmap",
                "data": {
                    "target_role": target_role,
                    "experience_level": (
                        experience_level
                    ),
                    "estimated_duration": (
                        "No additional skills required."
                    ),
                    "priority_order": [],
                    "phases": [],
                    "portfolio_projects": [],
                    "interview_preparation": [],
                    "final_recommendations": [
                        "Continue improving "
                        "existing skills."
                    ]
                }
            }

        result = self.ai.generate_learning_roadmap(
            missing_skills=missing_skills,
            target_role=target_role,
            experience_level=experience_level
        )

        if not result["success"]:

            return {
                "success": False,
                "stage": "learning_roadmap",
                "error": result.get(
                    "error",
                    "Roadmap generation failed."
                )
            }

        return {
            "success": True,
            "stage": "learning_roadmap",
            "data": result.get(
                "data",
                {}
            )
        }


    # =====================================================
    # SAVE ROADMAP
    # =====================================================

    def save_roadmap(
        self,
        user_id: int,
        roadmap: Dict[str, Any],
        target_role: str,
        skill_gap_id: Optional[int] = None
    ) -> int:
        """
        Save generated roadmap.
        """

        data = roadmap.get(
            "data",
            roadmap
        )

        return self.db.save_roadmap(
            user_id=user_id,
            skill_gap_id=skill_gap_id,
            target_role=target_role,
            roadmap=data
        )


    # =====================================================
    # INTERVIEW QUESTIONS
    # =====================================================

    def generate_interview_questions(
        self,
        resume_text: str,
        target_role: str
    ) -> Dict[str, Any]:
        """
        Generate personalized interview questions.
        """

        result = self.ai.generate_interview_questions(
            resume_text=resume_text,
            target_role=target_role
        )

        if not result["success"]:

            return {
                "success": False,
                "stage": "interview_questions",
                "error": result.get(
                    "error",
                    "Interview question generation failed."
                )
            }

        return {
            "success": True,
            "stage": "interview_questions",
            "data": result.get(
                "data",
                {}
            )
        }


    def analyze_uploaded_resume(
        self,
        resume_text: str,
        job_description: str,
        job_title: str = "",
        company_name: str = ""
    ) -> Dict[str, Any]:
        """Run the complete analysis for resume text supplied by the app."""

        if not isinstance(resume_text, str) or not resume_text.strip():
            return {
                "success": False,
                "workflow": "complete",
                "model": self.model,
                "errors": ["Resume text is empty."]
            }

        if not isinstance(job_description, str) or not job_description.strip():
            return {
                "success": False,
                "workflow": "complete",
                "model": self.model,
                "errors": ["Job description is empty."]
            }

        return self.run_complete_analysis(
            user_id=0,
            file_name="uploaded_resume.txt",
            file_bytes=resume_text.encode("utf-8"),
            job_description=job_description,
            job_title=job_title,
            company_name=company_name,
            target_role=job_title,
            save_results=False
        )


    # =====================================================
    # COMPLETE ANALYSIS
    # =====================================================

    def run_complete_analysis(
        self,
        user_id: int,
        file_name: str,
        file_bytes: bytes,
        job_description: str = "",
        job_title: str = "",
        company_name: str = "",
        target_role: str = "",
        experience_level: str = "beginner",
        save_results: bool = True
    ) -> Dict[str, Any]:
        """
        Run the complete agentic workflow.

        This is the main function used by Streamlit.

        Workflow:

            1. Parse resume
            2. Save resume
            3. Analyze resume
            4. Extract skills
            5. Analyze job
            6. Analyze skill gap
            7. Save skill gap
            8. Improve resume
            9. Recommend careers
            10. Generate roadmap
            11. Save roadmap

        The workflow continues only when each
        critical stage succeeds.
        """

        result = {

            "success": False,

            "workflow": "complete",

            "model": self.model,

            "resume": {},

            "resume_analysis": {},

            "skills": {},

            "job_analysis": {},

            "skill_gap": {},

            "resume_improvements": {},

            "career_recommendations": {},

            "roadmap": {},

            "resume_id": None,

            "job_id": None,

            "skill_gap_id": None,

            "roadmap_id": None,

            "errors": []
        }

        # =================================================
        # STEP 1
        # PARSE RESUME
        # =================================================

        parsed_resume = self.parse_resume_file(
            file_name=file_name,
            file_bytes=file_bytes
        )

        result["resume"] = parsed_resume

        if not parsed_resume["success"]:

            result["errors"].append(
                parsed_resume.get(
                    "error",
                    "Resume parsing failed."
                )
            )

            return result

        resume_text = parsed_resume[
            "text"
        ]

        # =================================================
        # STEP 2
        # SAVE RESUME
        # =================================================

        if save_results:

            try:

                resume_id = self.save_resume(
                    user_id=user_id,
                    parsed_resume=parsed_resume,
                    target_role=target_role
                )

                result["resume_id"] = resume_id

            except Exception as error:

                result["errors"].append(
                    f"Resume storage error: {error}"
                )

        # =================================================
        # STEP 3
        # RESUME ANALYSIS
        # =================================================

        resume_analysis = self.analyze_resume(
            resume_text
        )

        result[
            "resume_analysis"
        ] = resume_analysis

        if not resume_analysis["success"]:

            result["errors"].append(
                resume_analysis.get(
                    "error",
                    "Resume analysis failed."
                )
            )

            return result

        # =================================================
        # STEP 4
        # SKILL EXTRACTION
        # =================================================

        skills = self.extract_skills(
            resume_text
        )

        result[
            "skills"
        ] = skills

        if not skills["success"]:

            result["errors"].append(
                skills.get(
                    "error",
                    "Skill extraction failed."
                )
            )

        # =================================================
        # STEP 5
        # JOB ANALYSIS
        # =================================================

        job_analysis = None

        if job_description.strip():

            job_analysis = self.analyze_job(
                job_description
            )

            result[
                "job_analysis"
            ] = job_analysis

            if not job_analysis["success"]:

                result["errors"].append(
                    job_analysis.get(
                        "error",
                        "Job analysis failed."
                    )
                )

        # =================================================
        # STEP 6
        # SAVE JOB
        # =================================================

        if (
            save_results
            and job_description.strip()
        ):

            try:

                job_id = self.save_job(
                    user_id=user_id,
                    job_title=job_title or target_role,
                    job_description=job_description,
                    company_name=company_name
                )

                result["job_id"] = job_id

            except Exception as error:

                result["errors"].append(
                    f"Job storage error: {error}"
                )

        # =================================================
        # STEP 7
        # SKILL GAP
        # =================================================

        skill_gap = None

        if job_description.strip():

            skill_gap = self.analyze_skill_gap(
                resume_text=resume_text,
                job_description=job_description
            )

            result[
                "skill_gap"
            ] = skill_gap

            if not skill_gap["success"]:

                result["errors"].append(
                    skill_gap.get(
                        "error",
                        "Skill gap analysis failed."
                    )
                )

            elif save_results:

                try:

                    skill_gap_id = (
                        self.save_skill_gap(
                            user_id=user_id,
                            skill_gap=skill_gap,
                            resume_id=result[
                                "resume_id"
                            ],
                            job_id=result[
                                "job_id"
                            ]
                        )
                    )

                    result[
                        "skill_gap_id"
                    ] = skill_gap_id

                except Exception as error:

                    result["errors"].append(
                        "Skill gap storage error: "
                        f"{error}"
                    )

        # =================================================
        # STEP 8
        # RESUME IMPROVEMENTS
        # =================================================

        improvements = self.improve_resume(
            resume_text=resume_text,
            job_description=(
                job_description
                if job_description.strip()
                else None
            )
        )

        result[
            "resume_improvements"
        ] = improvements

        if not improvements["success"]:

            result["errors"].append(
                improvements.get(
                    "error",
                    "Resume improvement failed."
                )
            )

        # =================================================
        # STEP 9
        # CAREER RECOMMENDATIONS
        # =================================================

        careers = self.recommend_careers(
            resume_text
        )

        result[
            "career_recommendations"
        ] = careers

        if not careers["success"]:

            result["errors"].append(
                careers.get(
                    "error",
                    "Career recommendation failed."
                )
            )

        # =================================================
        # STEP 10
        # LEARNING ROADMAP
        # =================================================

        missing_skills = []

        if skill_gap:

            skill_gap_data = skill_gap.get(
                "data",
                {}
            )

            missing_skills = ensure_list(
                skill_gap_data.get(
                    "missing_skills",
                    []
                )
            )

        # Determine target role

        final_target_role = (
            target_role
            or job_title
        )

        if not final_target_role:

            resume_data = resume_analysis.get(
                "data",
                {}
            )

            recommended_roles = ensure_list(
                resume_data.get(
                    "recommended_roles",
                    []
                )
            )

            if recommended_roles:

                final_target_role = str(
                    recommended_roles[0]
                )

            else:

                final_target_role = (
                    "Target Career Role"
                )

        roadmap = self.generate_roadmap(
            missing_skills=missing_skills,
            target_role=final_target_role,
            experience_level=experience_level
        )

        result[
            "roadmap"
        ] = roadmap

        if not roadmap["success"]:

            result["errors"].append(
                roadmap.get(
                    "error",
                    "Roadmap generation failed."
                )
            )

        elif save_results:

            try:

                roadmap_id = self.save_roadmap(
                    user_id=user_id,
                    roadmap=roadmap,
                    target_role=final_target_role,
                    skill_gap_id=result[
                        "skill_gap_id"
                    ]
                )

                result[
                    "roadmap_id"
                ] = roadmap_id

            except Exception as error:

                result["errors"].append(
                    f"Roadmap storage error: {error}"
                )

        # =================================================
        # FINAL STATUS
        # =================================================

        result["success"] = True

        return result


    # =====================================================
    # QUICK SKILL GAP
    # =====================================================

    def quick_skill_gap(
        self,
        resume_text: str,
        job_description: str
    ) -> Dict[str, Any]:
        """
        Perform only skill-gap analysis.

        Useful when the user doesn't want the
        complete workflow.
        """

        return self.analyze_skill_gap(
            resume_text=resume_text,
            job_description=job_description
        )


    # =====================================================
    # QUICK RESUME ANALYSIS
    # =====================================================

    def quick_resume_analysis(
        self,
        resume_text: str
    ) -> Dict[str, Any]:
        """
        Perform only resume analysis.
        """

        return self.analyze_resume(
            resume_text
        )


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def ensure_list(
    value: Any
) -> List[Any]:
    """
    Convert different values into a list.
    """

    if value is None:

        return []

    if isinstance(
        value,
        list
    ):

        return value

    if isinstance(
        value,
        tuple
    ):

        return list(
            value
        )

    if isinstance(
        value,
        str
    ):

        if not value.strip():

            return []

        return [
            item.strip()
            for item in value.split(",")
            if item.strip()
        ]

    return [
        value
    ]


def safe_float(
    value: Any,
    default: float = 0.0
) -> float:
    """
    Safely convert a value to float.
    """

    try:

        number = float(
            value
        )

        return max(
            0.0,
            min(
                100.0,
                number
            )
        )

    except (
        ValueError,
        TypeError
    ):

        return default


# =========================================================
# DEFAULT AGENT
# =========================================================

agent = ResumeSkillGapAgent(
    model=DEFAULT_MODEL
)


# =========================================================
# CONVENIENCE FUNCTION
# =========================================================

def run_agent(
    user_id: int,
    file_name: str,
    file_bytes: bytes,
    job_description: str = "",
    job_title: str = "",
    company_name: str = "",
    target_role: str = "",
    experience_level: str = "beginner",
    model: str = DEFAULT_MODEL
) -> Dict[str, Any]:
    """
    Convenience function used by the Streamlit app.
    """

    project_agent = ResumeSkillGapAgent(
        model=model
    )

    return project_agent.run_complete_analysis(
        user_id=user_id,
        file_name=file_name,
        file_bytes=file_bytes,
        job_description=job_description,
        job_title=job_title,
        company_name=company_name,
        target_role=target_role,
        experience_level=experience_level,
        save_results=True
    )


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    print("=" * 70)

    print(
        "AI RESUME & SKILL GAP AGENT"
    )

    print(
        "Agent Orchestration Test"
    )

    print("=" * 70)

    project_agent = ResumeSkillGapAgent(
        model=DEFAULT_MODEL
    )

    # -----------------------------------------------------
    # Agent status
    # -----------------------------------------------------

    print(
        "\nChecking agent status..."
    )

    status = project_agent.get_status()

    print(
        f"Agent: {status['agent']}"
    )

    print(
        f"Model: {status['model']}"
    )

    print(
        f"Ollama connected: "
        f"{status['ollama_connected']}"
    )

    print(
        f"Model available: "
        f"{status['model_available']}"
    )

    # -----------------------------------------------------
    # Sample resume
    # -----------------------------------------------------

    sample_resume = """
    John Doe

    Python Developer

    SUMMARY

    Python developer with experience in
    data analysis and web development.

    SKILLS

    Python
    SQL
    Pandas
    Streamlit
    Git

    EXPERIENCE

    Software Developer
    ABC Technologies

    Developed Python applications and
    data processing tools.

    EDUCATION

    Bachelor of Computer Applications
    """

    # -----------------------------------------------------
    # Sample job
    # -----------------------------------------------------

    sample_job = """
    Data Scientist

    Required Skills:

    Python
    SQL
    Pandas
    Machine Learning
    Statistics
    Scikit-learn

    Responsibilities:

    Build machine learning models.
    Analyze business data.
    Create data-driven solutions.
    """

    # -----------------------------------------------------
    # Test skill gap
    # -----------------------------------------------------

    if status["model_available"]:

        print(
            "\nRunning quick skill-gap test..."
        )

        result = project_agent.quick_skill_gap(
            resume_text=sample_resume,
            job_description=sample_job
        )

        if result["success"]:

            print(
                "\n✅ Skill-gap analysis completed."
            )

            data = result.get(
                "data",
                {}
            )

            print(
                "\nMatch percentage:"
            )

            print(
                data.get(
                    "match_percentage",
                    0
                )
            )

            print(
                "\nMatched skills:"
            )

            for skill in ensure_list(
                data.get(
                    "matched_skills",
                    []
                )
            ):

                print(
                    f"  ✓ {skill}"
                )

            print(
                "\nMissing skills:"
            )

            for skill in ensure_list(
                data.get(
                    "missing_skills",
                    []
                )
            ):

                print(
                    f"  ✗ {skill}"
                )

        else:

            print(
                "\n❌ Skill-gap test failed."
            )

            print(
                result.get(
                    "error",
                    "Unknown error"
                )
            )

    else:

        print(
            "\n⚠️ Ollama model is not available."
        )

        print(
            "Install a model before testing."
        )

    print(
        "\n" + "=" * 70
    )

