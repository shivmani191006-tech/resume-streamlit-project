from typing import Dict, Any, List

from ollama_client import (
    DEFAULT_MODEL,
    generate_learning_roadmap
)


# =========================================================
# ROADMAP AGENT
# =========================================================

class RoadmapAgent:
    """
    Creates a personalized learning roadmap from
    candidate skill gaps.
    """

    name = "Learning Roadmap Agent"

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
        missing_skills: List[str],
        target_role: str,
        current_skills: List[str] = None,
        learning_goal: str = ""
    ) -> Dict[str, Any]:
        """
        Generate a personalized learning roadmap.
        """

        current_skills = (
            current_skills or []
        )

        missing_skills = clean_list(
            missing_skills
        )

        current_skills = clean_list(
            current_skills
        )

        if not target_role.strip():

            return {
                "success": False,
                "agent": self.name,
                "error": "Target role is required.",
                "data": None
            }

        if not missing_skills:

            return {
                "success": True,
                "agent": self.name,
                "error": None,
                "data": {
                    "message": (
                        "No major skill gaps were identified. "
                        "Focus on strengthening existing skills "
                        "and preparing for interviews."
                    ),
                    "roadmap": [],
                    "priority_skills": [],
                    "total_skills": 0
                }
            }

        try:

            result = generate_learning_roadmap(
                missing_skills=missing_skills,
                target_role=target_role,
                current_skills=current_skills,
                learning_goal=learning_goal,
                model=self.model
            )

            normalized = normalize_roadmap(
                result
            )

            normalized[
                "target_role"
            ] = target_role

            normalized[
                "missing_skills"
            ] = missing_skills

            normalized[
                "current_skills"
            ] = current_skills

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
# CLEAN LIST
# =========================================================

def clean_list(
    values: Any
) -> List[str]:
    """
    Clean a list of skills/topics.
    """

    if values is None:

        return []

    if isinstance(
        values,
        str
    ):

        values = values.split(
            ","
        )

    if not isinstance(
        values,
        list
    ):

        return []

    result = []

    seen = set()

    for value in values:

        if not isinstance(
            value,
            str
        ):

            continue

        value = value.strip(
            " -•\t"
        )

        if not value:

            continue

        normalized = value.lower()

        if normalized in seen:

            continue

        seen.add(
            normalized
        )

        result.append(
            value
        )

    return result


# =========================================================
# NORMALIZE ROADMAP
# =========================================================

def normalize_roadmap(
    data: Any
) -> Dict[str, Any]:
    """
    Normalize the AI-generated roadmap.

    Expected structure:

        {
            "roadmap_summary": "...",
            "priority_skills": [],
            "phases": [],
            "projects": [],
            "resources": [],
            "weekly_plan": []
        }
    """

    if not isinstance(
        data,
        dict
    ):

        data = {}

    phases = normalize_phases(
        get_value(
            data,
            [
                "phases",
                "learning_phases",
                "roadmap"
            ],
            []
        )
    )

    projects = normalize_list(
        get_value(
            data,
            [
                "projects",
                "practice_projects",
                "project_ideas"
            ],
            []
        )
    )

    resources = normalize_list(
        get_value(
            data,
            [
                "resources",
                "learning_resources",
                "recommended_resources"
            ],
            []
        )
    )

    weekly_plan = normalize_list(
        get_value(
            data,
            [
                "weekly_plan",
                "weekly_schedule",
                "study_plan"
            ],
            []
        )
    )

    priority_skills = clean_list(
        get_value(
            data,
            [
                "priority_skills",
                "top_skills",
                "skills_to_learn_first"
            ],
            []
        )
    )

    total_duration = get_value(
        data,
        [
            "total_duration",
            "estimated_duration",
            "duration"
        ],
        "Not specified"
    )

    summary = get_value(
        data,
        [
            "roadmap_summary",
            "summary",
            "learning_summary",
            "overview"
        ],
        ""
    )

    return {

        "roadmap_summary": summary,

        "priority_skills": priority_skills,

        "phases": phases,

        "projects": projects,

        "resources": resources,

        "weekly_plan": weekly_plan,

        "total_duration": total_duration,

        "total_skills": len(
            priority_skills
        )
    }


# =========================================================
# NORMALIZE LIST
# =========================================================

def normalize_list(
    value: Any
) -> List[str]:
    """
    Normalize strings/lists into a list.
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

                item = item.strip()

                if item:

                    result.append(
                        item
                    )

            elif isinstance(
                item,
                dict
            ):

                # Convert simple AI objects into readable text
                title = item.get(
                    "title",
                    item.get(
                        "name",
                        ""
                    )
                )

                if title:

                    result.append(
                        str(title)
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
# NORMALIZE PHASES
# =========================================================

def normalize_phases(
    value: Any
) -> List[Dict[str, Any]]:
    """
    Normalize learning phases.

    Example:

        {
            "phase": 1,
            "title": "Python Foundations",
            "duration": "2 weeks",
            "skills": ["Python"],
            "topics": ["Functions", "OOP"],
            "goals": ["Build confidence"],
            "tasks": ["Practice exercises"]
        }
    """

    if not isinstance(
        value,
        list
    ):

        return []

    phases = []

    for index, item in enumerate(
        value,
        start=1
    ):

        if isinstance(
            item,
            str
        ):

            phases.append(
                {
                    "phase": index,
                    "title": item,
                    "duration": "",
                    "skills": [],
                    "topics": [],
                    "goals": [],
                    "tasks": []
                }
            )

            continue

        if not isinstance(
            item,
            dict
        ):

            continue

        phase_number = get_value(
            item,
            [
                "phase",
                "phase_number",
                "number"
            ],
            index
        )

        title = get_value(
            item,
            [
                "title",
                "name",
                "phase_title"
            ],
            f"Phase {index}"
        )

        duration = get_value(
            item,
            [
                "duration",
                "estimated_duration",
                "time"
            ],
            ""
        )

        skills = clean_list(
            get_value(
                item,
                [
                    "skills",
                    "skill",
                    "technologies"
                ],
                []
            )
        )

        topics = normalize_list(
            get_value(
                item,
                [
                    "topics",
                    "learning_topics",
                    "subjects"
                ],
                []
            )
        )

        goals = normalize_list(
            get_value(
                item,
                [
                    "goals",
                    "objectives",
                    "outcomes"
                ],
                []
            )
        )

        tasks = normalize_list(
            get_value(
                item,
                [
                    "tasks",
                    "activities",
                    "action_items"
                ],
                []
            )
        )

        phases.append(
            {
                "phase": phase_number,
                "title": str(title),
                "duration": str(duration),
                "skills": skills,
                "topics": topics,
                "goals": goals,
                "tasks": tasks
            }
        )

    return phases


# =========================================================
# GET VALUE
# =========================================================

def get_value(
    data: Dict[str, Any],
    keys: List[str],
    default=None
) -> Any:
    """
    Return first available non-empty value.
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
# PRIORITIZE SKILLS
# =========================================================

def prioritize_skills(
    missing_skills: List[str],
    required_skills: List[str] = None
) -> List[Dict[str, Any]]:
    """
    Create deterministic skill priorities.

    Required job skills receive higher priority.
    """

    missing_skills = clean_list(
        missing_skills
    )

    required_skills = clean_list(
        required_skills or []
    )

    required_lower = {
        skill.lower()
        for skill in required_skills
    }

    result = []

    for skill in missing_skills:

        if skill.lower() in required_lower:

            priority = "High"

        else:

            priority = "Medium"

        result.append(
            {
                "skill": skill,
                "priority": priority
            }
        )

    return result


# =========================================================
# LEARNING PRIORITY SCORE
# =========================================================

def calculate_priority_score(
    skill: str,
    required_skills: List[str],
    index: int
) -> int:
    """
    Calculate a simple priority score from 1-100.

    This is intentionally transparent rather than relying
    entirely on the LLM.
    """

    required_lower = {
        item.lower()
        for item in clean_list(
            required_skills
        )
    }

    if skill.lower() in required_lower:

        base_score = 90

    else:

        base_score = 65

    # Earlier skills receive a slight priority boost
    score = base_score - (
        min(index, 10) * 2
    )

    return max(
        1,
        min(
            score,
            100
        )
    )


# =========================================================
# BUILD PRIORITY TABLE
# =========================================================

def build_priority_table(
    missing_skills: List[str],
    required_skills: List[str] = None
) -> List[Dict[str, Any]]:
    """
    Build skill priority information for Streamlit.
    """

    required_skills = (
        required_skills or []
    )

    table = []

    for index, skill in enumerate(
        missing_skills
    ):

        score = calculate_priority_score(
            skill=skill,
            required_skills=required_skills,
            index=index
        )

        if score >= 80:

            priority = "High"

        elif score >= 60:

            priority = "Medium"

        else:

            priority = "Low"

        table.append(
            {
                "skill": skill,
                "priority": priority,
                "score": score
            }
        )

    return table


# =========================================================
# CONVENIENCE FUNCTION
# =========================================================

def generate_roadmap(
    missing_skills: List[str],
    target_role: str,
    current_skills: List[str] = None,
    learning_goal: str = "",
    model: str = DEFAULT_MODEL
) -> Dict[str, Any]:
    """
    Convenience function for Streamlit.
    """

    agent = RoadmapAgent(
        model=model
    )

    return agent.run(
        missing_skills=missing_skills,
        target_role=target_role,
        current_skills=current_skills,
        learning_goal=learning_goal
    )


# =========================================================
# ROADMAP SUMMARY
# =========================================================

def create_roadmap_summary(
    roadmap: Dict[str, Any]
) -> str:
    """
    Create a readable roadmap summary.
    """

    if not roadmap:

        return "No roadmap available."

    target_role = roadmap.get(
        "target_role",
        "target role"
    )

    missing = roadmap.get(
        "missing_skills",
        []
    )

    phases = roadmap.get(
        "phases",
        []
    )

    duration = roadmap.get(
        "total_duration",
        "Not specified"
    )

    return (
        f"Learning roadmap for {target_role}. "
        f"{len(missing)} skill gaps identified, "
        f"{len(phases)} learning phases planned, "
        f"estimated duration: {duration}."
    )


# =========================================================
# DISPLAY DATA
# =========================================================

def get_roadmap_display_data(
    result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Prepare roadmap data for Streamlit.
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

    return {

        "success": True,

        "target_role": data.get(
            "target_role",
            ""
        ),

        "summary": data.get(
            "roadmap_summary",
            ""
        ),

        "priority_skills": data.get(
            "priority_skills",
            []
        ),

        "phases": data.get(
            "phases",
            []
        ),

        "projects": data.get(
            "projects",
            []
        ),

        "resources": data.get(
            "resources",
            []
        ),

        "weekly_plan": data.get(
            "weekly_plan",
            []
        ),

        "total_duration": data.get(
            "total_duration",
            "Not specified"
        ),

        "missing_skills": data.get(
            "missing_skills",
            []
        ),

        "current_skills": data.get(
            "current_skills",
            []
        )
    }


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    print("=" * 70)
    print("AI RESUME & SKILL GAP AGENT")
    print("Learning Roadmap Agent Test")
    print("=" * 70)

    missing_skills = [
        "NumPy",
        "Scikit-learn",
        "Statistics",
        "AWS",
        "Docker"
    ]

    current_skills = [
        "Python",
        "SQL",
        "Pandas",
        "Git"
    ]

    target_role = "Data Scientist"

    print(
        "\nMissing Skills:"
    )

    for skill in missing_skills:

        print(
            f"  ❌ {skill}"
        )

    print(
        "\nBuilding priority table..."
    )

    priority_table = build_priority_table(
        missing_skills=missing_skills,
        required_skills=[
            "NumPy",
            "Scikit-learn",
            "Statistics"
        ]
    )

    for item in priority_table:

        print(
            f"  {item['skill']} "
            f"→ {item['priority']} "
            f"({item['score']}/100)"
        )

    print(
        "\nGenerating AI learning roadmap..."
    )

    result = generate_roadmap(
        missing_skills=missing_skills,
        current_skills=current_skills,
        target_role=target_role,
        learning_goal=(
            "Become job-ready for a Data Scientist role."
        ),
        model=DEFAULT_MODEL
    )

    if not result["success"]:

        print(
            "\n❌ Roadmap Agent failed:"
        )

        print(
            result["error"]
        )

        raise SystemExit

    display = get_roadmap_display_data(
        result
    )

    print(
        "\n✅ Roadmap generated."
    )

    print(
        "\nSummary:"
    )

    print(
        display["summary"]
    )

    print(
        "\nTotal Duration:"
    )

    print(
        display["total_duration"]
    )

    print(
        "\nPriority Skills:"
    )

    for skill in display[
        "priority_skills"
    ]:

        print(
            f"  🎯 {skill}"
        )

    print(
        "\nLearning Phases:"
    )

    for phase in display[
        "phases"
    ]:

        print(
            f"\nPhase {phase['phase']}: "
            f"{phase['title']}"
        )

        print(
            f"Duration: {phase['duration']}"
        )

        if phase["skills"]:

            print(
                "Skills:"
            )

            for skill in phase[
                "skills"
            ]:

                print(
                    f"  • {skill}"
                )

        if phase["topics"]:

            print(
                "Topics:"
            )

            for topic in phase[
                "topics"
            ]:

                print(
                    f"  • {topic}"
                )

    print(
        "\nProjects:"
    )

    for project in display[
        "projects"
    ]:

        print(
            f"  🚀 {project}"
        )

    print(
        "\n" + "=" * 70
    )

    print(
        "Roadmap Agent test completed."
    )

    print(
        "=" * 70
    )

