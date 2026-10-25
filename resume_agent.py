from typing import Dict, Any, Optional

from resume_parsor import (
    process_resume,
    detect_resume_sections,
    create_resume_preview
)

from agents import (
    ResumeAnalysisAgent,
    SkillExtractionAgent,
    flatten_skill_result
)

from ollama_client import (
    DEFAULT_MODEL
)


# =========================================================
# RESUME AGENT
# =========================================================

class ResumeAgent:
    """
    Main Resume Agent.

    Responsibilities:
        1. Process uploaded resume.
        2. Validate extracted text.
        3. Detect resume sections.
        4. Analyze resume with Ollama.
        5. Extract candidate skills.
        6. Build structured candidate profile.
    """

    name = "Resume Agent"

    def __init__(
        self,
        model: str = DEFAULT_MODEL
    ):

        self.model = model

        self.resume_analysis_agent = (
            ResumeAnalysisAgent(
                model=model
            )
        )

        self.skill_extraction_agent = (
            SkillExtractionAgent(
                model=model
            )
        )

    # =====================================================
    # PROCESS UPLOADED FILE
    # =====================================================

    def process_file(
        self,
        uploaded_file,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process an uploaded resume file.

        Supports:
            DOCX
            TXT
            PDF
        """

        result = process_resume(
            file=uploaded_file,
            filename=filename
        )

        if not result["success"]:

            return {
                "success": False,
                "agent": self.name,
                "error": result["error"],
                "data": None
            }

        return self.process_text(
            resume_text=result["text"],
            metadata=result["metadata"],
            validation=result["validation"]
        )

    # =====================================================
    # PROCESS TEXT
    # =====================================================

    def process_text(
        self,
        resume_text: str,
        metadata: Optional[Dict[str, Any]] = None,
        validation: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process already-extracted resume text.
        """

        if not resume_text or not resume_text.strip():

            return {
                "success": False,
                "agent": self.name,
                "error": "Resume text is empty.",
                "data": None
            }

        try:

            # -------------------------------------------------
            # Detect basic sections
            # -------------------------------------------------

            sections = detect_resume_sections(
                resume_text
            )

            # -------------------------------------------------
            # AI Resume Analysis
            # -------------------------------------------------

            analysis_result = (
                self.resume_analysis_agent.run(
                    resume_text
                )
            )

            if not analysis_result["success"]:

                return {
                    "success": False,
                    "agent": self.name,
                    "error": analysis_result["error"],
                    "data": None
                }

            # -------------------------------------------------
            # AI Skill Extraction
            # -------------------------------------------------

            skill_result = (
                self.skill_extraction_agent.run(
                    resume_text
                )
            )

            if not skill_result["success"]:

                return {
                    "success": False,
                    "agent": self.name,
                    "error": skill_result["error"],
                    "data": None
                }

            # -------------------------------------------------
            # Flatten skills
            # -------------------------------------------------

            structured_skills = (
                skill_result["data"]
            )

            all_skills = flatten_skill_result(
                structured_skills
            )

            # -------------------------------------------------
            # Candidate profile
            # -------------------------------------------------

            profile = self.build_candidate_profile(
                resume_text=resume_text,
                sections=sections,
                analysis=analysis_result["data"],
                structured_skills=structured_skills,
                all_skills=all_skills
            )

            return {
                "success": True,
                "agent": self.name,
                "error": None,
                "data": profile
            }

        except Exception as error:

            return {
                "success": False,
                "agent": self.name,
                "error": str(error),
                "data": None
            }

    # =====================================================
    # BUILD CANDIDATE PROFILE
    # =====================================================

    def build_candidate_profile(
        self,
        resume_text: str,
        sections: Dict[str, str],
        analysis: Any,
        structured_skills: Dict[str, Any],
        all_skills: list
    ) -> Dict[str, Any]:
        """
        Build the standardized candidate profile.
        """

        profile = {

            "resume_text": resume_text,

            "resume_preview": create_resume_preview(
                resume_text,
                max_characters=1200
            ),

            "sections": sections,

            "analysis": analysis,

            "skills": {
                "structured": structured_skills,
                "all": all_skills
            },

            "summary": {
                "skill_count": len(
                    all_skills
                ),

                "section_count": len(
                    sections
                ),

                "resume_characters": len(
                    resume_text
                ),

                "resume_words": len(
                    resume_text.split()
                )
            }
        }

        return profile


# =========================================================
# SKILL SUMMARY
# =========================================================

def get_skill_summary(
    profile: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Return a simplified skill summary.
    """

    skills_data = profile.get(
        "skills",
        {}
    )

    structured = skills_data.get(
        "structured",
        {}
    )

    return {
        "technical_skills": structured.get(
            "technical_skills",
            []
        ),

        "soft_skills": structured.get(
            "soft_skills",
            []
        ),

        "tools": structured.get(
            "tools",
            []
        ),

        "frameworks": structured.get(
            "frameworks",
            []
        ),

        "programming_languages": structured.get(
            "programming_languages",
            []
        ),

        "databases": structured.get(
            "databases",
            []
        ),

        "cloud": structured.get(
            "cloud",
            []
        ),

        "other_skills": structured.get(
            "other_skills",
            []
        )
    }


# =========================================================
# PROFILE SUMMARY
# =========================================================

def create_profile_summary(
    profile: Dict[str, Any]
) -> str:
    """
    Create a simple human-readable profile summary.
    """

    summary = profile.get(
        "summary",
        {}
    )

    skill_count = summary.get(
        "skill_count",
        0
    )

    section_count = summary.get(
        "section_count",
        0
    )

    word_count = summary.get(
        "resume_words",
        0
    )

    return (
        f"Resume contains approximately "
        f"{word_count} words, "
        f"{skill_count} identified skills, "
        f"and {section_count} detected sections."
    )


# =========================================================
# EXTRACT CANDIDATE NAME
# =========================================================

def guess_candidate_name(
    resume_text: str
) -> str:
    """
    Make a simple attempt to identify the candidate's name.

    This is intentionally conservative.

    The first meaningful line is used unless it looks
    like an email, phone number, URL or section heading.
    """

    lines = [
        line.strip()
        for line in resume_text.split(
            "\n"
        )
        if line.strip()
    ]

    ignored_words = {
        "resume",
        "curriculum vitae",
        "cv",
        "profile",
        "summary",
        "experience",
        "education",
        "skills",
        "projects"
    }

    for line in lines[:10]:

        lower = line.lower()

        if "@" in line:

            continue

        if (
            "http://" in lower
            or "https://" in lower
            or "www." in lower
        ):

            continue

        digits = sum(
            character.isdigit()
            for character in line
        )

        if digits > 4:

            continue

        if lower in ignored_words:

            continue

        # Avoid very long lines
        if len(line) > 60:

            continue

        return line

    return "Unknown Candidate"


# =========================================================
# CANDIDATE PROFILE DISPLAY DATA
# =========================================================

def get_profile_display_data(
    profile: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Prepare profile information for Streamlit.
    """

    resume_text = profile.get(
        "resume_text",
        ""
    )

    skill_summary = get_skill_summary(
        profile
    )

    return {
        "candidate_name": guess_candidate_name(
            resume_text
        ),

        "summary": create_profile_summary(
            profile
        ),

        "technical_skills": skill_summary[
            "technical_skills"
        ],

        "soft_skills": skill_summary[
            "soft_skills"
        ],

        "tools": skill_summary[
            "tools"
        ],

        "frameworks": skill_summary[
            "frameworks"
        ],

        "programming_languages": skill_summary[
            "programming_languages"
        ],

        "databases": skill_summary[
            "databases"
        ],

        "cloud": skill_summary[
            "cloud"
        ],

        "other_skills": skill_summary[
            "other_skills"
        ]
    }


# =========================================================
# CONVENIENCE FUNCTION
# =========================================================

def analyze_uploaded_resume(
    uploaded_file,
    model: str = DEFAULT_MODEL
) -> Dict[str, Any]:
    """
    Convenience function used by Streamlit.
    """

    agent = ResumeAgent(
        model=model
    )

    return agent.process_file(
        uploaded_file
    )


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    print("=" * 70)
    print("AI RESUME & SKILL GAP AGENT")
    print("Resume Agent Test")
    print("=" * 70)

    sample_resume = """
    Rahul Sharma

    rahul@example.com

    PROFESSIONAL SUMMARY

    Python Developer with 2 years of experience
    developing data applications and dashboards.

    SKILLS

    Python
    SQL
    Pandas
    Streamlit
    Machine Learning
    Git

    EXPERIENCE

    Python Developer
    ABC Technologies
    2024 - Present

    Developed Python applications and data analysis
    dashboards.

    EDUCATION

    B.Tech Computer Science
    """

    print(
        "\nStarting Resume Agent..."
    )

    print(
        "\n⚠️ This test requires Ollama to be running."
    )

    agent = ResumeAgent(
        model=DEFAULT_MODEL
    )

    result = agent.process_text(
        resume_text=sample_resume
    )

    if not result["success"]:

        print(
            "\n❌ Resume Agent failed:"
        )

        print(
            result["error"]
        )

        raise SystemExit

    profile = result[
        "data"
    ]

    print(
        "\n✅ Resume processed successfully."
    )

    print(
        "\nCandidate:"
    )

    print(
        guess_candidate_name(
            sample_resume
        )
    )

    print(
        "\nProfile Summary:"
    )

    print(
        create_profile_summary(
            profile
        )
    )

    print(
        "\nDetected Skills:"
    )

    for skill in profile[
        "skills"
    ][
        "all"
    ]:

        print(
            f"  • {skill}"
        )

    print(
        "\nDetected Sections:"
    )

    for section in profile[
        "sections"
    ]:

        print(
            f"  • {section}"
        )

    print(
        "\nAI Analysis:"
    )

    print(
        profile[
            "analysis"
        ]
    )

    print(
        "\n" + "=" * 70
    )

    print(
        "Resume Agent test completed."
    )

    print(
        "=" * 70
    )

