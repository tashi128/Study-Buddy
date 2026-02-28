"""
Premium Landing Page - Study Buddy
Modern, minimal, Apple-inspired design with premium SaaS aesthetics
"""

import streamlit as st
from auth import auth_db, is_authenticated, get_current_user
from oauth_handler import OAuthHandler


# Hide default Streamlit elements
st.markdown("""
<style>
    header {visibility: hidden;}
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


def show_landing_page():
    """Display premium animated landing page"""
    if not st.session_state.get("_landing_page_config_set"):
        st.set_page_config(
            page_title="Study Buddy - Where Intelligence Meets Learning",
            page_icon="🧠",
            layout="wide",
            initial_sidebar_state="collapsed"
        )
        st.session_state._landing_page_config_set = True
    
    # Premium CSS styling
    premium_css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Manrope:wght@400;500;600;700&display=swap');

    :root {
        --rose-100: #fff7f5;
        --rose-200: #fce8e6;
        --rose-300: #f6d7d4;
        --rose-500: #d78b95;
        --rose-700: #7d4550;
        --ink-700: #4d2d35;
        --ink-900: #2e1a1f;
        --card-bg: rgba(255, 253, 252, 0.62);
        --card-border: rgba(255, 255, 255, 0.75);
        --card-shadow: rgba(169, 103, 116, 0.26);
    }

    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }

    html, body {
        width: 100%;
        min-height: 100%;
        overflow-x: hidden;
    }

    header, footer, #MainMenu, .stDeployButton {
        display: none !important;
    }

    .main {
        padding: 0 !important;
        background: transparent !important;
    }

    .stApp {
        min-height: 100vh !important;
        margin: 0 !important;
        padding: 0 !important;
        background:
            radial-gradient(circle at 10% 15%, rgba(255, 244, 238, 0.98) 0%, rgba(255, 244, 238, 0) 40%),
            radial-gradient(circle at 85% 12%, rgba(251, 216, 225, 0.65) 0%, rgba(251, 216, 225, 0) 45%),
            radial-gradient(circle at 75% 80%, rgba(243, 205, 215, 0.55) 0%, rgba(243, 205, 215, 0) 42%),
            linear-gradient(120deg, #f8e2d8 0%, #f9e9e2 30%, #f8ece6 58%, #f5dbd8 100%) !important;
        animation: silkShift 22s ease-in-out infinite alternate;
    }

    @keyframes silkShift {
        0% { filter: saturate(100%); }
        100% { filter: saturate(112%); }
    }

    .ambient-stage {
        position: fixed;
        inset: 0;
        pointer-events: none;
        z-index: 1;
        overflow: hidden;
    }

    .smoke-layer {
        position: absolute;
        width: 72vw;
        height: 72vw;
        border-radius: 50%;
        filter: blur(55px);
        opacity: 0.45;
        mix-blend-mode: screen;
    }

    .smoke-1 {
        top: -22vw;
        left: -14vw;
        background: radial-gradient(circle, rgba(255, 239, 231, 0.9) 0%, rgba(255, 239, 231, 0) 70%);
        animation: driftOne 22s ease-in-out infinite;
    }

    .smoke-2 {
        top: 14vh;
        right: -18vw;
        background: radial-gradient(circle, rgba(248, 210, 220, 0.8) 0%, rgba(248, 210, 220, 0) 72%);
        animation: driftTwo 30s ease-in-out infinite;
    }

    .smoke-3 {
        bottom: -22vh;
        left: 22vw;
        background: radial-gradient(circle, rgba(252, 225, 218, 0.72) 0%, rgba(252, 225, 218, 0) 75%);
        animation: driftThree 26s ease-in-out infinite;
    }

    @keyframes driftOne {
        0%, 100% { transform: translate(0, 0) scale(1); }
        50% { transform: translate(10vw, 6vh) scale(1.08); }
    }

    @keyframes driftTwo {
        0%, 100% { transform: translate(0, 0) scale(1); }
        50% { transform: translate(-12vw, -5vh) scale(1.05); }
    }

    @keyframes driftThree {
        0%, 100% { transform: translate(0, 0) scale(1); }
        50% { transform: translate(-8vw, -8vh) scale(1.1); }
    }

    .sparkle-field {
        position: absolute;
        inset: 0;
    }

    .spark {
        position: absolute;
        width: 4px;
        height: 4px;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.95);
        box-shadow: 0 0 12px rgba(255, 255, 255, 0.75);
        animation: twinkle 5s ease-in-out infinite;
    }

    .spark:nth-child(2n) { width: 3px; height: 3px; animation-duration: 6s; }
    .spark:nth-child(3n) { width: 5px; height: 5px; animation-duration: 7s; }
    .spark:nth-child(1) { top: 12%; left: 7%; animation-delay: -1s; }
    .spark:nth-child(2) { top: 22%; left: 18%; animation-delay: -2.5s; }
    .spark:nth-child(3) { top: 30%; left: 88%; animation-delay: -1.2s; }
    .spark:nth-child(4) { top: 40%; left: 70%; animation-delay: -3.4s; }
    .spark:nth-child(5) { top: 58%; left: 12%; animation-delay: -2.1s; }
    .spark:nth-child(6) { top: 64%; left: 44%; animation-delay: -0.8s; }
    .spark:nth-child(7) { top: 74%; left: 80%; animation-delay: -3.1s; }
    .spark:nth-child(8) { top: 8%; left: 58%; animation-delay: -4.4s; }
    .spark:nth-child(9) { top: 82%; left: 55%; animation-delay: -2.9s; }
    .spark:nth-child(10) { top: 48%; left: 92%; animation-delay: -1.7s; }
    .spark:nth-child(11) { top: 14%; left: 42%; animation-delay: -3.8s; }
    .spark:nth-child(12) { top: 88%; left: 24%; animation-delay: -4.7s; }

    @keyframes twinkle {
        0%, 100% { opacity: 0.12; transform: scale(0.5); }
        40% { opacity: 0.95; transform: scale(1); }
        75% { opacity: 0.3; transform: scale(0.75); }
    }

    .petal-rain {
        position: absolute;
        inset: -10vh 0 0;
    }

    .petal {
        position: absolute;
        top: -12vh;
        width: 14px;
        height: 20px;
        border-radius: 70% 45% 70% 45%;
        background: linear-gradient(160deg, #ffd8e5 0%, #f1aebb 90%);
        opacity: 0.7;
        box-shadow: 0 0 10px rgba(240, 173, 188, 0.48);
        animation: petalDrop linear infinite;
    }

    .petal:before {
        content: "";
        position: absolute;
        left: 48%;
        top: 10%;
        width: 1px;
        height: 68%;
        background: rgba(204, 120, 142, 0.35);
        transform: rotate(8deg);
    }

    .petal.p1 { left: 4%; animation-duration: 10s; animation-delay: -1s; }
    .petal.p2 { left: 10%; animation-duration: 13s; animation-delay: -5s; transform: scale(0.8); }
    .petal.p3 { left: 16%; animation-duration: 11s; animation-delay: -2.2s; }
    .petal.p4 { left: 24%; animation-duration: 15s; animation-delay: -8s; transform: scale(1.1); }
    .petal.p5 { left: 33%; animation-duration: 12s; animation-delay: -6s; transform: scale(0.75); }
    .petal.p6 { left: 40%; animation-duration: 14s; animation-delay: -3s; }
    .petal.p7 { left: 48%; animation-duration: 10.5s; animation-delay: -7.5s; transform: scale(0.9); }
    .petal.p8 { left: 56%; animation-duration: 16s; animation-delay: -4s; }
    .petal.p9 { left: 64%; animation-duration: 12.5s; animation-delay: -9.5s; transform: scale(1.05); }
    .petal.p10 { left: 72%; animation-duration: 11.2s; animation-delay: -5.6s; }
    .petal.p11 { left: 80%; animation-duration: 14.2s; animation-delay: -3.4s; transform: scale(0.85); }
    .petal.p12 { left: 88%; animation-duration: 13.6s; animation-delay: -10.2s; }
    .petal.p13 { left: 94%; animation-duration: 17s; animation-delay: -4.8s; transform: scale(0.8); }

    @keyframes petalDrop {
        0% {
            transform: translateY(-12vh) translateX(0) rotate(0deg);
            opacity: 0;
        }
        8% {
            opacity: 0.78;
        }
        60% {
            transform: translateY(62vh) translateX(18px) rotate(180deg);
        }
        100% {
            transform: translateY(118vh) translateX(-22px) rotate(365deg);
            opacity: 0.2;
        }
    }

    .hero-content {
        position: relative;
        z-index: 20;
        text-align: center;
        max-width: 880px;
        margin: 0 auto;
        width: 100%;
    }

    .hero-headline {
        font-family: 'Cormorant Garamond', serif;
        font-size: clamp(52px, 9vw, 94px);
        font-weight: 700;
        letter-spacing: -1.5px;
        color: var(--ink-900);
        margin: 0 0 16px 0;
        line-height: 1.02;
        animation: introRise 1s cubic-bezier(0.2, 0.8, 0.2, 1);
        text-shadow: 0 1px 0 rgba(255, 255, 255, 0.55);
    }

    .hero-tagline {
        font-family: 'Manrope', sans-serif;
        font-size: clamp(15px, 2.2vw, 21px);
        font-weight: 500;
        color: rgba(77, 45, 53, 0.86);
        letter-spacing: 0.16em;
        margin: 0 0 38px 0;
        text-transform: uppercase;
        animation: introRise 1s cubic-bezier(0.2, 0.8, 0.2, 1) 0.15s both;
    }

    @keyframes introRise {
        from { opacity: 0; transform: translateY(22px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .glass-card {
        background: var(--card-bg);
        border: 1px solid var(--card-border);
        border-radius: 26px;
        padding: 44px 38px;
        max-width: 560px;
        margin: 0 auto;
        box-shadow: 0 24px 70px var(--card-shadow);
        backdrop-filter: blur(14px);
        position: relative;
        z-index: 18;
    }

    .google-auth-btn {
        width: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
        text-decoration: none;
        margin: 12px 0;
        padding: 15px 24px;
        border-radius: 14px;
        border: 1px solid rgba(125, 69, 80, 0.18);
        background: rgba(255, 255, 255, 0.85);
        color: var(--ink-700);
        font-family: 'Manrope', sans-serif;
        font-size: 15px;
        font-weight: 700;
        letter-spacing: 0.02em;
        transition: transform 0.25s ease, box-shadow 0.25s ease;
        box-shadow: 0 8px 28px rgba(120, 78, 90, 0.2);
    }

    .google-auth-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 14px 34px rgba(120, 78, 90, 0.28);
    }

    .google-logo {
        width: 19px;
        height: 19px;
        display: inline-block;
    }

    .divider {
        text-align: center;
        margin: 20px 0;
        color: rgba(77, 45, 53, 0.6);
        font-family: 'Manrope', sans-serif;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.24em;
        text-transform: uppercase;
    }

    .divider:before,
    .divider:after {
        content: "";
        display: inline-block;
        width: 44px;
        height: 1px;
        background: rgba(125, 69, 80, 0.26);
        margin: 0 12px;
        vertical-align: middle;
    }

    .stButton > button {
        border-radius: 14px !important;
        border: 1px solid rgba(125, 69, 80, 0.32) !important;
        color: var(--ink-700) !important;
        background: rgba(255, 255, 255, 0.78) !important;
        font-family: 'Manrope', sans-serif !important;
        font-weight: 700 !important;
        font-size: 15px !important;
        min-height: 46px !important;
        transition: all 0.2s ease !important;
    }

    .stButton > button:hover {
        border-color: rgba(125, 69, 80, 0.5) !important;
        box-shadow: 0 8px 24px rgba(125, 69, 80, 0.2) !important;
        transform: translateY(-1px);
    }

    .stTextInput label, .stTextInput p {
        color: var(--ink-700) !important;
        font-family: 'Manrope', sans-serif !important;
        font-weight: 600 !important;
    }

    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.86) !important;
        border: 1px solid rgba(125, 69, 80, 0.22) !important;
        border-radius: 12px !important;
        color: var(--ink-900) !important;
        font-family: 'Manrope', sans-serif !important;
    }

    .stSuccess, .stError, .stInfo {
        border-radius: 12px !important;
        font-family: 'Manrope', sans-serif !important;
    }

    @media (max-width: 768px) {
        .glass-card { padding: 28px 22px; border-radius: 22px; }
        .hero-headline { font-size: clamp(44px, 12vw, 58px); }
        .hero-tagline { font-size: 14px; letter-spacing: 0.12em; margin-bottom: 26px; }
        .petal { opacity: 0.55; }
    }
    </style>
    """
    
    st.markdown(premium_css, unsafe_allow_html=True)
    
    # Initialize session state
    if 'show_login' not in st.session_state:
        st.session_state.show_login = False
    if 'show_signup' not in st.session_state:
        st.session_state.show_signup = False
    
    # Full-screen layout with containers
    hero_placeholder = st.container()
    
    with hero_placeholder:
        # Animated background layers
        st.markdown("""
        <div class="ambient-stage">
            <div class="smoke-layer smoke-1"></div>
            <div class="smoke-layer smoke-2"></div>
            <div class="smoke-layer smoke-3"></div>
            <div class="sparkle-field">
                <span class="spark"></span><span class="spark"></span><span class="spark"></span><span class="spark"></span>
                <span class="spark"></span><span class="spark"></span><span class="spark"></span><span class="spark"></span>
                <span class="spark"></span><span class="spark"></span><span class="spark"></span><span class="spark"></span>
            </div>
            <div class="petal-rain">
                <span class="petal p1"></span><span class="petal p2"></span><span class="petal p3"></span><span class="petal p4"></span>
                <span class="petal p5"></span><span class="petal p6"></span><span class="petal p7"></span><span class="petal p8"></span>
                <span class="petal p9"></span><span class="petal p10"></span><span class="petal p11"></span><span class="petal p12"></span>
                <span class="petal p13"></span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Hero content
        col1, col2, col3 = st.columns([1, 1.2, 1])
        
        with col2:
            # Hero headline and tagline
            st.markdown("""
            <div class="hero-content">
                <h1 class="hero-headline">Welcome to Study Buddy</h1>
                <p class="hero-tagline">Where Intelligence Meets Learning</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br><br>", unsafe_allow_html=True)
            
            # Check if showing login or signup form
            if not st.session_state.show_login and not st.session_state.show_signup:
                # Show CTA buttons
                # Google button
                google_auth_url = OAuthHandler.get_google_auth_url()
                if google_auth_url:
                    st.markdown(f'''
                    <a href="{google_auth_url}" target="_self" class="google-auth-btn">
                        <svg class="google-logo" viewBox="0 0 24 24" aria-hidden="true">
                            <path fill="#EA4335" d="M12 10.2v3.9h5.4c-.2 1.3-1.6 3.9-5.4 3.9-3.2 0-5.9-2.7-5.9-6s2.7-6 5.9-6c1.8 0 3.1.8 3.8 1.4l2.6-2.5C16.7 3.3 14.5 2.4 12 2.4 6.9 2.4 2.8 6.6 2.8 11.9S6.9 21.4 12 21.4c6.9 0 9.2-4.9 9.2-7.4 0-.5-.1-.9-.1-1.2z"/>
                            <path fill="#34A853" d="M3.8 7.3l3.2 2.4C7.8 8 9.7 6.6 12 6.6c1.8 0 3.1.8 3.8 1.4l2.6-2.5C16.7 3.3 14.5 2.4 12 2.4 8.4 2.4 5.2 4.4 3.8 7.3z"/>
                            <path fill="#FBBC05" d="M12 21.4c2.4 0 4.5-.8 6-2.2l-2.8-2.2c-.8.6-1.8 1-3.2 1-2.7 0-5-1.8-5.8-4.2l-3.2 2.5c1.4 3 4.5 5.1 9 5.1z"/>
                            <path fill="#4285F4" d="M21.2 14c.1-.4.2-.9.2-1.5 0-.5-.1-.9-.1-1.2H12v3.9h5.4c-.3 1.4-1.2 2.5-2.5 3.2l2.8 2.2c1.6-1.5 3.5-4.1 3.5-7.2z"/>
                        </svg>
                        Continue with Google
                    </a>
                    ''', unsafe_allow_html=True)
                
                st.markdown('<div class="divider">Or</div>', unsafe_allow_html=True)
                
                # Sign in/up buttons
                btn_col1, btn_col2 = st.columns(2, gap="small")
                
                with btn_col1:
                    if st.button("Sign In", key="cta_signin", use_container_width=True):
                        st.session_state.show_login = True
                        st.rerun()
                
                with btn_col2:
                    if st.button("Create Account", key="cta_create", use_container_width=True):
                        st.session_state.show_signup = True
                        st.rerun()
            
            # Login Form
            elif st.session_state.show_login:
                st.markdown("<h2 style='color: #41242c; font-family: Manrope, sans-serif; font-size: 30px; margin-bottom: 20px; text-align: center; font-weight: 700;'>Sign In</h2>", unsafe_allow_html=True)

                with st.form("login_form", clear_on_submit=False):
                    st.text_input("Email", placeholder="you@example.com", key="login_email")
                    st.text_input("Password", type="password", placeholder="••••••••", key="login_password")
                    login_submitted = st.form_submit_button("Sign In", use_container_width=True)

                if login_submitted:
                    login_email = st.session_state.get("login_email", "").strip()
                    login_password = st.session_state.get("login_password", "")
                    if not login_email or not login_password:
                        st.error("❌ Please fill in all fields")
                    else:
                        result = auth_db.login_user(login_email, login_password)
                        if result["success"]:
                            st.session_state.authenticated = True
                            st.session_state.user_id = result["user_id"]
                            st.session_state.user_name = result["name"]
                            st.session_state.user_email = login_email
                            st.session_state.session_token = result["session_token"]
                            st.success("✅ Login successful!")
                            st.rerun()
                        else:
                            st.error("❌ " + result["error"])
                
                st.markdown("<p style='text-align: center; color: rgba(77,45,53,0.78); margin-top: 20px; font-size: 14px; font-family: Manrope, sans-serif;'>Don't have an account?</p>", unsafe_allow_html=True)
                
                col_a, col_b = st.columns([1, 1])
                with col_a:
                    if st.button("Sign Up", use_container_width=True, key="to_signup"):
                        st.session_state.show_login = False
                        st.session_state.show_signup = True
                        st.rerun()
                with col_b:
                    if st.button("← Back", use_container_width=True, key="back_login"):
                        st.session_state.show_login = False
                        st.rerun()
            
            # Sign Up Form
            elif st.session_state.show_signup:
                st.markdown("<h2 style='color: #41242c; font-family: Manrope, sans-serif; font-size: 30px; margin-bottom: 20px; text-align: center; font-weight: 700;'>Create Account</h2>", unsafe_allow_html=True)

                with st.form("signup_form", clear_on_submit=False):
                    st.text_input("Full Name", placeholder="John Doe", key="signup_name")
                    st.text_input("Email", placeholder="you@example.com", key="signup_email")
                    st.text_input("Password", type="password", placeholder="••••••••", key="signup_password")

                    st.markdown("""
                    <div style='background: rgba(255, 255, 255, 0.72); border: 1px solid rgba(125, 69, 80, 0.22); border-radius: 12px; padding: 12px 15px; margin: 8px 0; font-size: 12px; color: rgba(66, 35, 42, 0.92); font-family: Manrope, sans-serif;'>
                    <strong>Password Requirements:</strong><br>
                    ✓ Min 8 characters &nbsp; ✓ 1 uppercase (A-Z) &nbsp; ✓ 1 lowercase (a-z)<br>
                    ✓ 1 number (0-9) &nbsp; ✓ 1 special char (!@#$%^&*)
                    </div>
                    """, unsafe_allow_html=True)

                    st.text_input("Confirm Password", type="password", placeholder="••••••••", key="signup_confirm")
                    signup_submitted = st.form_submit_button("Create Account", use_container_width=True)

                if signup_submitted:
                    signup_name = st.session_state.get("signup_name", "").strip()
                    signup_email = st.session_state.get("signup_email", "").strip()
                    signup_password = st.session_state.get("signup_password", "")
                    signup_confirm = st.session_state.get("signup_confirm", "")
                    if not signup_name or not signup_email or not signup_password or not signup_confirm:
                        st.error("❌ Please fill in all fields")
                    elif signup_password != signup_confirm:
                        st.error("❌ Passwords do not match")
                    else:
                        result = auth_db.register_user(signup_name, signup_email, signup_password)
                        if result["success"]:
                            st.success("✅ Account created! Please sign in.")
                            st.session_state.show_signup = False
                            st.session_state.show_login = True
                            st.rerun()
                        else:
                            st.error("❌ " + result["error"])
                
                st.markdown("<p style='text-align: center; color: rgba(77,45,53,0.78); margin-top: 20px; font-size: 14px; font-family: Manrope, sans-serif;'>Already have an account?</p>", unsafe_allow_html=True)
                
                col_a, col_b = st.columns([1, 1])
                with col_a:
                    if st.button("Sign In", use_container_width=True, key="to_signin"):
                        st.session_state.show_signup = False
                        st.session_state.show_login = True
                        st.rerun()
                with col_b:
                    if st.button("← Back", use_container_width=True, key="back_signup"):
                        st.session_state.show_signup = False
                        st.rerun()


if __name__ == "__main__":
    show_landing_page()
