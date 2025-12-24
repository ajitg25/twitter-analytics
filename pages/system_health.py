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

# === COMMUNITY FUNDING NOTE ===
st.markdown("""
<style>
    .funding-card {
        background: linear-gradient(135deg, #1DA1F2 0%, #00BA7C 100%);
        color: white;
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        margin: 40px 0 20px 0;
        box-shadow: 0 10px 25px rgba(29, 161, 242, 0.15);
    }
    .funding-btn {
        background: white;
        color: #1DA1F2;
        padding: 10px 25px;
        border-radius: 25px;
        text-decoration: none;
        font-weight: bold;
        display: inline-block;
        margin: 10px 10px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    .funding-btn:hover { transform: translateY(-2px); box-shadow: 0 6px 15px rgba(0,0,0,0.15); color: #00BA7C; }
</style>
<div class="funding-card">
<h3 style="color: white; margin-top: 0;">🤝 Make it Community Driven</h3>
<p style="font-size: 15px; line-height: 1.6; margin-bottom: 25px; color: white; opacity: 0.95;">
I want to make this a community driven project now. It's possible to get the analytics for all users 
with <b>significantly less costs</b> than the <a href="https://docs.x.com/x-api/introduction#api-tiers-&-pricing" target="_blank" style="color: white; text-decoration: underline;">$100-$5000/mo X charges</a> if we do a collective effort. 
<br><br>
<b>$200/month</b> is what it takes to power this for everyone. 
Since this is now <b>open source</b>, your contributions directly help keep the public instance running.
</p>
<div style="display: flex; justify-content: center; flex-wrap: wrap; gap: 10px;">
<a href="https://github.com/ajitg25/twitter-analytics" target="_blank" class="funding-btn">💻 GitHub Repo</a>
<a href="https://github.com/sponsors/ajitg25" target="_blank" class="funding-btn">💖 GitHub Sponsor</a>
<a href="https://buymeacoffee.com/ajit_gupta" target="_blank" class="funding-btn">☕ Buy Me a Coffee</a>
</div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br><br><div style='text-align: center; color: #8899a6;'>Twitter Analytics Dashboard v2.0 <br> Made with ❤️ by @unfiltered_ajit</div>", unsafe_allow_html=True)
