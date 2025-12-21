import streamlit as st
import os
from auth import get_current_user, is_authenticated, TWITTER_CLIENT_ID, REDIRECT_URI

# Set page config
st.set_page_config(page_title="System Health", page_icon="🛡️", layout="wide")

# Access Control
if not is_authenticated():
    st.error("🔒 Please sign in first.")
    if st.button("Go to Home"):
        st.switch_page("main.py")
    st.stop()

user = get_current_user()
# Only unfiltered_ajit allowed
if user.get('username') != 'unfiltered_ajit':
    st.error("🚫 Access Denied: Administrator Only.")
    if st.button("Go to Home"):
        st.switch_page("main.py")
    st.stop()

st.title("🛡️ System Health & Diagnostics")
st.markdown("---")

# Section 1: OAuth Configuration
st.subheader("🔑 OAuth 2.0 Configuration")
col1, col2 = st.columns(2)

with col1:
    st.info("**Application Environment Settings**")
    st.write(f"**Redirect URI:** `{REDIRECT_URI}`")
    st.write(f"**Environment:** `{os.getenv('APP_ENV', 'production')}`")

with col2:
    st.info("**Twitter API Credentials**")
    st.write(f"**Client ID Present:** {'✅ Yes' if TWITTER_CLIENT_ID else '❌ No'}")
    if TWITTER_CLIENT_ID:
        # Masked Client ID for safety even in admin view
        st.code(f"{TWITTER_CLIENT_ID[:8]}...{TWITTER_CLIENT_ID[-8:]}", language="text")
    
    # Check Client Secret
    from auth import TWITTER_CLIENT_SECRET
    st.write(f"**Client Secret Present:** {'✅ Yes' if TWITTER_CLIENT_SECRET else '❌ No'}")

st.markdown("---")

# Section 2: Troubleshooting Guide
st.subheader("🛠️ Connection Diagnostics")
st.warning("If you encounter 'Refused to Connect' or 'Callback Mismatch':")

diag_col1, diag_col2 = st.columns(2)
with diag_col1:
    st.markdown("""
    **1. Twitter Developer Portal Check**
    - Ensure your App is set to **OAuth 2.0**
    - App type must be **Web App, Android, or iOS**
    - Callback URL must match EXACTLY:
    """)
    st.code(REDIRECT_URI, language="text")

with diag_col2:
    st.markdown("""
    **2. Streamlit Secrets Check**
    - Login to Streamlit Cloud dashboard
    - Go to **Settings** -> **Secrets**
    - Ensure variables are correctly named:
      - `TWITTER_CLIENT_ID`
      - `TWITTER_CLIENT_SECRET`
      - `REDIRECT_URI`
    """)

st.markdown("---")

# # Section 3: User Info Raw Data
# with st.expander("👤 View Admin User Raw Data"):
#     st.json(user)

if st.button("⬅️ Back to Dashboard"):
    st.switch_page("main.py")

st.markdown("<br><br><div style='text-align: center; color: #8899a6;'>Twitter Analytics Dashboard v2.0 <br> Made with ❤️ by @unfiltered_ajit</div>", unsafe_allow_html=True)
