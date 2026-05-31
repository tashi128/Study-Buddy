"""
Premium Landing Page - Study Buddy
Modern, minimal, Apple-inspired design with premium SaaS aesthetics
"""

import streamlit as st
from auth import auth_db, is_authenticated, get_current_user, start_guest_session
from oauth_handler import OAuthHandler


def show_landing_page():
    """Display premium animated landing page"""
    
    # Page configuration
    st.set_page_config(
        page_title="Study Buddy - Where Intelligence Meets Learning",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Premium CSS styling
    premium_css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');
    
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    html, body {
        width: 100%;
        height: 100%;
        overflow: hidden;
    }
    
    /* Premium dark background with gradient */
    .stApp {
        background: linear-gradient(135deg, #0f0a1a 0%, #1a0f2e 25%, #2d1b4e 50%, #1a0f2e 75%, #0f0a1a 100%) !important;
        background-size: 400% 400% !important;
        animation: premiumGradient 25s ease infinite !important;
        position: relative;
        min-height: 100vh;
        overflow-y: auto;
    }
    
    @keyframes premiumGradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Premium container */
    .premium-hero {
        width: 100%;
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        padding: 40px 20px;
        overflow: hidden;
    }
    
    /* Animated background elements */
    .glow-background {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        opacity: 0.6;
        pointer-events: none;
    }
    
    .glow-orb {
        position: absolute;
        border-radius: 50%;
        filter: blur(80px);
        opacity: 0.5;
    }
    
    .glow-orb-1 {
        width: 400px;
        height: 400px;
        background: radial-gradient(circle, #ec4899 0%, #d946ef 100%);
        top: -100px;
        left: -100px;
        animation: float-slow 20s ease-in-out infinite;
    }
    
    .glow-orb-2 {
        width: 350px;
        height: 350px;
        background: radial-gradient(circle, #f97316 0%, #ec4899 100%);
        top: 50%;
        right: -150px;
        animation: float-slow-reverse 25s ease-in-out infinite;
    }
    
    .glow-orb-3 {
        width: 300px;
        height: 300px;
        background: radial-gradient(circle, #a855f7 0%, #6366f1 100%);
        bottom: -50px;
        left: 50%;
        animation: float-slow 22s ease-in-out infinite;
    }
    
    @keyframes float-slow {
        0%, 100% { transform: translate(0, 0); }
        25% { transform: translate(30px, -40px); }
        50% { transform: translate(-20px, -80px); }
        75% { transform: translate(-40px, -20px); }
    }
    
    @keyframes float-slow-reverse {
        0%, 100% { transform: translate(0, 0); }
        25% { transform: translate(-30px, 40px); }
        50% { transform: translate(20px, 80px); }
        75% { transform: translate(40px, 20px); }
    }
    
    /* Cherry blossom particles */
    .petal {
        position: absolute;
        pointer-events: none;
    }
    
    @keyframes petal-fall {
        0% {
            opacity: 0;
            transform: translateY(0) rotateZ(0deg);
        }
        10% {
            opacity: 1;
        }
        90% {
            opacity: 1;
        }
        100% {
            opacity: 0;
            transform: translateY(100vh) rotateZ(360deg);
        }
    }
    
    /* Premium content wrapper */
    .hero-content {
        position: relative;
        z-index: 10;
        text-align: center;
        max-width: 900px;
        margin: 0 auto;
    }
    
    /* Premium headline */
    .hero-headline {
        font-family: 'Playfair Display', serif;
        font-size: clamp(48px, 12vw, 96px);
        font-weight: 700;
        letter-spacing: -2px;
        background: linear-gradient(135deg, #ffffff 0%, #f0f0ff 50%, #fca5a5 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 24px;
        animation: headline-fade-in 1.2s cubic-bezier(0.34, 1.56, 0.64, 1);
        line-height: 1.1;
    }
    
    @keyframes headline-fade-in {
        0% {
            opacity: 0;
            transform: translateY(30px);
        }
        100% {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Premium tagline */
    .hero-tagline {
        font-family: 'Space Grotesk', sans-serif;
        font-size: clamp(20px, 5vw, 32px);
        font-weight: 400;
        color: rgba(255, 255, 255, 0.8);
        letter-spacing: 1.5px;
        margin-bottom: 48px;
        animation: tagline-fade-in 1.2s cubic-bezier(0.34, 1.56, 0.64, 1) 0.2s both;
        text-transform: uppercase;
    }
    
    @keyframes tagline-fade-in {
        0% {
            opacity: 0;
            transform: translateY(30px);
        }
        100% {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Glassmorphism card */
    .glass-card {
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 20px;
        padding: 48px 40px;
        max-width: 500px;
        margin: 0 auto;
        box-shadow: 0 20px 80px rgba(236, 72, 153, 0.15);
        animation: card-fade-in 1.2s cubic-bezier(0.34, 1.56, 0.64, 1) 0.4s both;
    }
    
    @keyframes card-fade-in {
        0% {
            opacity: 0;
            transform: translateY(40px);
        }
        100% {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Premium buttons */
    .premium-btn {
        display: inline-block;
        width: 100%;
        padding: 16px 32px;
        margin: 12px 0;
        font-family: 'Space Grotesk', sans-serif;
        font-size: 16px;
        font-weight: 600;
        letter-spacing: 0.5px;
        border: none;
        border-radius: 12px;
        cursor: pointer;
        transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
        text-decoration: none;
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    
    .premium-btn::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: rgba(255, 255, 255, 0.1);
        transition: left 0.4s ease;
        z-index: 0;
    }

    .inapp-browser-warning {
        display: none;
        margin: 0 0 18px 0;
        padding: 14px 16px;
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.18);
        background: rgba(22, 14, 37, 0.82);
        color: rgba(255, 255, 255, 0.9);
        font-family: 'Space Grotesk', sans-serif;
        text-align: left;
    }

    .inapp-browser-warning strong {
        display: block;
        margin-bottom: 6px;
        color: #ffffff;
        font-size: 14px;
    }

    .inapp-browser-warning p {
        margin: 0;
        font-size: 13px;
        line-height: 1.5;
    }

    .inapp-browser-warning code {
        font-size: 12px;
        background: rgba(255, 255, 255, 0.08);
        padding: 2px 6px;
        border-radius: 8px;
    }

    .helper-note {
        margin: 10px 0 18px 0;
        color: rgba(255, 255, 255, 0.72);
        font-family: 'Space Grotesk', sans-serif;
        font-size: 13px;
        line-height: 1.55;
        text-align: center;
    }
    
    .premium-btn:hover::before {
        left: 100%;
    }
    
    .premium-btn span {
        position: relative;
        z-index: 1;
    }
    
    /* Google button */
    .btn-google {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
        box-shadow: 0 12px 40px rgba(79, 172, 254, 0.3);
    }
    
    .btn-google:hover {
        transform: translateY(-4px);
        box-shadow: 0 20px 60px rgba(79, 172, 254, 0.5);
    }
    
    /* Create account button */
    .btn-create {
        background: linear-gradient(135deg, #d946ef 0%, #ec4899 100%);
        color: white;
        box-shadow: 0 12px 40px rgba(217, 70, 239, 0.3);
    }
    
    .btn-create:hover {
        transform: translateY(-4px);
        box-shadow: 0 20px 60px rgba(217, 70, 239, 0.5);
    }
    
    /* Sign in/up text button */
    .text-button {
        background: transparent;
        color: rgba(255, 255, 255, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.3);
        margin-top: 16px;
        font-weight: 500;
    }
    
    .text-button:hover {
        background: rgba(255, 255, 255, 0.1);
        color: white;
        border-color: rgba(255, 255, 255, 0.5);
    }
    
    /* Divider */
    .divider {
        text-align: center;
        margin: 24px 0;
        color: rgba(255, 255, 255, 0.5);
        font-size: 14px;
        font-weight: 500;
        letter-spacing: 1px;
    }
    
    .divider::before,
    .divider::after {
        content: '';
        display: inline-block;
        width: 50px;
        height: 1px;
        background: rgba(255, 255, 255, 0.2);
        margin: 0 12px;
        vertical-align: middle;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .glass-card {
            padding: 32px 24px;
        }
        
        .hero-headline {
            font-size: 48px;
        }
        
        .hero-tagline {
            font-size: 18px;
            margin-bottom: 32px;
        }
    }
    </style>
    """
    
    st.markdown(premium_css, unsafe_allow_html=True)
    
    # Initialize session state
    if 'show_login' not in st.session_state:
        st.session_state.show_login = False
    if 'show_signup' not in st.session_state:
        st.session_state.show_signup = False
    
    # Hero HTML
    hero_html = """
    <div class="premium-hero">
        <div class="glow-background">
            <div class="glow-orb glow-orb-1"></div>
            <div class="glow-orb glow-orb-2"></div>
            <div class="glow-orb glow-orb-3"></div>
        </div>
        
        <div class="hero-content">
            <h1 class="hero-headline">Welcome to Study Buddy</h1>
            <p class="hero-tagline">Where Intelligence Meets Learning</p>
        </div>
    </div>
    """
    
    st.markdown(hero_html, unsafe_allow_html=True)
    
    # Main content area
    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    with col2:
        # Check if showing login or signup form
        if not st.session_state.show_login and not st.session_state.show_signup:
            # Show CTA buttons
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            
            # Google button
            google_auth_url = OAuthHandler.get_google_auth_url()
            if google_auth_url:
                st.markdown("""
                <div id="inapp-browser-warning" class="inapp-browser-warning">
                    <strong>Open Study Buddy in Safari or Chrome</strong>
                    <p>Google sign-in is blocked inside LinkedIn, Instagram, Facebook, and other in-app browsers. Use the browser menu and choose <code>Open in browser</code>, then try Google again.</p>
                </div>
                <script>
                (function() {
                    const ua = navigator.userAgent || "";
                    const isInAppBrowser = /(LinkedInApp|Instagram|FBAN|FBAV|FB_IAB|Messenger|Line|TikTok|Twitter|Snapchat)/i.test(ua);
                    const warning = window.parent.document.getElementById("inapp-browser-warning") || document.getElementById("inapp-browser-warning");
                    if (warning && isInAppBrowser) {
                        warning.style.display = "block";
                    }
                })();
                </script>
                """, unsafe_allow_html=True)
                st.markdown(f'''
                <a href="{google_auth_url}" target="_top" rel="noopener noreferrer" class="premium-btn btn-google">
                    <span>🔵 Continue with Google</span>
                </a>
                ''', unsafe_allow_html=True)

            st.markdown(
                "<p class='helper-note'>For the smoothest experience, open this link in Safari or Chrome. If Google sign-in is blocked, you can still explore Study Buddy in guest mode.</p>",
                unsafe_allow_html=True
            )
            
            st.markdown('<div class="divider">Or</div>', unsafe_allow_html=True)
            
            # Sign in/up buttons
            btn_col1, btn_col2, btn_col3 = st.columns(3, gap="small")
            
            with btn_col1:
                if st.button("Sign In", key="cta_signin", use_container_width=True):
                    st.session_state.show_login = True
                    st.rerun()
            
            with btn_col2:
                if st.button("Create Account", key="cta_create", use_container_width=True):
                    st.session_state.show_signup = True
                    st.rerun()

            with btn_col3:
                if st.button("Guest Mode", key="cta_guest", use_container_width=True):
                    start_guest_session()
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Login Form
        elif st.session_state.show_login:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("<h2 style='color: white; font-family: Space Grotesk; font-size: 28px; margin-bottom: 24px;'>Sign In</h2>", unsafe_allow_html=True)
            
            login_email = st.text_input("Email", placeholder="you@example.com", key="login_email")
            login_password = st.text_input("Password", type="password", placeholder="••••••••", key="login_password")
            
            if st.button("Sign In", use_container_width=True, key="login_submit"):
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
            
            st.markdown("<p style='text-align: center; color: rgba(255,255,255,0.7); margin-top: 20px; font-size: 14px;'>Don't have an account? </p>", unsafe_allow_html=True)
            
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
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Sign Up Form
        elif st.session_state.show_signup:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("<h2 style='color: white; font-family: Space Grotesk; font-size: 28px; margin-bottom: 24px;'>Create Account</h2>", unsafe_allow_html=True)
            
            signup_name = st.text_input("Full Name", placeholder="John Doe", key="signup_name")
            signup_email = st.text_input("Email", placeholder="you@example.com", key="signup_email")
            signup_password = st.text_input("Password", type="password", placeholder="••••••••", key="signup_password")
            
            st.markdown("""
            <div style='background: rgba(124, 58, 237, 0.15); border: 1px solid rgba(124, 58, 237, 0.3); border-radius: 8px; padding: 10px 15px; margin: 8px 0; font-size: 12px; color: rgba(255, 255, 255, 0.85);'>
            <strong>Password Requirements:</strong><br>
            ✓ Min 8 characters &nbsp; ✓ 1 uppercase (A-Z) &nbsp; ✓ 1 lowercase (a-z)<br>
            ✓ 1 number (0-9) &nbsp; ✓ 1 special char (!@#$%^&*)
            </div>
            """, unsafe_allow_html=True)
            
            signup_confirm = st.text_input("Confirm Password", type="password", placeholder="••••••••", key="signup_confirm")
            
            if st.button("Create Account", use_container_width=True, key="signup_submit"):
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
            
            st.markdown("<p style='text-align: center; color: rgba(255,255,255,0.7); margin-top: 20px; font-size: 14px;'>Already have an account? </p>", unsafe_allow_html=True)
            
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
            
            st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    show_landing_page()
