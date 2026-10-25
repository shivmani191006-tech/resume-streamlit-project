import re
import streamlit as st

from db_manager import DatabaseManager


# =========================================================
# DATABASE
# =========================================================

db = DatabaseManager()


# =========================================================
# SESSION STATE INITIALIZATION
# =========================================================

def initialize_session():
    """
    Initialize authentication-related
    Streamlit session variables.
    """

    if "logged_in" not in st.session_state:

        st.session_state.logged_in = False

    if "user" not in st.session_state:

        st.session_state.user = None

    if "user_id" not in st.session_state:

        st.session_state.user_id = None


# =========================================================
# VALIDATE EMAIL
# =========================================================

def is_valid_email(
    email: str
) -> bool:
    """
    Validate email format.
    """

    pattern = (
        r"^[A-Za-z0-9._%+-]+"
        r"@[A-Za-z0-9.-]+\."
        r"[A-Za-z]{2,}$"
    )

    return bool(
        re.match(
            pattern,
            email
        )
    )


# =========================================================
# VALIDATE PASSWORD
# =========================================================

def validate_password(
    password: str
) -> tuple[bool, str]:
    """
    Validate password strength.
    """

    if len(password) < 6:

        return (
            False,
            "Password must contain at least 6 characters."
        )

    return (
        True,
        ""
    )


# =========================================================
# REGISTER USER
# =========================================================

def register_user(
    username: str,
    email: str,
    password: str,
    confirm_password: str,
    full_name: str = ""
) -> dict:
    """
    Register a new user.
    """

    username = username.strip()

    email = email.strip().lower()

    full_name = full_name.strip()

    # -----------------------------------------------------
    # Required fields
    # -----------------------------------------------------

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

    if not password:

        return {
            "success": False,
            "message": "Password is required."
        }

    # -----------------------------------------------------
    # Username validation
    # -----------------------------------------------------

    if len(username) < 3:

        return {
            "success": False,
            "message": (
                "Username must contain at least 3 characters."
            )
        }

    # -----------------------------------------------------
    # Email validation
    # -----------------------------------------------------

    if not is_valid_email(email):

        return {
            "success": False,
            "message": (
                "Please enter a valid email address."
            )
        }

    # -----------------------------------------------------
    # Password validation
    # -----------------------------------------------------

    valid_password, password_message = (
        validate_password(password)
    )

    if not valid_password:

        return {
            "success": False,
            "message": password_message
        }

    # -----------------------------------------------------
    # Confirm password
    # -----------------------------------------------------

    if password != confirm_password:

        return {
            "success": False,
            "message": "Passwords do not match."
        }

    # -----------------------------------------------------
    # Create user
    # -----------------------------------------------------

    result = db.create_user(
        username=username,
        email=email,
        password=password,
        full_name=full_name
    )

    if result["success"]:

        return {
            "success": True,
            "message": (
                "Registration successful. "
                "You can now log in."
            ),
            "user_id": result.get(
                "user_id"
            )
        }

    return {
        "success": False,
        "message": result.get(
            "error",
            "Registration failed."
        )
    }


# =========================================================
# LOGIN USER
# =========================================================

def login_user(
    username_or_email: str,
    password: str
) -> dict:
    """
    Authenticate a user and create
    a Streamlit session.
    """

    username_or_email = (
        username_or_email.strip()
    )

    if not username_or_email:

        return {
            "success": False,
            "message": (
                "Username or email is required."
            )
        }

    if not password:

        return {
            "success": False,
            "message": "Password is required."
        }

    user = db.authenticate_user(
        username_or_email=username_or_email,
        password=password
    )

    if user is None:

        return {
            "success": False,
            "message": (
                "Invalid username/email or password."
            )
        }

    # -----------------------------------------------------
    # Save user in session
    # -----------------------------------------------------

    st.session_state.logged_in = True

    st.session_state.user = user

    st.session_state.user_id = user["id"]

    return {
        "success": True,
        "message": "Login successful.",
        "user": user
    }


# =========================================================
# LOGOUT
# =========================================================

def logout():
    """
    Log out the current user.
    """

    st.session_state.logged_in = False

    st.session_state.user = None

    st.session_state.user_id = None

    # Optional page state cleanup

    keys_to_remove = [
        "current_resume",
        "current_resume_id",
        "current_job",
        "current_job_id",
        "analysis_result",
        "skill_gap_result",
        "roadmap_result"
    ]

    for key in keys_to_remove:

        if key in st.session_state:

            del st.session_state[key]


# =========================================================
# CHECK LOGIN
# =========================================================

def is_logged_in() -> bool:
    """
    Check whether a user is authenticated.
    """

    initialize_session()

    return bool(
        st.session_state.logged_in
    )


# =========================================================
# GET CURRENT USER
# =========================================================

def get_current_user():
    """
    Return currently logged-in user.
    """

    initialize_session()

    return st.session_state.user


# =========================================================
# GET CURRENT USER ID
# =========================================================

def get_current_user_id():
    """
    Return current user ID.
    """

    initialize_session()

    return st.session_state.user_id


# =========================================================
# LOGIN PAGE
# =========================================================

def show_login_page():
    """
    Display Streamlit login form.
    """

    st.markdown(
        """
        <div style="
            text-align:center;
            padding:20px 0 10px 0;
        ">

            <h1 style="
                color:#4F46E5;
                margin-bottom:5px;
            ">
                🤖 AI Resume & Skill Gap Agent
            </h1>

            <p style="
                color:#64748B;
                font-size:17px;
            ">
                Login to analyze your resume and
                discover your skill gaps.
            </p>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    # -----------------------------------------------------
    # Login form
    # -----------------------------------------------------

    with st.form(
        "login_form",
        clear_on_submit=False
    ):

        st.subheader(
            "🔐 Login"
        )

        username_or_email = st.text_input(
            "Username or Email",
            placeholder="Enter username or email"
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password"
        )

        login_button = st.form_submit_button(
            "Login",
            use_container_width=True
        )

        if login_button:

            result = login_user(
                username_or_email,
                password
            )

            if result["success"]:

                st.success(
                    result["message"]
                )

                st.rerun()

            else:

                st.error(
                    result["message"]
                )

    st.markdown("")

    st.info(
        "Don't have an account? "
        "Use the Register option below."
    )


# =========================================================
# REGISTER PAGE
# =========================================================

def show_register_page():
    """
    Display Streamlit registration form.
    """

    st.markdown(
        """
        <div style="
            text-align:center;
            padding:20px 0 10px 0;
        ">

            <h1 style="
                color:#4F46E5;
            ">
                📝 Create Your Account
            </h1>

            <p style="
                color:#64748B;
                font-size:17px;
            ">
                Start your AI-powered career journey.
            </p>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    # -----------------------------------------------------
    # Registration form
    # -----------------------------------------------------

    with st.form(
        "register_form",
        clear_on_submit=True
    ):

        st.subheader(
            "Create Account"
        )

        full_name = st.text_input(
            "Full Name",
            placeholder="Enter your full name"
        )

        username = st.text_input(
            "Username",
            placeholder="Choose a username"
        )

        email = st.text_input(
            "Email",
            placeholder="you@example.com"
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Minimum 6 characters"
        )

        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
            placeholder="Re-enter your password"
        )

        register_button = st.form_submit_button(
            "Create Account",
            use_container_width=True
        )

        if register_button:

            result = register_user(
                username=username,
                email=email,
                password=password,
                confirm_password=confirm_password,
                full_name=full_name
            )

            if result["success"]:

                st.success(
                    result["message"]
                )

                st.info(
                    "Please go to Login and sign in."
                )

            else:

                st.error(
                    result["message"]
                )


# =========================================================
# AUTHENTICATION UI
# =========================================================

def show_auth_page():
    """
    Display Login/Register interface.
    """

    initialize_session()

    # -----------------------------------------------------
    # Tabs
    # -----------------------------------------------------

    login_tab, register_tab = st.tabs(
        [
            "🔐 Login",
            "📝 Register"
        ]
    )

    with login_tab:

        show_login_page()

    with register_tab:

        show_register_page()


# =========================================================
# PROTECTED PAGE HELPER
# =========================================================

def require_login():
    """
    Stop execution when the user is not logged in.

    Returns:
        True  -> user is logged in
        False -> user is not logged in
    """

    initialize_session()

    if not st.session_state.logged_in:

        st.warning(
            "Please login to access this page."
        )

        st.stop()

    return True


# =========================================================
# USER HEADER
# =========================================================

def show_user_header():
    """
    Display logged-in user information
    in the Streamlit sidebar.
    """

    initialize_session()

    if not st.session_state.logged_in:

        return

    user = st.session_state.user

    st.sidebar.markdown(
        "### 👤 User"
    )

    if user:

        full_name = user.get(
            "full_name"
        )

        username = user.get(
            "username"
        )

        email = user.get(
            "email"
        )

        if full_name:

            st.sidebar.write(
                f"**{full_name}**"
            )

        st.sidebar.caption(
            f"@{username}"
        )

        st.sidebar.caption(
            email
        )

    st.sidebar.divider()

    if st.sidebar.button(
        "🚪 Logout",
        use_container_width=True
    ):

        logout()

        st.rerun()


# =========================================================
# AUTH PAGE ROUTER
# =========================================================

def authentication_required():
    """
    Main authentication router.

    Returns:
        True if logged in.
        False if login page is shown.
    """

    initialize_session()

    if not st.session_state.logged_in:

        show_auth_page()

        return False

    show_user_header()

    return True


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    st.set_page_config(
        page_title="AI Resume Agent",
        page_icon="🤖",
        layout="centered"
    )

    authentication_required()

