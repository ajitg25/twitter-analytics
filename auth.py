"""Twitter Authentication Module - Rettiwt Service + MongoDB"""

import os
import streamlit as st
from datetime import datetime
import requests
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass


def init_auth_state():
    """Initialize authentication state in session"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    if 'rettiwt_cookies' not in st.session_state:
        st.session_state.rettiwt_cookies = None


def logout():
    """Logout user and clear session"""
    st.session_state.authenticated = False
    st.session_state.user_info = None
    st.session_state.rettiwt_cookies = None
    
    # Logout from Rettiwt service (clears .env cookies)
    try:
        service_url = os.getenv('RETTIWT_SERVICE_URL', 'http://localhost:3001')
        requests.post(f"{service_url}/api/auth/logout", timeout=5)
    except:
        pass


def is_authenticated():
    """Check if user is authenticated"""
    return st.session_state.get('authenticated', False) and st.session_state.get('user_info') is not None


def get_current_user():
    """Get current authenticated user info"""
    return st.session_state.get('user_info')


def show_login_button():
    """Display Twitter login button or handle auth flow"""
    service_url = os.getenv('RETTIWT_SERVICE_URL', 'http://localhost:3001')
    
    try:
        response = requests.get(f"{service_url}/api/auth/status", timeout=5)
        if response.status_code != 200:
            st.error("⚠️ Rettiwt service error")
            return
            
        data = response.json()
        
        # If authenticated via Rettiwt service, sync to session
        if data.get('authenticated') and data.get('user'):
            user = data.get('user')
            cookies = data.get('cookies')
            
            st.session_state.authenticated = True
            st.session_state.user_info = {
                'id': user.get('id'),
                'username': user.get('username'),
                'name': user.get('name'),
                'profile_image_url': user.get('profile_image_url'),
                'verified': user.get('verified', False),
                'followers_count': user.get('followers_count'),
                'following_count': user.get('following_count'),
                'tweet_count': user.get('tweet_count'),
                'authenticated_at': datetime.now().isoformat()
            }
            
            if cookies:
                st.session_state.rettiwt_cookies = cookies
                st.session_state.user_info['rettiwt_cookies'] = cookies
            
            # Save to MongoDB
            try:
                from database import Database
                db = Database()
                if db.is_connected():
                    db.create_or_update_user(st.session_state.user_info)
            except Exception as e:
                print(f"DB Save Error: {e}")
            
            st.rerun()
            return
        
        # If auth in progress, show complete button
        if data.get('auth_in_progress'):
            st.info("🔐 Login browser is open. Complete login in the browser window.")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ I've Logged In", type="primary", use_container_width=True):
                    _complete_auth(service_url)
            with col2:
                if st.button("❌ Cancel", use_container_width=True):
                    try:
                        requests.post(f"{service_url}/api/auth/cancel", timeout=5)
                    except:
                        pass
                    st.rerun()
            return
        
        # Show login button
        if st.button("🐦 Sign in with X", type="primary", use_container_width=True):
            _start_auth(service_url)
                
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Rettiwt service not running. Start it with: `cd rettiwt-service && npm start`")
    except Exception as e:
        st.error(f"Connection error: {e}")


def _start_auth(service_url: str):
    """Start Rettiwt browser auth"""
    try:
        response = requests.post(f"{service_url}/api/auth/start", timeout=10)
        if response.status_code == 200:
            st.success("✅ Browser window opened! Please log in to Twitter/X.")
            st.info("After logging in and seeing your feed, click the button below.")
            st.rerun()
        elif response.status_code == 409:
            st.warning("Auth already in progress. Complete login in the browser window.")
            st.rerun()
        else:
            st.error(f"Failed to start auth: {response.json().get('error')}")
    except Exception as e:
        st.error(f"Error starting auth: {e}")


def _complete_auth(service_url: str):
    """Complete auth - get cookies and fetch user info"""
    try:
        with st.spinner("🔄 Completing authentication..."):
            response = requests.post(f"{service_url}/api/auth/complete", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                cookies = data.get('cookies')
                user = data.get('user')
                
                # If user info wasn't returned, fetch it via API
                if not user and cookies:
                    st.info("Fetching user info...")
                    # We need to get username somehow - for now ask user
                    username = st.text_input("Enter your Twitter username (without @):")
                    if username:
                        user_response = requests.get(f"{service_url}/api/user/{username}", timeout=10)
                        if user_response.status_code == 200:
                            user_data = user_response.json().get('data', {})
                            user = {
                                'id': user_data.get('id'),
                                'username': user_data.get('username'),
                                'name': user_data.get('name'),
                                'profile_image_url': user_data.get('profile_image_url'),
                                'verified': user_data.get('verified', False),
                                'followers_count': user_data.get('public_metrics', {}).get('followers_count'),
                                'following_count': user_data.get('public_metrics', {}).get('following_count'),
                                'tweet_count': user_data.get('public_metrics', {}).get('tweet_count'),
                            }
                
                if user:
                    st.session_state.authenticated = True
                    st.session_state.user_info = {
                        'id': user.get('id'),
                        'username': user.get('username'),
                        'name': user.get('name'),
                        'profile_image_url': user.get('profile_image_url'),
                        'verified': user.get('verified', False),
                        'followers_count': user.get('followers_count'),
                        'following_count': user.get('following_count'),
                        'tweet_count': user.get('tweet_count'),
                        'authenticated_at': datetime.now().isoformat()
                    }
                    
                    if cookies:
                        st.session_state.rettiwt_cookies = cookies
                        st.session_state.user_info['rettiwt_cookies'] = cookies
                    
                    # Save to MongoDB
                    try:
                        from database import Database
                        db = Database()
                        if db.is_connected():
                            db.create_or_update_user(st.session_state.user_info)
                            st.success(f"✅ Logged in as @{user.get('username')} - Saved to database!")
                    except Exception as e:
                        st.success(f"✅ Logged in as @{user.get('username')}")
                        print(f"DB Save Error: {e}")
                    
                    st.rerun()
                else:
                    st.error("Login failed - could not get user info. Please try again.")
                    
            elif response.status_code == 401:
                st.warning("⚠️ Please complete login in the browser window first")
            else:
                error_msg = response.json().get('error', 'Unknown error')
                st.error(f"Auth failed: {error_msg}")
                
    except Exception as e:
        st.error(f"Error completing auth: {e}")


def show_user_profile():
    """Display authenticated user profile"""
    user = get_current_user()
    
    if not user:
        return
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        profile_img = user.get('profile_image_url', '')
        st.markdown(f"""
            <div style="
                background: white;
                padding: 20px;
                border-radius: 15px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                text-align: center;
            ">
                <img src="{profile_img}" 
                     style="border-radius: 50%; width: 80px; height: 80px; margin-bottom: 10px;"
                     onerror="this.style.display='none'">
                <h3 style="margin: 10px 0;">{user.get('name', '')} {'✓' if user.get('verified') else ''}</h3>
                <p style="color: #657786; margin: 5px 0;">@{user.get('username', '')}</p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚪 Logout", use_container_width=True, type="secondary"):
            logout()
            st.rerun()
