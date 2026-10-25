from typing import List, Dict, Any

import pandas as pd


# =========================================================
# SKILL ALIASES
# =========================================================

SKILL_ALIASES = {
    "python programming": "python",
    "python3": "python",
    "py": "python",

    "machine learning": "machine learning",
    "ml": "machine learning",

    "deep learning": "deep learning",
    "dl": "deep learning",

    "natural language processing": "nlp",
    "natural language processing (nlp)": "nlp",

    "scikit learn": "scikit-learn",
    "sklearn": "scikit-learn",

    "postgres": "postgresql",
    "postgre sql": "postgresql",

    "ms sql": "sql",
    "mysql": "mysql",

    "amazon web services": "aws",
    "amazon aws": "aws",

    "microsoft azure": "azure",

    "google cloud platform": "gcp",

    "data visualization": "data visualization",
    "data viz": "data visualization",

    "natural language processing": "nlp",

    "power bi": "power bi",
    "powerbi": "power bi",

    "ms excel": "excel",
    "microsoft excel": "excel",

    "javascript": "javascript",
    "js": "javascript",

    "typescript": "typescript",
    "ts": "typescript",

    "react.js": "react",
    "reactjs": "react",

    "node.js": "node",
    "nodejs": "node"
}


# =========================================================
# NORMALIZATION
# =========================================================

def normalize_skill(
    skill: str
) -> str:
    """
    Normalize a skill name.

    Example:
        "Python Programming" -> "python"
        "Scikit Learn" -> "scikit-learn"
    """

    if not isinstance(
        skill,
        str
    ):

        return ""

    value = (
        skill
        .strip()
        .lower()
    )

    value = (
        value
        .replace("_", " ")
        .replace("-", " ")
    )

    value = " ".join(
        value.split()
    )

    if value in SKILL_ALIASES:

        return SKILL_ALIASES[value]

    return value


# =========================================================
# UNIQUE SKILLS
# =========================================================

def unique_skills(
    skills: List[str]
) -> List[str]:
    """
    Remove duplicate skills while preserving
    the first readable version.
    """

    result = []

    seen = set()

    for skill in skills:

        if not isinstance(
            skill,
            str
        ):

            continue

        cleaned = skill.strip()

        if not cleaned:

            continue

        normalized = normalize_skill(
            cleaned
        )

        if normalized not in seen:

            result.append(
                cleaned
            )

            seen.add(
                normalized
            )

    return result


# =========================================================
# EXACT SKILL MATCHING
# =========================================================

def compare_skills(
    resume_skills: List[str],
    required_skills: List[str],
    preferred_skills: List[str] = None
) -> Dict[str, Any]:
    """
    Compare candidate skills with job requirements.

    Required skills are used to calculate the main
    match percentage.

    Preferred skills are reported separately.
    """

    preferred_skills = (
        preferred_skills or []
    )

    resume_skills = unique_skills(
        resume_skills
    )

    required_skills = unique_skills(
        required_skills
    )

    preferred_skills = unique_skills(
        preferred_skills
    )

    # -----------------------------------------------------
    # Normalized lookup
    # -----------------------------------------------------

    resume_map = {
        normalize_skill(skill): skill
        for skill in resume_skills
    }

    required_map = {
        normalize_skill(skill): skill
        for skill in required_skills
    }

    preferred_map = {
        normalize_skill(skill): skill
        for skill in preferred_skills
    }

    resume_set = set(
        resume_map.keys()
    )

    required_set = set(
        required_map.keys()
    )

    preferred_set = set(
        preferred_map.keys()
    )

    # -----------------------------------------------------
    # Required skills
    # -----------------------------------------------------

    matched_normalized = (
        resume_set & required_set
    )

    missing_normalized = (
        required_set - resume_set
    )

    matched_skills = [
        required_map[skill]
        for skill in matched_normalized
    ]

    missing_skills = [
        required_map[skill]
        for skill in missing_normalized
    ]

    # -----------------------------------------------------
    # Preferred skills
    # -----------------------------------------------------

    preferred_matched_normalized = (
        resume_set & preferred_set
    )

    preferred_missing_normalized = (
        preferred_set - resume_set
    )

    preferred_matched = [
        preferred_map[skill]
        for skill in preferred_matched_normalized
    ]

    preferred_missing = [
        preferred_map[skill]
        for skill in preferred_missing_normalized
    ]

    # -----------------------------------------------------
    # Score
    # -----------------------------------------------------

    total_required = len(
        required_set
    )

    total_matched = len(
        matched_normalized
    )

    if total_required == 0:

        match_percentage = 0.0

    else:

        match_percentage = (
            total_matched
            / total_required
        ) * 100

    return {
        "matched_skills": sorted(
            matched_skills
        ),

        "missing_skills": sorted(
            missing_skills
        ),

        "preferred_matched": sorted(
            preferred_matched
        ),

        "preferred_missing": sorted(
            preferred_missing
        ),

        "match_percentage": round(
            match_percentage,
            2
        ),

        "total_required": total_required,

        "total_matched": total_matched
    }


# =========================================================
# PARTIAL MATCHING
# =========================================================

def find_partial_matches(
    resume_skills: List[str],
    required_skills: List[str]
) -> List[Dict[str, str]]:
    """
    Find possible partial matches.

    Example:
        Resume: "AWS"
        Requirement: "AWS Cloud"

    or:

        Resume: "Machine Learning"
        Requirement: "Machine Learning Algorithms"
    """

    resume_skills = unique_skills(
        resume_skills
    )

    required_skills = unique_skills(
        required_skills
    )

    results = []

    normalized_resume = [
        (
            skill,
            normalize_skill(skill)
        )
        for skill in resume_skills
    ]

    normalized_required = [
        (
            skill,
            normalize_skill(skill)
        )
        for skill in required_skills
    ]

    for required_original, required_normalized in normalized_required:

        required_words = set(
            required_normalized.split()
        )

        for resume_original, resume_normalized in normalized_resume:

            resume_words = set(
                resume_normalized.split()
            )

            if not required_words:

                continue

            common_words = (
                required_words
                & resume_words
            )

            if not common_words:

                continue

            # Avoid treating a complete exact match
            # as partial.
            if (
                resume_normalized
                == required_normalized
            ):

                continue

            overlap = (
                len(common_words)
                / len(required_words)
            )

            if overlap >= 0.5:

                results.append(
                    {
                        "resume_skill": resume_original,
                        "required_skill": required_original,
                        "similarity": f"{overlap * 100:.0f}%"
                    }
                )

    return results


# =========================================================
# PRIORITY ASSIGNMENT
# =========================================================

def prioritize_missing_skills(
    missing_skills: List[str],
    required_skills: List[str],
    preferred_skills: List[str] = None
) -> List[Dict[str, Any]]:
    """
    Assign priorities to missing skills.

    Required skills:
        HIGH

    Preferred skills:
        MEDIUM

    Unknown:
        LOW
    """

    preferred_skills = (
        preferred_skills or []
    )

    required_normalized = {
        normalize_skill(skill)
        for skill in required_skills
    }

    preferred_normalized = {
        normalize_skill(skill)
        for skill in preferred_skills
    }

    priorities = []

    for skill in missing_skills:

        normalized = normalize_skill(
            skill
        )

        if normalized in required_normalized:

            priority = "HIGH"

        elif normalized in preferred_normalized:

            priority = "MEDIUM"

        else:

            priority = "LOW"

        priorities.append(
            {
                "skill": skill,
                "priority": priority
            }
        )

    # HIGH → MEDIUM → LOW
    priority_order = {
        "HIGH": 1,
        "MEDIUM": 2,
        "LOW": 3
    }

    priorities.sort(
        key=lambda item:
        priority_order.get(
            item["priority"],
            99
        )
    )

    return priorities


# =========================================================
# DATAFRAME REPORT
# =========================================================

def create_skill_dataframe(
    resume_skills: List[str],
    required_skills: List[str],
    preferred_skills: List[str] = None
) -> pd.DataFrame:
    """
    Create a Pandas DataFrame showing each required
    skill and its candidate status.
    """

    preferred_skills = (
        preferred_skills or []
    )

    resume_normalized = {
        normalize_skill(skill)
        for skill in resume_skills
    }

    preferred_normalized = {
        normalize_skill(skill)
        for skill in preferred_skills
    }

    rows = []

    for skill in unique_skills(
        required_skills
    ):

        normalized = normalize_skill(
            skill
        )

        if normalized in resume_normalized:

            status = "Matched"
            priority = "None"

        else:

            status = "Missing"

            if normalized in preferred_normalized:

                priority = "MEDIUM"

            else:

                priority = "HIGH"

        rows.append(
            {
                "Skill": skill,
                "Status": status,
                "Priority": priority,
                "Required": "Yes"
            }
        )

    # Preferred skills that are not already required
    required_normalized = {
        normalize_skill(skill)
        for skill in required_skills
    }

    for skill in unique_skills(
        preferred_skills
    ):

        normalized = normalize_skill(
            skill
        )

        if normalized in required_normalized:

            continue

        if normalized in resume_normalized:

            status = "Matched"
            priority = "None"

        else:

            status = "Missing"
            priority = "MEDIUM"

        rows.append(
            {
                "Skill": skill,
                "Status": status,
                "Priority": priority,
                "Required": "Preferred"
            }
        )

    return pd.DataFrame(
        rows,
        columns=[
            "Skill",
            "Status",
            "Priority",
            "Required"
        ]
    )


# =========================================================
# COMPLETE ANALYSIS
# =========================================================

def analyze_skill_gap(
    resume_skills: List[str],
    required_skills: List[str],
    preferred_skills: List[str] = None
) -> Dict[str, Any]:
    """
    Perform complete deterministic skill-gap analysis.
    """

    preferred_skills = (
        preferred_skills or []
    )

    comparison = compare_skills(
        resume_skills=resume_skills,
        required_skills=required_skills,
        preferred_skills=preferred_skills
    )

    partial_matches = find_partial_matches(
        resume_skills=resume_skills,
        required_skills=required_skills
    )

    priorities = prioritize_missing_skills(
        missing_skills=comparison[
            "missing_skills"
        ],
        required_skills=required_skills,
        preferred_skills=preferred_skills
    )

    dataframe = create_skill_dataframe(
        resume_skills=resume_skills,
        required_skills=required_skills,
        preferred_skills=preferred_skills
    )

    high_priority = [
        item["skill"]
        for item in priorities
        if item["priority"] == "HIGH"
    ]

    medium_priority = [
        item["skill"]
        for item in priorities
        if item["priority"] == "MEDIUM"
    ]

    low_priority = [
        item["skill"]
        for item in priorities
        if item["priority"] == "LOW"
    ]

    return {
        **comparison,

        "partial_matches": partial_matches,

        "priority_details": priorities,

        "high_priority_missing": high_priority,

        "medium_priority_missing": medium_priority,

        "low_priority_missing": low_priority,

        "dataframe": dataframe
    }


# =========================================================
# TEXT SUMMARY
# =========================================================

def create_skill_gap_summary(
    analysis: Dict[str, Any]
) -> str:
    """
    Create a human-readable summary.
    """

    match = analysis.get(
        "match_percentage",
        0
    )

    matched = analysis.get(
        "matched_skills",
        []
    )

    missing = analysis.get(
        "missing_skills",
        []
    )

    high_priority = analysis.get(
        "high_priority_missing",
        []
    )

    return (
        f"Overall skill match: {match}%\n"
        f"Matched skills: {len(matched)}\n"
        f"Missing skills: {len(missing)}\n"
        f"High-priority gaps: {len(high_priority)}"
    )


# =========================================================
# EXPORT REPORT
# =========================================================

def export_skill_gap_csv(
    analysis: Dict[str, Any],
    file_path: str
) -> None:
    """
    Export the skill-gap DataFrame to CSV.
    """

    dataframe = analysis.get(
        "dataframe"
    )

    if dataframe is None:

        raise ValueError(
            "Skill DataFrame is not available."
        )

    dataframe.to_csv(
        file_path,
        index=False
    )


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    resume_skills = [
        "Python",
        "SQL",
        "Pandas",
        "Streamlit",
        "Machine Learning",
        "Git"
    ]

    required_skills = [
        "Python",
        "SQL",
        "Pandas",
        "NumPy",
        "Machine Learning",
        "Scikit-learn",
        "Statistics",
        "Data Visualization"
    ]

    preferred_skills = [
        "AWS",
        "Docker",
        "Deep Learning"
    ]

    print("=" * 60)
    print("SKILL GAP ANALYSIS TEST")
    print("=" * 60)

    analysis = analyze_skill_gap(
        resume_skills=resume_skills,
        required_skills=required_skills,
        preferred_skills=preferred_skills
    )

    print(
        "\nMatch Percentage:"
    )

    print(
        f"{analysis['match_percentage']}%"
    )

    print(
        "\nMatched Skills:"
    )

    for skill in analysis[
        "matched_skills"
    ]:

        print(
            f"  ✅ {skill}"
        )

    print(
        "\nMissing Skills:"
    )

    for skill in analysis[
        "missing_skills"
    ]:

        print(
            f"  ❌ {skill}"
        )

    print(
        "\nHigh Priority:"
    )

    for skill in analysis[
        "high_priority_missing"
    ]:

        print(
            f"  🔴 {skill}"
        )

    print(
        "\nMedium Priority:"
    )

    for skill in analysis[
        "medium_priority_missing"
    ]:

        print(
            f"  🟡 {skill}"
        )

    print(
        "\nPartial Matches:"
    )

    for item in analysis[
        "partial_matches"
    ]:

        print(
            f"  🔄 {item['resume_skill']} "
            f"→ {item['required_skill']} "
            f"({item['similarity']})"
        )

    print(
        "\nDataFrame:"
    )

    print(
        analysis["dataframe"].to_string(
            index=False
        )
    )

    print(
        "\nSummary:"
    )

    print(
        create_skill_gap_summary(
            analysis
        )
    )

