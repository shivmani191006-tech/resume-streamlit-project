import json
import re
from typing import Any, Dict, List, Optional

import ollama


# =========================================================
# CONFIGURATION
# =========================================================

DEFAULT_MODEL = "llama3.2"

SUPPORTED_MODELS = [
    "llama3.2",
    "mistral",
    "phi3"
]

OLLAMA_HOST = "http://localhost:11434"


# =========================================================
# OLLAMA CLIENT
# =========================================================

class OllamaClient:
    """
    Wrapper around the Ollama Python client.
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        host: str = OLLAMA_HOST
    ):

        self.model = model

        self.host = host

        self.client = ollama.Client(
            host=self.host
        )


    # =====================================================
    # CHANGE MODEL
    # =====================================================

    def set_model(
        self,
        model: str
    ):
        """
        Change the active Ollama model.
        """

        if not model:

            raise ValueError(
                "Model name cannot be empty."
            )

        self.model = model


    # =====================================================
    # CHECK CONNECTION
    # =====================================================

    def check_connection(self) -> Dict[str, Any]:
        """
        Check whether Ollama is accessible.
        """

        try:

            models = self.client.list()

            model_names = []

            for model in models.get(
                "models",
                []
            ):

                name = model.get(
                    "name",
                    ""
                )

                if name:

                    model_names.append(
                        name
                    )

            return {
                "success": True,
                "message": (
                    "Ollama connection successful."
                ),
                "models": model_names
            }

        except Exception as error:

            return {
                "success": False,
                "message": (
                    "Unable to connect to Ollama."
                ),
                "error": str(error),
                "models": []
            }


    # =====================================================
    # LIST MODELS
    # =====================================================

    def list_models(self) -> List[str]:
        """
        Return locally installed Ollama models.
        """

        result = self.check_connection()

        if not result["success"]:

            return []

        return result["models"]


    # =====================================================
    # CHECK MODEL
    # =====================================================

    def model_exists(
        self,
        model: Optional[str] = None
    ) -> bool:
        """
        Check whether a model is installed locally.
        """

        model = model or self.model

        installed_models = self.list_models()

        for installed_model in installed_models:

            if (
                installed_model == model
                or installed_model.startswith(
                    model + ":"
                )
            ):

                return True

        return False


    # =====================================================
    # GENERATE RESPONSE
    # =====================================================

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        json_mode: bool = False
    ) -> Dict[str, Any]:
        """
        Generate an AI response using Ollama.

        Returns:

            {
                "success": True,
                "response": "...",
                "model": "llama3.2"
            }
        """

        if not prompt.strip():

            return {
                "success": False,
                "response": "",
                "error": "Prompt cannot be empty."
            }

        messages = []

        if system_prompt:

            messages.append(
                {
                    "role": "system",
                    "content": system_prompt
                }
            )

        messages.append(
            {
                "role": "user",
                "content": prompt
            }
        )

        options = {
            "temperature": temperature
        }

        try:

            response = self.client.chat(
                model=self.model,
                messages=messages,
                options=options,
                format="json" if json_mode else ""
            )

            message = response.get(
                "message",
                {}
            )

            content = message.get(
                "content",
                ""
            )

            return {
                "success": True,
                "response": content,
                "model": self.model
            }

        except Exception as error:

            return {
                "success": False,
                "response": "",
                "model": self.model,
                "error": str(error)
            }


    # =====================================================
    # GENERATE JSON
    # =====================================================

    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1
    ) -> Dict[str, Any]:
        """
        Ask Ollama to return structured JSON.

        Handles cases where the model accidentally
        adds markdown code fences.
        """

        result = self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            json_mode=True
        )

        if not result["success"]:

            return result

        response = result["response"]

        parsed = self._parse_json_response(
            response
        )

        if parsed is None:

            return {
                "success": False,
                "response": response,
                "model": self.model,
                "error": (
                    "The AI response could not "
                    "be converted to valid JSON."
                )
            }

        return {
            "success": True,
            "response": response,
            "data": parsed,
            "model": self.model
        }


    # =====================================================
    # PARSE JSON
    # =====================================================

    @staticmethod
    def _parse_json_response(
        response: str
    ) -> Optional[Dict[str, Any]]:
        """
        Safely parse JSON from an AI response.
        """

        if not response:

            return None

        response = response.strip()

        # -------------------------------------------------
        # Direct JSON
        # -------------------------------------------------

        try:

            data = json.loads(
                response
            )

            if isinstance(
                data,
                dict
            ):

                return data

        except json.JSONDecodeError:

            pass

        # -------------------------------------------------
        # Remove markdown code fences
        # -------------------------------------------------

        cleaned = re.sub(
            r"```json\s*",
            "",
            response,
            flags=re.IGNORECASE
        )

        cleaned = re.sub(
            r"```\s*",
            "",
            cleaned
        )

        cleaned = cleaned.strip()

        try:

            data = json.loads(
                cleaned
            )

            if isinstance(
                data,
                dict
            ):

                return data

        except json.JSONDecodeError:

            pass

        # -------------------------------------------------
        # Find first JSON object
        # -------------------------------------------------

        start = cleaned.find(
            "{"
        )

        end = cleaned.rfind(
            "}"
        )

        if start >= 0 and end > start:

            json_text = cleaned[
                start:end + 1
            ]

            try:

                data = json.loads(
                    json_text
                )

                if isinstance(
                    data,
                    dict
                ):

                    return data

            except json.JSONDecodeError:

                pass

        return None


    # =====================================================
    # RESUME ANALYSIS
    # =====================================================

    def analyze_resume(
        self,
        resume_text: str
    ) -> Dict[str, Any]:
        """
        Analyze a resume using Ollama.
        """

        system_prompt = """
You are an expert AI resume analyst and career coach.

Analyze resumes accurately and objectively.

Return ONLY valid JSON.

Do not invent information that is not present
in the resume.

Focus on:
- Professional summary
- Skills
- Experience
- Education
- Projects
- Certifications
- Strengths
- Weaknesses
- Missing information
- ATS optimization
- Career recommendations
"""

        prompt = f"""
Analyze the following resume.

RESUME:
-------------------------
{resume_text}
-------------------------

Return JSON using exactly this structure:

{{
    "candidate_summary": "",
    "current_role": "",
    "experience_level": "",
    "skills": [],
    "technical_skills": [],
    "soft_skills": [],
    "education": [],
    "experience": [],
    "projects": [],
    "certifications": [],
    "strengths": [],
    "weaknesses": [],
    "missing_information": [],
    "ats_score": 0,
    "ats_improvements": [],
    "recommended_roles": []
}}

Rules:

1. ats_score must be a number from 0 to 100.
2. skills must contain skills explicitly found
   or strongly supported by the resume.
3. Do not fabricate experience.
4. recommended_roles should contain realistic
   roles based on the resume.
"""

        return self.generate_json(
            prompt=prompt,
            system_prompt=system_prompt
        )


    # =====================================================
    # EXTRACT SKILLS
    # =====================================================

    def extract_skills(
        self,
        resume_text: str
    ) -> Dict[str, Any]:
        """
        Extract technical and professional skills.
        """

        system_prompt = """
You are an expert technical recruiter.

Extract skills from a resume.

Return ONLY valid JSON.

Never invent skills that are not supported
by the resume.
"""

        prompt = f"""
Extract skills from this resume:

-------------------------
{resume_text}
-------------------------

Return:

{{
    "technical_skills": [],
    "programming_languages": [],
    "frameworks": [],
    "databases": [],
    "cloud_tools": [],
    "data_tools": [],
    "ai_ml_tools": [],
    "soft_skills": [],
    "other_skills": []
}}
"""

        return self.generate_json(
            prompt=prompt,
            system_prompt=system_prompt
        )


    # =====================================================
    # JOB DESCRIPTION ANALYSIS
    # =====================================================

    def analyze_job_description(
        self,
        job_description: str
    ) -> Dict[str, Any]:
        """
        Analyze a job description and extract
        requirements.
        """

        system_prompt = """
You are an expert technical recruiter
and job-description analyst.

Extract requirements accurately.

Return ONLY valid JSON.
"""

        prompt = f"""
Analyze this job description:

-------------------------
{job_description}
-------------------------

Return:

{{
    "job_title": "",
    "required_skills": [],
    "preferred_skills": [],
    "programming_languages": [],
    "frameworks": [],
    "databases": [],
    "cloud_tools": [],
    "ai_ml_tools": [],
    "soft_skills": [],
    "education_requirements": [],
    "experience_requirements": [],
    "responsibilities": []
}}
"""

        return self.generate_json(
            prompt=prompt,
            system_prompt=system_prompt
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
        Compare resume against a job description.

        Produces:
            - Matching skills
            - Partial skills
            - Missing skills
            - Match percentage
            - Priority gaps
        """

        system_prompt = """
You are an expert AI career advisor.

Compare a candidate's resume with a target
job description.

Be conservative.

A skill should only be considered matched when
the resume provides evidence for it.

Return ONLY valid JSON.
"""

        prompt = f"""
Compare the following candidate resume with
the target job description.

CANDIDATE RESUME
=========================
{resume_text}

TARGET JOB
=========================
{job_description}

Return:

{{
    "match_percentage": 0,
    "matched_skills": [],
    "partial_skills": [],
    "missing_skills": [],
    "priority_gaps": [],
    "strengths_for_role": [],
    "experience_gaps": [],
    "education_gaps": [],
    "recommendations": []
}}

Rules:

1. match_percentage must be between 0 and 100.
2. matched_skills must be supported by the resume.
3. partial_skills are skills with limited evidence.
4. missing_skills are required skills absent
   from the resume.
5. priority_gaps should rank the most important
   missing skills.
6. Do not invent candidate experience.
"""

        return self.generate_json(
            prompt=prompt,
            system_prompt=system_prompt
        )


    # =====================================================
    # RESUME IMPROVEMENT
    # =====================================================

    def generate_resume_improvements(
        self,
        resume_text: str,
        job_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate resume improvement recommendations.
        """

        system_prompt = """
You are a professional resume writer,
ATS optimization specialist and recruiter.

Provide practical and truthful recommendations.

Never invent achievements, job titles,
companies or technologies.

Return ONLY valid JSON.
"""

        if job_description:

            target_section = f"""
TARGET JOB DESCRIPTION
-------------------------
{job_description}
-------------------------
"""

        else:

            target_section = """
No target job description was provided.
Give general ATS and resume recommendations.
"""

        prompt = f"""
Review this resume:

RESUME
-------------------------
{resume_text}
-------------------------

{target_section}

Return:

{{
    "overall_score": 0,
    "summary_improvements": [],
    "experience_improvements": [],
    "skills_improvements": [],
    "project_improvements": [],
    "education_improvements": [],
    "ats_keywords_to_consider": [],
    "formatting_recommendations": [],
    "action_items": []
}}
"""

        return self.generate_json(
            prompt=prompt,
            system_prompt=system_prompt
        )


    # =====================================================
    # LEARNING ROADMAP
    # =====================================================

    def generate_learning_roadmap(
        self,
        missing_skills: List[str],
        target_role: str,
        experience_level: str = "beginner",
        current_skills: Optional[List[str]] = None,
        learning_goal: str = ""
    ) -> Dict[str, Any]:
        """
        Generate a personalized skill-development roadmap.
        """

        system_prompt = """
You are an expert career-development advisor.

Create realistic learning roadmaps.

Prioritize skills based on:
- Importance for the target role
- Dependencies between skills
- Candidate experience level
- Practical project opportunities

Return ONLY valid JSON.
"""

        skills_text = ", ".join(
            missing_skills
        )

        prompt = f"""
Create a learning roadmap.

TARGET ROLE:
{target_role}

EXPERIENCE LEVEL:
{experience_level}

MISSING SKILLS:
{skills_text}

CURRENT SKILLS:
{", ".join(current_skills or []) or "Not provided"}

LEARNING GOAL:
{learning_goal or "Build the skills needed for the target role"}

Return:

{{
    "target_role": "",
    "experience_level": "",
    "estimated_duration": "",
    "priority_order": [],
    "phases": [
        {{
            "phase": 1,
            "title": "",
            "duration": "",
            "skills": [],
            "objectives": [],
            "practice_projects": [],
            "completion_criteria": []
        }}
    ],
    "portfolio_projects": [],
    "interview_preparation": [],
    "final_recommendations": []
}}
"""

        return self.generate_json(
            prompt=prompt,
            system_prompt=system_prompt
        )


    # =====================================================
    # CAREER RECOMMENDATIONS
    # =====================================================

    def recommend_careers(
        self,
        resume_text: str
    ) -> Dict[str, Any]:
        """
        Recommend career roles based on resume.
        """

        system_prompt = """
You are an expert career counselor.

Recommend realistic career paths based only
on evidence in the candidate's resume.

Return ONLY valid JSON.
"""

        prompt = f"""
Analyze this resume and recommend career paths.

RESUME
-------------------------
{resume_text}
-------------------------

Return:

{{
    "current_profile": "",
    "recommended_roles": [
        {{
            "role": "",
            "fit_percentage": 0,
            "reason": "",
            "required_skills": [],
            "skill_gaps": []
        }}
    ],
    "career_direction": "",
    "next_steps": []
}}

Provide between 3 and 5 realistic roles.
"""

        return self.generate_json(
            prompt=prompt,
            system_prompt=system_prompt
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

        system_prompt = """
You are an expert technical interviewer.

Generate interview questions based on the
candidate's resume and target role.

Return ONLY valid JSON.
"""

        prompt = f"""
Candidate resume:

-------------------------
{resume_text}
-------------------------

Target role:

{target_role}

Return:

{{
    "technical_questions": [],
    "behavioral_questions": [],
    "project_questions": [],
    "resume_based_questions": [],
    "questions_to_practice": []
}}

Do not invent projects or experience.
"""

        return self.generate_json(
            prompt=prompt,
            system_prompt=system_prompt
        )


# =========================================================
# DEFAULT CLIENT
# =========================================================

ollama_client = OllamaClient(
    model=DEFAULT_MODEL
)


# =========================================================
# CONVENIENCE FUNCTIONS
# =========================================================

def ask_ai(
    prompt: str,
    model: str = DEFAULT_MODEL
) -> Dict[str, Any]:
    """
    Simple helper for sending a prompt to Ollama.
    """

    client = OllamaClient(
        model=model
    )

    return client.generate(
        prompt=prompt
    )


def analyze_resume(
    resume_text: str,
    model: str = DEFAULT_MODEL
) -> Dict[str, Any]:
    """
    Convenience function for resume analysis.
    """

    client = OllamaClient(
        model=model
    )

    return client.analyze_resume(
        resume_text
    )


def analyze_skill_gap(
    resume_text: str,
    job_description: str,
    model: str = DEFAULT_MODEL
) -> Dict[str, Any]:
    """
    Convenience function for skill-gap analysis.
    """

    client = OllamaClient(
        model=model
    )

    return client.analyze_skill_gap(
        resume_text,
        job_description
    )


def analyze_job_description(
    job_description: str,
    model: str = DEFAULT_MODEL
) -> Dict[str, Any]:
    """Analyze a job description using the default Ollama client."""

    client = OllamaClient(
        model=model
    )

    result = client.analyze_job_description(
        job_description
    )

    if not result.get("success"):
        raise RuntimeError(
            result.get("error", "Job description analysis failed.")
        )

    return result.get("data", {})


def career_advisor(
    resume_text: str,
    skill_gap: Dict[str, Any],
    target_role: str,
    model: str = DEFAULT_MODEL
) -> Dict[str, Any]:
    """Generate career guidance tailored to a resume and skill-gap analysis."""

    client = OllamaClient(
        model=model
    )

    system_prompt = """
You are an expert career advisor. Give practical, evidence-based guidance
for the target role. Do not invent candidate experience. Return only valid JSON.
"""

    prompt = f"""
Candidate resume:
-------------------------
{resume_text}
-------------------------

Target role: {target_role}

Skill-gap analysis:
{json.dumps(skill_gap, ensure_ascii=False, default=str)}

Return a JSON object with these fields:
{{
  "career_summary": "",
  "strengths": [],
  "weaknesses": [],
  "recommended_roles": [],
  "resume_improvements": [],
  "interview_topics": [],
  "next_steps": [],
  "career_paths": [],
  "certifications": []
}}
"""

    result = client.generate_json(
        prompt=prompt,
        system_prompt=system_prompt
    )

    if not result.get("success"):
        raise RuntimeError(
            result.get("error", "Career advice generation failed.")
        )

    return result.get("data", {})


def generate_learning_roadmap(
    missing_skills: List[str],
    target_role: str,
    experience_level: str = "beginner",
    current_skills: Optional[List[str]] = None,
    learning_goal: str = "",
    model: str = DEFAULT_MODEL
) -> Dict[str, Any]:
    """
    Convenience function for roadmap generation.
    """

    client = OllamaClient(
        model=model
    )

    return client.generate_learning_roadmap(
        missing_skills=missing_skills,
        target_role=target_role,
        experience_level=experience_level,
        current_skills=current_skills,
        learning_goal=learning_goal
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
        "Ollama Client Test"
    )

    print("=" * 70)

    client = OllamaClient(
        model=DEFAULT_MODEL
    )

    # -----------------------------------------------------
    # Connection test
    # -----------------------------------------------------

    print(
        "\nChecking Ollama connection..."
    )

    connection = client.check_connection()

    if connection["success"]:

        print(
            "✅ Ollama is running."
        )

        print(
            "\nInstalled models:"
        )

        for model in connection["models"]:

            print(
                f"  - {model}"
            )

    else:

        print(
            "❌ Ollama connection failed."
        )

        print(
            connection.get(
                "error",
                connection["message"]
            )
        )

        raise SystemExit

    # -----------------------------------------------------
    # Model test
    # -----------------------------------------------------

    print(
        f"\nChecking model: {client.model}"
    )

    if not client.model_exists():

        print(
            f"⚠️ Model '{client.model}' "
            "is not installed."
        )

        print(
            f"Install it with:\n"
            f"ollama pull {client.model}"
        )

        raise SystemExit

    print(
        "✅ Model is available."
    )

    # -----------------------------------------------------
    # Simple AI test
    # -----------------------------------------------------

    print(
        "\nSending test prompt..."
    )

    result = client.generate(
        prompt=(
            "Give me one short tip for "
            "improving a software developer resume."
        )
    )

    if result["success"]:

        print(
            "\nAI Response:"
        )

        print(
            result["response"]
        )

    else:

        print(
            "\n❌ AI request failed."
        )

        print(
            result.get(
                "error",
                "Unknown error"
            )
        )

    print(
        "\n" + "=" * 70
    )

