"""Twitter OAuth Authentication Module"""

import os
import streamlit as st
from datetime import datetime
import requests
from urllib.parse import urlencode
import secrets
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

# Twitter OAuth 2.0 Configuration
# IMPORTANT: In production (Streamlit Cloud), set REDIRECT_URI in Secrets to:
# https://twitter-x-analytics.streamlit.app/
TWITTER_CLIENT_ID = os.getenv('TWITTER_CLIENT_ID', st.secrets.get('TWITTER_CLIENT_ID', ''))
TWITTER_CLIENT_SECRET = os.getenv('TWITTER_CLIENT_SECRET', st.secrets.get('TWITTER_CLIENT_SECRET', ''))
REDIRECT_URI = os.getenv('REDIRECT_URI', st.secrets.get('REDIRECT_URI', 'http://localhost:8501'))

# OAuth endpoints
TWITTER_AUTH_URL = "https://twitter.com/i/oauth2/authorize"
TWITTER_TOKEN_URL = "https://api.twitter.com/2/oauth2/token"
TWITTER_USER_URL = "https://api.twitter.com/2/users/me"


def init_auth_state():
    """Initialize authentication state in session"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    if 'oauth_state' not in st.session_state:
        st.session_state.oauth_state = None
    if 'code_verifier' not in st.session_state:
        st.session_state.code_verifier = None
    
    # Try to restore from persistent storage
    _restore_auth_from_cache()


def _get_cache_file():
    """Get path to auth cache file"""
    import tempfile
    cache_dir = Path(tempfile.gettempdir()) / 'twitter_analytics_cache'
    cache_dir.mkdir(exist_ok=True)
    return cache_dir / 'auth_cache.json'


def _save_auth_to_cache():
    """Save authentication state to persistent cache"""
    if st.session_state.get('authenticated') and st.session_state.get('user_info'):
        try:
            import json
            cache_file = _get_cache_file()
            
            cache_data = {
                'authenticated': st.session_state.authenticated,
                'user_info': st.session_state.user_info,
                'cached_at': datetime.now().isoformat()
            }
            
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f)
        except Exception as e:
            # Silent fail - caching is optional
            pass


def _restore_auth_from_cache():
    """Restore authentication state from persistent cache"""
    try:
        import json
        from datetime import timedelta
        
        cache_file = _get_cache_file()
        
        if not cache_file.exists():
            return
        
        with open(cache_file, 'r') as f:
            cache_data = json.load(f)
        
        # Check if cache is recent (within 24 hours)
        cached_at = datetime.fromisoformat(cache_data.get('cached_at', ''))
        if datetime.now() - cached_at > timedelta(hours=24):
            # Cache expired, delete it
            cache_file.unlink()
            return
        
        # Restore session state if not already set
        if not st.session_state.get('authenticated'):
            st.session_state.authenticated = cache_data.get('authenticated', False)
            st.session_state.user_info = cache_data.get('user_info')
            
    except Exception as e:
        # Silent fail - if cache is corrupted, just ignore it
        pass


def clear_auth_cache():
    """Clear persistent authentication cache"""
    try:
        cache_file = _get_cache_file()
        if cache_file.exists():
            cache_file.unlink()
    except Exception:
        pass


def generate_pkce_pair():
    """Generate PKCE code verifier and challenge for OAuth 2.0"""
    import hashlib
    import base64
    
    # Generate code verifier (random string)
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    
    # Generate code challenge (SHA256 hash of verifier)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('utf-8')).digest()
    ).decode('utf-8').rstrip('=')
    
    return code_verifier, code_challenge


def get_twitter_auth_url():
    """Generate Twitter OAuth authorization URL"""
    if not TWITTER_CLIENT_ID:
        return None
    
    # Generate PKCE pair
    code_verifier, code_challenge = generate_pkce_pair()
    
    # Generate state and encode code_verifier in it (base64)
    import base64
    import json
    
    state_data = {
        'state': secrets.token_urlsafe(16),
        'verifier': code_verifier
    }
    
    # Encode state data as base64
    state = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()
    
    # Store in session state as backup
    st.session_state.oauth_state = state_data['state']
    st.session_state.code_verifier = code_verifier
    
    # OAuth parameters
    params = {
        'response_type': 'code',
        'client_id': TWITTER_CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'scope': 'tweet.read users.read offline.access',
        'state': state,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256'
    }
    
    auth_url = f"{TWITTER_AUTH_URL}?{urlencode(params)}"
    return auth_url


def exchange_code_for_token(code):
    """Exchange authorization code for access token"""
    if not TWITTER_CLIENT_ID or not TWITTER_CLIENT_SECRET:
        return None
    
    code_verifier = st.session_state.get('code_verifier')
    if not code_verifier:
        return None
    
    # Token request
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'code_verifier': code_verifier,
        'client_id': TWITTER_CLIENT_ID
    }
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    try:
        response = requests.post(
            TWITTER_TOKEN_URL,
            data=data,
            headers=headers,
            auth=(TWITTER_CLIENT_ID, TWITTER_CLIENT_SECRET)
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Token exchange failed: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error exchanging code for token: {e}")
        return None


def refresh_access_token(refresh_token):
    """Refresh access token using refresh token"""
    if not TWITTER_CLIENT_ID or not TWITTER_CLIENT_SECRET:
        return None
    
    # Token request
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': TWITTER_CLIENT_ID
    }
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    try:
        response = requests.post(
            TWITTER_TOKEN_URL,
            data=data,
            headers=headers,
            auth=(TWITTER_CLIENT_ID, TWITTER_CLIENT_SECRET)
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Token refresh failed: {response.text}")
            return None
    except Exception as e:
        print(f"Error refreshing token: {e}")
        return None


def get_user_info(access_token):
    """Fetch user information from Twitter API"""
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    params = {
        'user.fields': 'id,name,username,profile_image_url,created_at,verified'
    }
    
    try:
        response = requests.get(
            TWITTER_USER_URL,
            headers=headers,
            params=params
        )
        
        if response.status_code == 200:
            return response.json().get('data')
        else:
            st.error(f"Failed to fetch user info: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error fetching user info: {e}")
        return None


def handle_oauth_callback():
    """Handle OAuth callback from Twitter"""
    # Get query parameters
    query_params = st.query_params
    
    code = query_params.get('code')
    state = query_params.get('state')
    error = query_params.get('error')
    
    if error:
        st.error(f"Authentication error: {error}")
        return False
    
    if code and state:
        # Decode state to get verifier
        import base64
        import json
        
        try:
            state_data = json.loads(base64.urlsafe_b64decode(state).decode())
            code_verifier = state_data.get('verifier')
            
            # Store code_verifier in session state for token exchange
            st.session_state.code_verifier = code_verifier
            
        except Exception as e:
            st.error(f"Failed to decode state: {e}")
            return False
        
        # Clear query parameters immediately after extraction to prevent re-processing on rerun
        st.query_params.clear()
        
        # Exchange code for token
        token_data = exchange_code_for_token(code)
        
        if token_data:
            access_token = token_data.get('access_token')
            refresh_token = token_data.get('refresh_token')
            
            # Get user information
            user_info = get_user_info(access_token)
            
            if user_info:
                # Store in session state
                st.session_state.authenticated = True
                st.session_state.user_info = {
                    'id': user_info.get('id'),
                    'username': user_info.get('username'),
                    'name': user_info.get('name'),
                    'profile_image_url': user_info.get('profile_image_url'),
                    'verified': user_info.get('verified', False),
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'authenticated_at': datetime.now().isoformat()
                }
                
                # Save to persistent cache
                _save_auth_to_cache()
                
                # Save to Database (MongoDB)
                try:
                    from database import get_database
                    db = get_database()
                    if db.is_connected():
                        db.create_or_update_user(st.session_state.user_info)
                except Exception as e:
                    print(f"DB Save Error: {e}")
                
                return True
            else:
                # If get_user_info failed (likely 429)
                st.error("📉 Failed to fetch your Twitter profile. This usually means the API Rate Limit was hit. Please wait 15 minutes and try again.")
        else:
            st.error("🚫 Authentication failed during token exchange. The link may have expired.")
    
    return False


def logout():
    """Logout user and clear session"""
    st.session_state.authenticated = False
    st.session_state.user_info = None
    st.session_state.oauth_state = None
    st.session_state.code_verifier = None
    
    # Clear persistent cache
    clear_auth_cache()


def is_authenticated():
    """Check if user is authenticated"""
    return st.session_state.get('authenticated', False)


def get_current_user():
    """Get current authenticated user info"""
    return st.session_state.get('user_info')


def show_login_button():
    """Display Twitter login button"""
    auth_url = get_twitter_auth_url()
    
    if not auth_url:
        st.error("⚠️ Twitter OAuth is not configured. Please set TWITTER_CLIENT_ID in environment variables.")
        st.info("To enable authentication, add your Twitter OAuth credentials to `.env` file or Streamlit secrets.")
        return
    
    st.markdown("""
        <style>
        .twitter-login-btn {
            background: linear-gradient(135deg, #1DA1F2 0%, #0d8bd9 100%);
            color: white;
            padding: 12px 24px;
            border-radius: 25px;
            text-decoration: none;
            font-weight: 600;
            display: inline-block;
            box-shadow: 0 4px 6px rgba(29, 161, 242, 0.3);
            transition: all 0.3s ease;
        }
        .twitter-login-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(29, 161, 242, 0.4);
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
        <div style="text-align: center; margin: 20px 0;">
            <a href="{auth_url}" target="_self" class="twitter-login-btn">
                🐦 Sign in with Twitter/X
            </a>
        </div>
    """, unsafe_allow_html=True)


def show_user_profile():
    """Display authenticated user profile"""
    user = get_current_user()
    
    if not user:
        return
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(f"""
            <div style="
                background: white;
                padding: 20px;
                border-radius: 15px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                text-align: center;
            ">
                <img src="{user.get('profile_image_url', '')}" 
                     style="border-radius: 50%; width: 80px; height: 80px; margin-bottom: 10px;">
                <h3 style="margin: 10px 0;">{user.get('name', '')} {'✓' if user.get('verified') else ''}</h3>
                <p style="color: #657786; margin: 5px 0;">@{user.get('username', '')}</p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚪 Logout", use_container_width=True, type="secondary"):
            logout()
            st.rerun()
