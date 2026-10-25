from typing import Dict, Any, List

from ollama_client import (
    DEFAULT_MODEL,
    career_advisor
)


# =========================================================
# CAREER AGENT
# =========================================================

class CareerAgent:
    """
    Personalized career advisor.

    Inputs:
        Candidate resume/profile
        Skill gap analysis
        Target role

    Outputs:
        Career recommendations
        Strengths
        Weaknesses
        Interview preparation
        Resume improvements
        Next steps
    """

    name = "Career Advisor Agent"

    def __init__(
        self,
        model: str = DEFAULT_MODEL
    ):

        self.model = model

    # =====================================================
    # RUN
    # =====================================================

    def run(
        self,
        resume_text: str,
        skill_gap: Dict[str, Any],
        target_role: str
    ) -> Dict[str, Any]:
        """
        Generate personalized career advice.
        """

        if not resume_text.strip():

            return {
                "success": False,
                "agent": self.name,
                "error": "Resume text is empty.",
                "data": None
            }

        if not target_role.strip():

            return {
                "success": False,
                "agent": self.name,
                "error": "Target role is empty.",
                "data": None
            }

        try:

            result = career_advisor(
                resume_text=resume_text,
                skill_gap=skill_gap,
                target_role=target_role,
                model=self.model
            )

            normalized = normalize_career_result(
                result
            )

            return {
                "success": True,
                "agent": self.name,
                "error": None,
                "data": normalized
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
    Convert AI output into a clean list of strings.
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

        lines = value.split(
            "\n"
        )

        if len(lines) > 1:

            return [
                line.strip(
                    " -•0123456789.\t"
                )
                for line in lines
                if line.strip(
                    " -•0123456789.\t"
                )
            ]

        if "," in value:

            return [
                item.strip()
                for item in value.split(
                    ","
                )
                if item.strip()
            ]

        return [
            value.strip()
        ]

    return []


# =========================================================
# NORMALIZE CAREER RESULT
# =========================================================

def normalize_career_result(
    data: Any
) -> Dict[str, Any]:
    """
    Normalize Ollama career-advice output.
    """

    if not isinstance(
        data,
        dict
    ):

        data = {}

    result = {

        "career_summary": get_value(
            data,
            [
                "career_summary",
                "summary",
                "career_advice",
                "overview"
            ],
            default=""
        ),

        "strengths": normalize_list(
            get_value(
                data,
                [
                    "strengths",
                    "candidate_strengths"
                ]
            )
        ),

        "weaknesses": normalize_list(
            get_value(
                data,
                [
                    "weaknesses",
                    "areas_to_improve",
                    "improvement_areas"
                ]
            )
        ),

        "recommended_roles": normalize_list(
            get_value(
                data,
                [
                    "recommended_roles",
                    "suitable_roles",
                    "career_roles"
                ]
            )
        ),

        "resume_improvements": normalize_list(
            get_value(
                data,
                [
                    "resume_improvements",
                    "resume_suggestions"
                ]
            )
        ),

        "interview_topics": normalize_list(
            get_value(
                data,
                [
                    "interview_topics",
                    "interview_preparation",
                    "interview_questions"
                ]
            )
        ),

        "next_steps": normalize_list(
            get_value(
                data,
                [
                    "next_steps",
                    "action_plan",
                    "recommendations"
                ]
            )
        ),

        "career_paths": normalize_list(
            get_value(
                data,
                [
                    "career_paths",
                    "career_directions"
                ]
            )
        ),

        "certifications": normalize_list(
            get_value(
                data,
                [
                    "certifications",
                    "recommended_certifications"
                ]
            )
        )
    }

    return result


# =========================================================
# GET VALUE
# =========================================================

def get_value(
    data: Dict[str, Any],
    keys: List[str],
    default=None
) -> Any:
    """
    Return the first available non-empty value.
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

    return default


# =========================================================
# STRENGTH ANALYZER
# =========================================================

def analyze_strengths(
    resume_skills: List[str],
    matched_skills: List[str]
) -> Dict[str, Any]:
    """
    Perform a simple deterministic strength analysis.

    The LLM provides semantic advice, while this function
    provides transparent numerical information.
    """

    resume_count = len(
        set(
            skill.lower().strip()
            for skill in resume_skills
            if isinstance(
                skill,
                str
            )
        )
    )

    matched_count = len(
        set(
            skill.lower().strip()
            for skill in matched_skills
            if isinstance(
                skill,
                str
            )
        )
    )

    if resume_count == 0:

        relevance = 0.0

    else:

        relevance = (
            matched_count
            / resume_count
        ) * 100

    return {
        "resume_skill_count": resume_count,
        "matched_skill_count": matched_count,
        "target_relevance": round(
            relevance,
            2
        )
    }


# =========================================================
# CAREER READINESS
# =========================================================

def calculate_career_readiness(
    match_percentage: float
) -> Dict[str, Any]:
    """
    Convert skill match percentage into a simple
    career-readiness category.
    """

    if match_percentage >= 85:

        level = "Excellent"
        description = (
            "The candidate appears strongly aligned "
            "with the target role."
        )

    elif match_percentage >= 70:

        level = "Good"
        description = (
            "The candidate has a solid foundation but "
            "should address several skill gaps."
        )

    elif match_percentage >= 50:

        level = "Moderate"
        description = (
            "The candidate has some relevant skills, "
            "but significant upskilling is recommended."
        )

    elif match_percentage >= 30:

        level = "Needs Improvement"
        description = (
            "The candidate should focus on building "
            "core requirements before applying."
        )

    else:

        level = "Low"
        description = (
            "There is currently a substantial gap "
            "between the resume and target role."
        )

    return {
        "level": level,
        "description": description
    }


# =========================================================
# INTERVIEW PREPARATION
# =========================================================

def create_interview_checklist(
    skill_gap: Dict[str, Any]
) -> List[str]:
    """
    Generate a deterministic interview preparation
    checklist from skill gaps.
    """

    checklist = []

    matched = skill_gap.get(
        "matched_skills",
        []
    )

    missing = skill_gap.get(
        "missing_skills",
        []
    )

    # -----------------------------------------------------
    # Review matched skills
    # -----------------------------------------------------

    for skill in matched[:10]:

        checklist.append(
            f"Prepare practical interview examples "
            f"for {skill}."
        )

    # -----------------------------------------------------
    # Study missing skills
    # -----------------------------------------------------

    for skill in missing[:10]:

        checklist.append(
            f"Study the fundamentals of {skill} "
            f"before the interview."
        )

    return checklist


# =========================================================
# COMPLETE CAREER ANALYSIS
# =========================================================

def build_career_analysis(
    career_result: Dict[str, Any],
    skill_gap: Dict[str, Any],
    resume_skills: List[str]
) -> Dict[str, Any]:
    """
    Combine LLM advice with deterministic analysis.
    """

    match_percentage = float(
        skill_gap.get(
            "match_percentage",
            0
        )
    )

    matched_skills = skill_gap.get(
        "matched_skills",
        []
    )

    missing_skills = skill_gap.get(
        "missing_skills",
        []
    )

    strengths = analyze_strengths(
        resume_skills=resume_skills,
        matched_skills=matched_skills
    )

    readiness = calculate_career_readiness(
        match_percentage
    )

    checklist = create_interview_checklist(
        skill_gap
    )

    return {

        "career_advice": career_result,

        "readiness": readiness,

        "skill_statistics": strengths,

        "interview_checklist": checklist,

        "target_role_match": match_percentage,

        "matched_skills": matched_skills,

        "missing_skills": missing_skills
    }


# =========================================================
# CONVENIENCE FUNCTION
# =========================================================

def get_career_advice(
    resume_text: str,
    skill_gap: Dict[str, Any],
    target_role: str,
    resume_skills: List[str] = None,
    model: str = DEFAULT_MODEL
) -> Dict[str, Any]:
    """
    Convenience function for Streamlit.
    """

    resume_skills = (
        resume_skills or []
    )

    agent = CareerAgent(
        model=model
    )

    result = agent.run(
        resume_text=resume_text,
        skill_gap=skill_gap,
        target_role=target_role
    )

    if not result["success"]:

        return result

    analysis = build_career_analysis(
        career_result=result["data"],
        skill_gap=skill_gap,
        resume_skills=resume_skills
    )

    result["data"] = analysis

    return result


# =========================================================
# DISPLAY DATA
# =========================================================

def get_career_display_data(
    result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Prepare career recommendations for the Streamlit UI.
    """

    if not result.get(
        "success",
        False
    ):

        return {
            "success": False,
            "error": result.get(
                "error",
                "Unknown error"
            )
        }

    data = result.get(
        "data",
        {}
    )

    career_advice = data.get(
        "career_advice",
        {}
    )

    readiness = data.get(
        "readiness",
        {}
    )

    return {

        "success": True,

        "career_summary": career_advice.get(
            "career_summary",
            ""
        ),

        "strengths": career_advice.get(
            "strengths",
            []
        ),

        "weaknesses": career_advice.get(
            "weaknesses",
            []
        ),

        "recommended_roles": career_advice.get(
            "recommended_roles",
            []
        ),

        "resume_improvements": career_advice.get(
            "resume_improvements",
            []
        ),

        "interview_topics": career_advice.get(
            "interview_topics",
            []
        ),

        "next_steps": career_advice.get(
            "next_steps",
            []
        ),

        "career_paths": career_advice.get(
            "career_paths",
            []
        ),

        "certifications": career_advice.get(
            "certifications",
            []
        ),

        "readiness_level": readiness.get(
            "level",
            "Unknown"
        ),

        "readiness_description": readiness.get(
            "description",
            ""
        ),

        "match_percentage": data.get(
            "target_role_match",
            0
        ),

        "interview_checklist": data.get(
            "interview_checklist",
            []
        )
    }


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    print("=" * 70)
    print("AI RESUME & SKILL GAP AGENT")
    print("Career Agent Test")
    print("=" * 70)

    sample_resume = """
    Rahul Sharma

    Python Developer with 2 years of experience.

    Skills:
    Python, SQL, Pandas, Streamlit,
    Machine Learning, Git.
    """

    sample_skill_gap = {
        "match_percentage": 62.5,

        "matched_skills": [
            "Python",
            "SQL",
            "Pandas",
            "Machine Learning"
        ],

        "missing_skills": [
            "NumPy",
            "Scikit-learn",
            "Statistics",
            "AWS"
        ]
    }

    target_role = "Data Scientist"

    print(
        "\nGenerating career advice..."
    )

    result = get_career_advice(
        resume_text=sample_resume,
        skill_gap=sample_skill_gap,
        target_role=target_role,
        resume_skills=[
            "Python",
            "SQL",
            "Pandas",
            "Streamlit",
            "Machine Learning",
            "Git"
        ],
        model=DEFAULT_MODEL
    )

    if not result["success"]:

        print(
            "\n❌ Career Agent failed:"
        )

        print(
            result["error"]
        )

        raise SystemExit

    display = get_career_display_data(
        result
    )

    print(
        "\n✅ Career analysis completed."
    )

    print(
        "\nReadiness:"
    )

    print(
        display["readiness_level"]
    )

    print(
        "\nMatch Percentage:"
    )

    print(
        f"{display['match_percentage']}%"
    )

    print(
        "\nCareer Summary:"
    )

    print(
        display["career_summary"]
    )

    print(
        "\nRecommended Roles:"
    )

    for role in display[
        "recommended_roles"
    ]:

        print(
            f"  • {role}"
        )

    print(
        "\nStrengths:"
    )

    for item in display[
        "strengths"
    ]:

        print(
            f"  ✅ {item}"
        )

    print(
        "\nWeaknesses:"
    )

    for item in display[
        "weaknesses"
    ]:

        print(
            f"  ⚠️ {item}"
        )

    print(
        "\nResume Improvements:"
    )

    for item in display[
        "resume_improvements"
    ]:

        print(
            f"  📝 {item}"
        )

    print(
        "\nInterview Topics:"
    )

    for item in display[
        "interview_topics"
    ]:

        print(
            f"  🎯 {item}"
        )

    print(
        "\nNext Steps:"
    )

    for item in display[
        "next_steps"
    ]:

        print(
            f"  → {item}"
        )

    print(
        "\n" + "=" * 70
    )

    print(
        "Career Agent test completed."
    )

    print(
        "=" * 70
    )

