import streamlit as st
import pandas as pd


# =========================================================
# PROJECT IMPORTS
# =========================================================

from database import (
    init_database,
    register_user,
    login_user,
    save_analysis,
    get_user_analyses
)

from resume_parsor import (
    extract_text_from_uploaded_file
)

from agents import (
    ResumeSkillGapAgent
)

from report_generator import (
    generate_report
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="AI Resume & Skill Gap Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

init_database()


# =========================================================
# SESSION STATE
# =========================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "username" not in st.session_state:
    st.session_state.username = None

if "page" not in st.session_state:
    st.session_state.page = "Login"

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""

if "report_bytes" not in st.session_state:
    st.session_state.report_bytes = None


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: 800;
        color: #2563EB;
        text-align: center;
        margin-bottom: 5px;
    }

    .subtitle {
        text-align: center;
        color: #6B7280;
        font-size: 18px;
        margin-bottom: 30px;
    }

    .feature-card {
        background-color: #F8FAFC;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #E5E7EB;
        margin-bottom: 15px;
        color: #000000;
    }
    
    .feature-card h3 {
         color: #000000;
    } 
    
    .feature-card p {
         color: #000000; 
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def get_nested(
    data,
    *keys,
    default=None
):
    current = data

    for key in keys:

        if not isinstance(
            current,
            dict
        ):
            return default

        current = current.get(
            key
        )

        if current is None:
            return default

    return current


def as_list(value):

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
        return list(value)

    if isinstance(
        value,
        str
    ):

        if not value.strip():
            return []

        return [
            x.strip()
            for x in value.split(",")
            if x.strip()
        ]

    return [value]


def display_list(
    items
):

    items = as_list(
        items
    )

    if not items:

        st.write(
            "No information available."
        )

        return

    for item in items:

        if isinstance(
            item,
            dict
        ):

            item = ", ".join(
                f"{k}: {v}"
                for k, v in item.items()
            )

        st.markdown(
            f"- {item}"
        )


def get_analysis_data(
    section
):

    if not isinstance(
        section,
        dict
    ):
        return {}

    if isinstance(
        section.get("data"),
        dict
    ):
        return section["data"]

    return section


# =========================================================
# LOGIN PAGE
# =========================================================

def login_page():

    st.markdown(
        '<div class="main-title">🤖 AI Resume Agent</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'AI-powered Resume Analysis & Skill Gap Detection'
        '</div>',
        unsafe_allow_html=True
    )

    _, center, _ = st.columns(
        [1, 2, 1]
    )

    with center:

        st.markdown(
            "### 🔐 Login"
        )

        username = st.text_input(
            "Username or Email",
            key="login_username"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="login_password"
        )

        if st.button(
            "Login",
            use_container_width=True,
            type="primary"
        ):

            if not username or not password:

                st.error(
                    "Please enter username and password."
                )

            else:

                result = login_user(
                    username,
                    password
                )

                if result:

                    st.session_state.logged_in = True

                    st.session_state.user_id = result[
                        "id"
                    ]

                    st.session_state.username = result[
                        "username"
                    ]

                    st.session_state.page = "Dashboard"

                    st.session_state.analysis_result = None

                    st.success(
                        "Login successful!"
                    )

                    st.rerun()

                else:

                    st.error(
                        "Invalid username/email or password."
                    )

        st.divider()

        st.write(
            "Don't have an account?"
        )

        if st.button(
            "Create Account",
            use_container_width=True
        ):

            st.session_state.page = "Register"

            st.rerun()


# =========================================================
# REGISTER PAGE
# =========================================================

def register_page():

    st.markdown(
        '<div class="main-title">🚀 Create Account</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'Start your AI-powered career journey'
        '</div>',
        unsafe_allow_html=True
    )

    _, center, _ = st.columns(
        [1, 2, 1]
    )

    with center:

        st.markdown(
            "### 📝 Register"
        )

        username = st.text_input(
            "Username",
            key="register_username"
        )

        email = st.text_input(
            "Email",
            key="register_email"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="register_password"
        )

        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
            key="register_confirm_password"
        )

        if st.button(
            "Register",
            use_container_width=True,
            type="primary"
        ):

            if not username or not email or not password:

                st.error(
                    "All fields are required."
                )

            elif password != confirm_password:

                st.error(
                    "Passwords do not match."
                )

            elif len(password) < 6:

                st.error(
                    "Password must contain at least 6 characters."
                )

            else:

                try:

                    result = register_user(
                        username,
                        email,
                        password
                    )

                    if result.get(
                        "success",
                        False
                    ):

                        st.success(
                            "Registration successful!"
                        )

                        st.info(
                            "You can now login."
                        )

                    else:

                        st.error(
                            result.get(
                                "message",
                                "Registration failed."
                            )
                        )

                except Exception as e:

                    st.error(
                        f"Registration failed: {e}"
                    )

        st.divider()

        if st.button(
            "← Back to Login",
            use_container_width=True
        ):

            st.session_state.page = "Login"

            st.rerun()


# =========================================================
# SIDEBAR
# =========================================================

def sidebar():

    with st.sidebar:

        st.markdown(
            "## 🤖 AI Resume Agent"
        )

        st.caption(
            f"Logged in as: "
            f"**{st.session_state.username}**"
        )

        st.divider()

        if st.button(
            "🏠 Dashboard",
            use_container_width=True
        ):

            st.session_state.page = "Dashboard"

            st.rerun()

        if st.button(
            "📄 Resume Analyzer",
            use_container_width=True
        ):

            st.session_state.page = "Analyzer"

            st.rerun()

        if st.button(
            "📚 My Analyses",
            use_container_width=True
        ):

            st.session_state.page = "History"

            st.rerun()

        st.divider()

        if st.button(
            "🚪 Logout",
            use_container_width=True
        ):

            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.username = None
            st.session_state.analysis_result = None
            st.session_state.resume_text = ""
            st.session_state.report_bytes = None
            st.session_state.page = "Login"

            st.rerun()


# =========================================================
# DASHBOARD
# =========================================================

def dashboard_page():

    st.title(
        "🏠 Dashboard"
    )

    st.write(
        f"Welcome back, "
        f"**{st.session_state.username}**!"
    )

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:

        st.markdown(
            """
            <div class="feature-card">
                <h3>📄 Resume Analysis</h3>
                <p>
                Upload your resume and let AI
                identify strengths, weaknesses,
                skills and ATS improvements.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:

        st.markdown(
            """
            <div class="feature-card">
                <h3>🎯 Skill Gap</h3>
                <p>
                Compare your current skills
                against a target job and
                identify missing skills.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:

        st.markdown(
            """
            <div class="feature-card">
                <h3>🧠 AI Roadmap</h3>
                <p>
                Get a personalized learning
                roadmap based on your career
                goals and skill gaps.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.divider()

    st.subheader(
        "🚀 Start New Analysis"
    )

    if st.button(
        "Analyze My Resume",
        type="primary",
        use_container_width=True
    ):

        st.session_state.page = "Analyzer"

        st.rerun()


# =========================================================
# RESUME ANALYZER
# =========================================================

def analyzer_page():

    st.title(
        "📄 AI Resume & Skill Gap Analyzer"
    )

    st.write(
        "Upload your resume and provide a target job description."
    )

    st.divider()

    st.subheader(
        "1️⃣ Upload Resume"
    )

    uploaded_file = st.file_uploader(
        "Upload PDF, DOCX or TXT",
        type=[
            "pdf",
            "docx",
            "txt"
        ]
    )

    st.subheader(
        "2️⃣ Target Job"
    )

    job_title = st.text_input(
        "Job Title",
        placeholder="Example: Data Scientist"
    )

    company_name = st.text_input(
        "Company Name (Optional)",
        placeholder="Example: Microsoft"
    )

    job_description = st.text_area(
        "Paste Job Description",
        height=250,
        placeholder=(
            "Paste the complete job description here..."
        )
    )

    st.subheader(
        "3️⃣ AI Model"
    )

    model_name = st.selectbox(
        "Select Ollama Model",
        [
            "llama3.2",
            "mistral",
            "phi3"
        ]
    )

    st.caption(
        "Make sure the selected model is installed in Ollama."
    )

    if st.button(
        "🚀 Analyze Resume",
        type="primary",
        use_container_width=True
    ):

        if uploaded_file is None:

            st.error(
                "Please upload your resume."
            )

            return

        if not job_description.strip():

            st.error(
                "Please enter the target job description."
            )

            return

        try:

            with st.spinner(
                "📖 Reading resume..."
            ):

                resume_text = extract_text_from_uploaded_file(
                    uploaded_file
                )

            if not resume_text.strip():

                st.error(
                    "Could not extract text from the resume."
                )

                return

            st.session_state.resume_text = resume_text

            with st.spinner(
                "🤖 AI agent is analyzing your resume..."
            ):

                agent = ResumeSkillGapAgent(
                    model=model_name
                )

                result = agent.analyze_uploaded_resume(
                    resume_text=resume_text,
                    job_description=job_description,
                    job_title=job_title,
                    company_name=company_name
                )

            if not isinstance(
                result,
                dict
            ):

                st.error(
                    "AI returned an invalid result."
                )

                return

            # -------------------------------------------------
            # Save resume text temporarily in result
            # -------------------------------------------------

            result["_resume_text"] = resume_text

            st.session_state.analysis_result = result

            # -------------------------------------------------
            # Save analysis
            # -------------------------------------------------

            try:

                save_analysis(
                    user_id=st.session_state.user_id,
                    job_title=job_title,
                    company_name=company_name,
                    result=result
                )

            except Exception as db_error:

                st.warning(
                    "Analysis completed, but history "
                    f"could not be saved: {db_error}"
                )

            st.session_state.report_bytes = None

            st.success(
                "✅ Analysis completed successfully!"
            )

            st.rerun()

        except Exception as e:

            st.error(
                "Analysis failed."
            )

            st.exception(
                e
            )

    # -----------------------------------------------------
    # Display previous result
    # -----------------------------------------------------

    if st.session_state.analysis_result:

        st.divider()

        display_results(
            st.session_state.analysis_result,
            job_title=job_title,
            company_name=company_name
        )


# =========================================================
# DISPLAY RESULTS
# =========================================================

def display_results(
    result,
    job_title="",
    company_name=""
):

    st.title(
        "📊 AI Analysis Results"
    )

    if not isinstance(
        result,
        dict
    ):

        st.error(
            "Invalid analysis result."
        )

        return

    resume_data = get_analysis_data(
        result.get(
            "resume_analysis",
            {}
        )
    )

    skills_data = get_analysis_data(
        result.get(
            "skills",
            {}
        )
    )

    skill_gap_data = get_analysis_data(
        result.get(
            "skill_gap",
            {}
        )
    )

    improvements_data = get_analysis_data(
        result.get(
            "resume_improvements",
            {}
        )
    )

    career_data = get_analysis_data(
        result.get(
            "career_recommendations",
            {}
        )
    )

    roadmap_data = get_analysis_data(
        result.get(
            "roadmap",
            {}
        )
    )

    # =====================================================
    # METRICS
    # =====================================================

    try:

        ats_score = float(
            resume_data.get(
                "ats_score",
                0
            ) or 0
        )

    except (
        ValueError,
        TypeError
    ):

        ats_score = 0

    try:

        match_score = float(
            skill_gap_data.get(
                "match_percentage",
                0
            ) or 0
        )

    except (
        ValueError,
        TypeError
    ):

        match_score = 0

    strengths_count = len(
        as_list(
            resume_data.get(
                "strengths",
                []
            )
        )
    )

    missing_count = len(
        as_list(
            skill_gap_data.get(
                "missing_skills",
                []
            )
        )
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "ATS Score",
            f"{ats_score:.0f}%"
        )

    with col2:
        st.metric(
            "Job Match",
            f"{match_score:.0f}%"
        )

    with col3:
        st.metric(
            "Strengths",
            strengths_count
        )

    with col4:
        st.metric(
            "Skill Gaps",
            missing_count
        )

    st.divider()

    # =====================================================
    # TABS
    # =====================================================

    (
        tab1,
        tab2,
        tab3,
        tab4,
        tab5,
        tab6,
        tab7
    ) = st.tabs(
        [
            "📄 Resume",
            "🛠️ Skills",
            "🎯 Skill Gap",
            "✨ Improvements",
            "💼 Career",
            "📚 Roadmap",
            "📥 Report"
        ]
    )

    # =====================================================
    # RESUME
    # =====================================================

    with tab1:

        st.subheader(
            "Candidate Summary"
        )

        summary = resume_data.get(
            "candidate_summary",
            ""
        )

        if summary:
            st.info(
                summary
            )

        st.subheader(
            "Resume Strengths"
        )

        display_list(
            resume_data.get(
                "strengths",
                []
            )
        )

        st.subheader(
            "Weaknesses"
        )

        display_list(
            resume_data.get(
                "weaknesses",
                []
            )
        )

        st.subheader(
            "Missing Information"
        )

        display_list(
            resume_data.get(
                "missing_information",
                []
            )
        )

    # =====================================================
    # SKILLS
    # =====================================================

    with tab2:

        st.subheader(
            "Extracted Skills"
        )

        skill_categories = [
            (
                "Programming Languages",
                "programming_languages"
            ),
            (
                "Technical Skills",
                "technical_skills"
            ),
            (
                "Frameworks",
                "frameworks"
            ),
            (
                "Databases",
                "databases"
            ),
            (
                "Cloud & Tools",
                "cloud_tools"
            ),
            (
                "Data Tools",
                "data_tools"
            ),
            (
                "AI / ML Tools",
                "ai_ml_tools"
            ),
            (
                "Soft Skills",
                "soft_skills"
            )
        ]

        rows = []

        for label, key in skill_categories:

            values = as_list(
                skills_data.get(
                    key,
                    []
                )
            )

            if values:

                rows.append(
                    {
                        "Category": label,
                        "Skills": ", ".join(
                            str(x)
                            for x in values
                        )
                    }
                )

        if rows:

            df = pd.DataFrame(
                rows
            )

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info(
                "No skill information available."
            )

    # =====================================================
    # SKILL GAP
    # =====================================================

    with tab3:

        st.subheader(
            "🎯 Skill Gap Analysis"
        )

        st.metric(
            "Job Match Percentage",
            f"{match_score:.0f}%"
        )

        st.subheader(
            "✅ Matched Skills"
        )

        display_list(
            skill_gap_data.get(
                "matched_skills",
                []
            )
        )

        st.subheader(
            "🟡 Partial Skills"
        )

        display_list(
            skill_gap_data.get(
                "partial_skills",
                []
            )
        )

        st.subheader(
            "❌ Missing Skills"
        )

        display_list(
            skill_gap_data.get(
                "missing_skills",
                []
            )
        )

        st.subheader(
            "🔥 Priority Skill Gaps"
        )

        display_list(
            skill_gap_data.get(
                "priority_gaps",
                []
            )
        )

        st.subheader(
            "💡 Recommendations"
        )

        display_list(
            skill_gap_data.get(
                "recommendations",
                []
            )
        )

    # =====================================================
    # IMPROVEMENTS
    # =====================================================

    with tab4:

        st.subheader(
            "✨ Resume Improvement Plan"
        )

        improvement_categories = [
            (
                "Summary Improvements",
                "summary_improvements"
            ),
            (
                "Experience Improvements",
                "experience_improvements"
            ),
            (
                "Skills Improvements",
                "skills_improvements"
            ),
            (
                "Project Improvements",
                "project_improvements"
            ),
            (
                "Education Improvements",
                "education_improvements"
            ),
            (
                "ATS Keywords",
                "ats_keywords_to_consider"
            ),
            (
                "Formatting Recommendations",
                "formatting_recommendations"
            ),
            (
                "Action Items",
                "action_items"
            )
        ]

        for title, key in improvement_categories:

            values = as_list(
                improvements_data.get(
                    key,
                    []
                )
            )

            if values:

                st.subheader(
                    title
                )

                display_list(
                    values
                )

    # =====================================================
    # CAREER
    # =====================================================

    with tab5:

        st.subheader(
            "💼 Career Recommendations"
        )

        current_profile = career_data.get(
            "current_profile",
            ""
        )

        if current_profile:
            st.info(
                current_profile
            )

        recommended_roles = as_list(
            career_data.get(
                "recommended_roles",
                []
            )
        )

        for index, role in enumerate(
            recommended_roles,
            start=1
        ):

            if isinstance(
                role,
                dict
            ):

                role_name = role.get(
                    "role",
                    f"Role {index}"
                )

                try:

                    fit = float(
                        role.get(
                            "fit_percentage",
                            0
                        ) or 0
                    )

                except (
                    ValueError,
                    TypeError
                ):

                    fit = 0

                st.markdown(
                    f"### {index}. {role_name}"
                )

                st.metric(
                    "Role Fit",
                    f"{fit:.0f}%"
                )

                reason = role.get(
                    "reason",
                    ""
                )

                if reason:
                    st.write(
                        reason
                    )

                st.write(
                    "**Required Skills**"
                )

                display_list(
                    role.get(
                        "required_skills",
                        []
                    )
                )

                st.write(
                    "**Skill Gaps**"
                )

                display_list(
                    role.get(
                        "skill_gaps",
                        []
                    )
                )

            else:

                st.markdown(
                    f"### {index}. {role}"
                )

        next_steps = career_data.get(
            "next_steps",
            []
        )

        if next_steps:

            st.subheader(
                "Next Steps"
            )

            display_list(
                next_steps
            )

    # =====================================================
    # ROADMAP
    # =====================================================

    with tab6:

        st.subheader(
            "📚 Personalized Learning Roadmap"
        )

        target = roadmap_data.get(
            "target_role",
            job_title
        )

        duration = roadmap_data.get(
            "estimated_duration",
            ""
        )

        experience = roadmap_data.get(
            "experience_level",
            ""
        )

        c1, c2, c3 = st.columns(3)

        with c1:

            st.metric(
                "Target Role",
                target or "Not specified"
            )

        with c2:

            st.metric(
                "Experience",
                experience or "Not specified"
            )

        with c3:

            st.metric(
                "Duration",
                duration or "Not specified"
            )

        priority_order = roadmap_data.get(
            "priority_order",
            []
        )

        if priority_order:

            st.subheader(
                "Priority Order"
            )

            display_list(
                priority_order
            )

        phases = as_list(
            roadmap_data.get(
                "phases",
                []
            )
        )

        for phase in phases:

            if not isinstance(
                phase,
                dict
            ):
                continue

            phase_number = phase.get(
                "phase",
                ""
            )

            title = phase.get(
                "title",
                "Learning Phase"
            )

            phase_duration = phase.get(
                "duration",
                ""
            )

            st.markdown(
                f"### Phase {phase_number}: {title}"
            )

            if phase_duration:

                st.caption(
                    f"Duration: {phase_duration}"
                )

            for label, key in [
                ("Objectives", "objectives"),
                ("Skills", "skills"),
                ("Practice Projects", "practice_projects"),
                ("Completion Criteria", "completion_criteria")
            ]:

                values = phase.get(
                    key,
                    []
                )

                if values:

                    st.write(
                        f"**{label}**"
                    )

                    display_list(
                        values
                    )

            st.divider()

        projects = roadmap_data.get(
            "portfolio_projects",
            []
        )

        if projects:

            st.subheader(
                "🚀 Portfolio Projects"
            )

            display_list(
                projects
            )

        interview = roadmap_data.get(
            "interview_preparation",
            []
        )

        if interview:

            st.subheader(
                "🎤 Interview Preparation"
            )

            display_list(
                interview
            )

    # =====================================================
    # REPORT
    # =====================================================

    with tab7:

        st.subheader(
            "📥 Download Your AI Report"
        )

        st.write(
            "Generate a professional DOCX report containing "
            "your complete resume and skill-gap analysis."
        )

        if st.button(
            "Generate DOCX Report",
            type="primary",
            use_container_width=True
        ):

            try:

                with st.spinner(
                    "Creating professional report..."
                ):

                    report_bytes = generate_report(
                        analysis=result,
                        candidate_name=(
                            resume_data.get(
                                "candidate_name",
                                st.session_state.username
                            )
                        ),
                        target_role=(
                            job_title
                            or roadmap_data.get(
                                "target_role",
                                ""
                            )
                        ),
                        job_title=job_title,
                        company_name=company_name
                    )

                    st.session_state.report_bytes = (
                        report_bytes
                    )

                st.success(
                    "Report generated successfully!"
                )

            except Exception as e:

                st.error(
                    f"Could not generate report: {e}"
                )

        if st.session_state.report_bytes:

            st.download_button(
                label="📥 Download Report",
                data=st.session_state.report_bytes,
                file_name="AI_Resume_Skill_Gap_Report.docx",
                mime=(
                    "application/vnd.openxmlformats-"
                    "officedocument.wordprocessingml.document"
                ),
                use_container_width=True
            )


# =========================================================
# HISTORY PAGE
# =========================================================

def history_page():

    st.title(
        "📚 My Analysis History"
    )

    try:

        analyses = get_user_analyses(
            st.session_state.user_id
        )

    except Exception as e:

        st.error(
            f"Could not load history: {e}"
        )

        return

    if not analyses:

        st.info(
            "You haven't analyzed any resumes yet."
        )

        if st.button(
            "Analyze Resume"
        ):

            st.session_state.page = "Analyzer"

            st.rerun()

        return

    rows = []

    for analysis in analyses:

        rows.append(
            {
                "Job Title": analysis.get(
                    "job_title",
                    ""
                ),

                "Company": analysis.get(
                    "company_name",
                    ""
                ),

                "Date": analysis.get(
                    "created_at",
                    ""
                ),

                "Match": (
                    f"{float(analysis.get('match_percentage', 0)):.0f}%"
                )
            }
        )

    if rows:

        df = pd.DataFrame(
            rows
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

    st.divider()

    st.subheader(
        "Analysis Records"
    )

    for analysis in analyses:

        job = analysis.get(
            "job_title",
            "Unknown Job"
        )

        company = analysis.get(
            "company_name",
            ""
        )

        date = analysis.get(
            "created_at",
            ""
        )

        with st.expander(
            f"📄 {job} "
            f"{'— ' + company if company else ''}"
        ):

            st.write(
                f"**Date:** {date}"
            )

            result = analysis.get(
                "result"
            )

            if result:

                data = get_analysis_data(
                    result.get(
                        "resume_analysis",
                        {}
                    )
                )

                try:

                    score = float(
                        data.get(
                            "ats_score",
                            0
                        ) or 0
                    )

                except (
                    ValueError,
                    TypeError
                ):

                    score = 0

                st.metric(
                    "ATS Score",
                    f"{score:.0f}%"
                )


# =========================================================
# MAIN APPLICATION
# =========================================================

def main():

    # -----------------------------------------------------
    # Authentication
    # -----------------------------------------------------

    if not st.session_state.logged_in:

        if st.session_state.page == "Register":

            register_page()

        else:

            login_page()

        return

    # -----------------------------------------------------
    # Logged-in application
    # -----------------------------------------------------

    sidebar()

    if st.session_state.page == "Dashboard":

        dashboard_page()

    elif st.session_state.page == "Analyzer":

        analyzer_page()

    elif st.session_state.page == "History":

        history_page()

    else:

        dashboard_page()


# =========================================================
# APPLICATION ENTRY POINT
# =========================================================

if __name__ == "__main__":
    main()

