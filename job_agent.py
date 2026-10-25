from typing import Dict, Any, List, Optional

from ollama_client import (
    DEFAULT_MODEL,
    analyze_job_description
)


# =========================================================
# JOB AGENT
# =========================================================

class JobAgent:
    """
    Analyzes a job description using Ollama.

    The output is normalized into a structure that can
    be consumed by the Skill Gap Agent.
    """

    name = "Job Analysis Agent"

    def __init__(
        self,
        model: str = DEFAULT_MODEL
    ):

        self.model = model

    # =====================================================
    # RUN AGENT
    # =====================================================

    def run(
        self,
        job_description: str
    ) -> Dict[str, Any]:
        """
        Analyze a job description.
        """

        if not job_description:

            return {
                "success": False,
                "agent": self.name,
                "error": "Job description is empty.",
                "data": None
            }

        job_description = (
            job_description.strip()
        )

        if len(job_description) < 30:

            return {
                "success": False,
                "agent": self.name,
                "error": (
                    "Job description is too short. "
                    "Please provide a complete job description."
                ),
                "data": None
            }

        try:

            # -------------------------------------------------
            # Call Ollama
            # -------------------------------------------------

            ai_result = analyze_job_description(
                job_description=job_description,
                model=self.model
            )

            # -------------------------------------------------
            # Normalize AI output
            # -------------------------------------------------

            profile = normalize_job_profile(
                ai_result
            )

            # -------------------------------------------------
            # Add raw description
            # -------------------------------------------------

            profile[
                "job_description"
            ] = job_description

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


# =========================================================
# NORMALIZE LIST
# =========================================================

def normalize_list(
    value: Any
) -> List[str]:
    """
    Convert different AI response formats into a list.

    Supported:

        ["Python", "SQL"]

    or:

        "Python, SQL"

    or:

        None
    """

    if value is None:

        return []

    if isinstance(
        value,
        list
    ):

        result = []

        for item in value:

            if isinstance(
                item,
                str
            ):

                cleaned = item.strip()

                if cleaned:

                    result.append(
                        cleaned
                    )

        return result

    if isinstance(
        value,
        str
    ):

        # Handle comma-separated AI output
        if "," in value:

            parts = value.split(
                ","
            )

            return [
                part.strip()
                for part in parts
                if part.strip()
            ]

        # Handle newline-separated output
        lines = value.split(
            "\n"
        )

        if len(lines) > 1:

            return [
                line.strip(
                    " -•\t"
                )
                for line in lines
                if line.strip(
                    " -•\t"
                )
            ]

        return [value.strip()]

    return []


# =========================================================
# NORMALIZE JOB PROFILE
# =========================================================

def normalize_job_profile(
    data: Any
) -> Dict[str, Any]:
    """
    Convert Ollama's job analysis into a predictable
    dictionary structure.

    This makes the rest of the application independent
    of minor variations in the AI response.
    """

    if not isinstance(
        data,
        dict
    ):

        data = {}

    profile = {

        "job_title": get_first_value(
            data,
            [
                "job_title",
                "title",
                "role",
                "position"
            ]
        ),

        "seniority": get_first_value(
            data,
            [
                "seniority",
                "experience_level",
                "level"
            ]
        ),

        "required_skills": normalize_list(
            get_first_value(
                data,
                [
                    "required_skills",
                    "must_have_skills",
                    "mandatory_skills"
                ]
            )
        ),

        "preferred_skills": normalize_list(
            get_first_value(
                data,
                [
                    "preferred_skills",
                    "nice_to_have_skills",
                    "optional_skills"
                ]
            )
        ),

        "programming_languages": normalize_list(
            get_first_value(
                data,
                [
                    "programming_languages",
                    "languages"
                ]
            )
        ),

        "frameworks": normalize_list(
            get_first_value(
                data,
                [
                    "frameworks",
                    "libraries"
                ]
            )
        ),

        "databases": normalize_list(
            get_first_value(
                data,
                [
                    "databases",
                    "database_technologies"
                ]
            )
        ),

        "cloud": normalize_list(
            get_first_value(
                data,
                [
                    "cloud",
                    "cloud_platforms",
                    "cloud_technologies"
                ]
            )
        ),

        "tools": normalize_list(
            get_first_value(
                data,
                [
                    "tools",
                    "software_tools",
                    "technologies"
                ]
            )
        ),

        "soft_skills": normalize_list(
            get_first_value(
                data,
                [
                    "soft_skills",
                    "professional_skills"
                ]
            )
        ),

        "education": normalize_list(
            get_first_value(
                data,
                [
                    "education",
                    "education_requirements",
                    "qualifications"
                ]
            )
        ),

        "experience": normalize_list(
            get_first_value(
                data,
                [
                    "experience",
                    "experience_requirements"
                ]
            )
        ),

        "responsibilities": normalize_list(
            get_first_value(
                data,
                [
                    "responsibilities",
                    "job_responsibilities",
                    "duties"
                ]
            )
        ),

        "keywords": normalize_list(
            get_first_value(
                data,
                [
                    "keywords",
                    "important_keywords"
                ]
            )
        )
    }

    # -----------------------------------------------------
    # Add combined skills
    # -----------------------------------------------------

    profile[
        "all_skills"
    ] = combine_skills(
        profile
    )

    # -----------------------------------------------------
    # Add counts
    # -----------------------------------------------------

    profile[
        "skill_counts"
    ] = {
        "required": len(
            profile[
                "required_skills"
            ]
        ),

        "preferred": len(
            profile[
                "preferred_skills"
            ]
        ),

        "programming_languages": len(
            profile[
                "programming_languages"
            ]
        ),

        "frameworks": len(
            profile[
                "frameworks"
            ]
        ),

        "databases": len(
            profile[
                "databases"
            ]
        ),

        "cloud": len(
            profile[
                "cloud"
            ]
        ),

        "tools": len(
            profile[
                "tools"
            ]
        )
    }

    return profile


# =========================================================
# GET FIRST AVAILABLE VALUE
# =========================================================

def get_first_value(
    data: Dict[str, Any],
    keys: List[str]
) -> Any:
    """
    Return the first non-empty value for the supplied keys.
    """

    for key in keys:

        if key not in data:

            continue

        value = data[
            key
        ]

        if value is None:

            continue

        if isinstance(
            value,
            str
        ) and not value.strip():

            continue

        if isinstance(
            value,
            list
        ) and not value:

            continue

        return value

    return None


# =========================================================
# COMBINE ALL SKILLS
# =========================================================

def combine_skills(
    profile: Dict[str, Any]
) -> List[str]:
    """
    Combine skills from all categories into one unique list.
    """

    categories = [
        "required_skills",
        "preferred_skills",
        "programming_languages",
        "frameworks",
        "databases",
        "cloud",
        "tools",
        "soft_skills"
    ]

    skills = []

    seen = set()

    for category in categories:

        values = profile.get(
            category,
            []
        )

        for skill in values:

            if not isinstance(
                skill,
                str
            ):

                continue

            cleaned = skill.strip()

            if not cleaned:

                continue

            normalized = (
                cleaned
                .lower()
                .strip()
            )

            if normalized not in seen:

                skills.append(
                    cleaned
                )

                seen.add(
                    normalized
                )

    return skills


# =========================================================
# EXTRACT REQUIRED SKILLS
# =========================================================

def get_required_skills(
    profile: Dict[str, Any]
) -> List[str]:
    """
    Return only mandatory job skills.
    """

    return profile.get(
        "required_skills",
        []
    )


# =========================================================
# EXTRACT PREFERRED SKILLS
# =========================================================

def get_preferred_skills(
    profile: Dict[str, Any]
) -> List[str]:
    """
    Return only preferred/nice-to-have skills.
    """

    return profile.get(
        "preferred_skills",
        []
    )


# =========================================================
# JOB SUMMARY
# =========================================================

def create_job_summary(
    profile: Dict[str, Any]
) -> str:
    """
    Create a human-readable summary of the job.
    """

    title = profile.get(
        "job_title"
    )

    seniority = profile.get(
        "seniority"
    )

    required = profile.get(
        "required_skills",
        []
    )

    preferred = profile.get(
        "preferred_skills",
        []
    )

    responsibilities = profile.get(
        "responsibilities",
        []
    )

    title_text = (
        title
        if title
        else "Target Position"
    )

    seniority_text = (
        seniority
        if seniority
        else "Not specified"
    )

    return (
        f"Target Role: {title_text}\n"
        f"Seniority: {seniority_text}\n"
        f"Required Skills: {len(required)}\n"
        f"Preferred Skills: {len(preferred)}\n"
        f"Responsibilities: {len(responsibilities)}"
    )


# =========================================================
# JOB PROFILE FOR SKILL GAP AGENT
# =========================================================

def prepare_for_skill_gap(
    profile: Dict[str, Any]
) -> Dict[str, List[str]]:
    """
    Prepare job data specifically for skill-gap analysis.
    """

    return {

        "required_skills": get_required_skills(
            profile
        ),

        "preferred_skills": get_preferred_skills(
            profile
        )
    }


# =========================================================
# CONVENIENCE FUNCTION
# =========================================================

def analyze_job(
    job_description: str,
    model: str = DEFAULT_MODEL
) -> Dict[str, Any]:
    """
    Convenience function for Streamlit.
    """

    agent = JobAgent(
        model=model
    )

    return agent.run(
        job_description
    )


# =========================================================
# DISPLAY DATA
# =========================================================

def get_job_display_data(
    profile: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Prepare job information for Streamlit display.
    """

    return {

        "job_title": profile.get(
            "job_title",
            "Unknown"
        ),

        "seniority": profile.get(
            "seniority",
            "Not specified"
        ),

        "required_skills": profile.get(
            "required_skills",
            []
        ),

        "preferred_skills": profile.get(
            "preferred_skills",
            []
        ),

        "programming_languages": profile.get(
            "programming_languages",
            []
        ),

        "frameworks": profile.get(
            "frameworks",
            []
        ),

        "databases": profile.get(
            "databases",
            []
        ),

        "cloud": profile.get(
            "cloud",
            []
        ),

        "tools": profile.get(
            "tools",
            []
        ),

        "soft_skills": profile.get(
            "soft_skills",
            []
        ),

        "education": profile.get(
            "education",
            []
        ),

        "experience": profile.get(
            "experience",
            []
        ),

        "responsibilities": profile.get(
            "responsibilities",
            []
        )
    }


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    print("=" * 70)
    print("AI RESUME & SKILL GAP AGENT")
    print("Job Agent Test")
    print("=" * 70)

    sample_job = """
    Data Scientist

    We are looking for a Data Scientist with 2-4 years
    of experience.

    Required skills:
    Python, SQL, Pandas, NumPy, Machine Learning,
    Scikit-learn, Statistics and Data Visualization.

    Preferred skills:
    Deep Learning, Docker, AWS and NLP.

    Responsibilities:
    - Build machine learning models.
    - Analyze large datasets.
    - Create dashboards and reports.
    - Work with engineering teams.

    Education:
    Bachelor's degree in Computer Science,
    Statistics, Mathematics or a related field.
    """

    print(
        "\nAnalyzing job description..."
    )

    agent = JobAgent(
        model=DEFAULT_MODEL
    )

    result = agent.run(
        sample_job
    )

    if not result["success"]:

        print(
            "\n❌ Job Agent failed:"
        )

        print(
            result["error"]
        )

        raise SystemExit

    profile = result[
        "data"
    ]

    print(
        "\n✅ Job analysis completed."
    )

    print(
        "\nJob Summary:"
    )

    print(
        create_job_summary(
            profile
        )
    )

    print(
        "\nRequired Skills:"
    )

    for skill in profile[
        "required_skills"
    ]:

        print(
            f"  🔴 {skill}"
        )

    print(
        "\nPreferred Skills:"
    )

    for skill in profile[
        "preferred_skills"
    ]:

        print(
            f"  🟡 {skill}"
        )

    print(
        "\nProgramming Languages:"
    )

    for skill in profile[
        "programming_languages"
    ]:

        print(
            f"  • {skill}"
        )

    print(
        "\nFrameworks:"
    )

    for skill in profile[
        "frameworks"
    ]:

        print(
            f"  • {skill}"
        )

    print(
        "\nDatabases:"
    )

    for skill in profile[
        "databases"
    ]:

        print(
            f"  • {skill}"
        )

    print(
        "\nCloud:"
    )

    for skill in profile[
        "cloud"
    ]:

        print(
            f"  • {skill}"
        )

    print(
        "\nResponsibilities:"
    )

    for item in profile[
        "responsibilities"
    ]:

        print(
            f"  • {item}"
        )

    print(
        "\n" + "=" * 70
    )

    print(
        "Job Agent test completed."
    )

    print(
        "=" * 70
    )

