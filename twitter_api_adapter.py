"""
Twitter API Adapter - Abstraction layer for switching between Official Twitter API and Rettiwt-API

Usage:
    Set environment variable TWITTER_OFFICIAL=true to use official Twitter API
    Otherwise, uses Rettiwt-API (free alternative)
"""

import os
import requests
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List, Any
import streamlit as st


class TwitterAPIBase(ABC):
    """Abstract base class for Twitter API implementations"""
    
    @abstractmethod
    def get_my_user_info(self) -> Optional[Dict]:
        """Get the authenticated user's information"""
        pass
    
    @abstractmethod
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user details by username"""
        pass
    
    @abstractmethod
    def get_recent_tweets(self, user_id: str, max_results: int = 100) -> List[Dict]:
        """Get user's recent tweets"""
        pass
    
    @abstractmethod
    def get_followers(self, user_id: str, max_results: int = 100) -> Optional[Dict]:
        """Get user's followers"""
        pass
    
    @abstractmethod
    def get_following(self, user_id: str, max_results: int = 100) -> Optional[Dict]:
        """Get accounts the user is following"""
        pass
    
    @abstractmethod
    def search_tweets(self, query: str, max_results: int = 50) -> List[Dict]:
        """Search for tweets"""
        pass
    
    @abstractmethod
    def get_all_tweets_since(self, user_id: str, days: int = 30) -> List[Dict]:
        """Get all tweets from user within the last N days (with pagination)"""
        pass


class OfficialTwitterAPI(TwitterAPIBase):
    """Official Twitter API v2 implementation"""
    
    def __init__(self, access_token: str, refresh_token: Optional[str] = None):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.base_url = "https://api.twitter.com/2"
        self.headers = {
            'Authorization': f'Bearer {access_token}'
        }
        self._user_id_cache = None
    
    def _refresh_access_token(self) -> bool:
        """Refresh the access token if expired"""
        if not self.refresh_token:
            return False
        
        try:
            from auth import refresh_access_token
            new_tokens = refresh_access_token(self.refresh_token)
            
            if new_tokens:
                self.access_token = new_tokens.get('access_token')
                self.refresh_token = new_tokens.get('refresh_token', self.refresh_token)
                self.headers['Authorization'] = f'Bearer {self.access_token}'
                
                # Update session state
                if 'user_info' in st.session_state:
                    st.session_state.user_info['access_token'] = self.access_token
                    st.session_state.user_info['refresh_token'] = self.refresh_token
                
                return True
        except Exception as e:
            print(f"Token Refresh Exception: {e}")
        return False
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make an API request with automatic token refresh"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.request(method, url, headers=self.headers, params=params)
            
            if response.status_code == 401:
                if self._refresh_access_token():
                    response = requests.request(method, url, headers=self.headers, params=params)
                else:
                    st.error("🔑 Session expired. Please log in again.")
                    return None
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                st.warning("⚠️ Rate limit reached. Try again in 15 minutes.")
                return None
            else:
                st.error(f"API Error: {response.text}")
                return None
                
        except Exception as e:
            st.error(f"Request failed: {e}")
            return None
    
    def get_my_user_info(self) -> Optional[Dict]:
        """Get the authenticated user's information"""
        if self._user_id_cache:
            return self._user_id_cache
        
        params = {'user.fields': 'id,username,name,profile_image_url,public_metrics,verified,created_at'}
        result = self._make_request('GET', '/users/me', params)
        
        if result and 'data' in result:
            self._user_id_cache = result['data']
            return result['data']
        return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user details by username"""
        params = {'user.fields': 'id,username,name,description,profile_image_url,public_metrics,verified,created_at'}
        result = self._make_request('GET', f'/users/by/username/{username}', params)
        
        if result and 'data' in result:
            return result['data']
        return None
    
    def get_recent_tweets(self, user_id: str, max_results: int = 100) -> List[Dict]:
        """Get user's recent tweets from the last 90 days"""
        ninety_days_ago = datetime.now(timezone.utc) - timedelta(days=90)
        start_time_str = ninety_days_ago.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        params = {
            'max_results': min(max_results, 100),
            'start_time': start_time_str,
            'tweet.fields': 'created_at,public_metrics,text,author_id',
            'expansions': 'author_id',
            'user.fields': 'username,name,profile_image_url'
        }
        
        all_tweets = []
        next_token = None
        max_pages = 32  # Up to 3,200 tweets
        
        for _ in range(max_pages):
            if next_token:
                params['pagination_token'] = next_token
            
            result = self._make_request('GET', f'/users/{user_id}/tweets', params)
            
            if result and 'data' in result:
                all_tweets.extend(result['data'])
                next_token = result.get('meta', {}).get('next_token')
                if not next_token:
                    break
            else:
                break
        
        return all_tweets
    
    def get_followers(self, user_id: str, max_results: int = 100) -> Optional[Dict]:
        """Get user's followers"""
        params = {
            'max_results': min(max_results, 1000),
            'user.fields': 'created_at,description,profile_image_url,public_metrics,verified'
        }
        
        result = self._make_request('GET', f'/users/{user_id}/followers', params)
        return result
    
    def get_following(self, user_id: str, max_results: int = 100) -> Optional[Dict]:
        """Get accounts the user is following"""
        params = {
            'max_results': min(max_results, 1000),
            'user.fields': 'created_at,description,profile_image_url,public_metrics,verified'
        }
        
        result = self._make_request('GET', f'/users/{user_id}/following', params)
        return result
    
    def search_tweets(self, query: str, max_results: int = 50) -> List[Dict]:
        """Search for tweets (requires elevated access)"""
        params = {
            'query': query,
            'max_results': min(max_results, 100),
            'tweet.fields': 'created_at,public_metrics,author_id'
        }
        
        result = self._make_request('GET', '/tweets/search/recent', params)
        
        if result and 'data' in result:
            return result['data']
        return []
    
    def get_all_tweets_since(self, user_id: str, days: int = 30) -> List[Dict]:
        """
        Get all tweets from user within the last N days (paginated)
        Official API has rate limits, so we paginate carefully
        """
        all_tweets = []
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        pagination_token = None
        
        while True:
            params = {
                'max_results': 100,
                'tweet.fields': 'created_at,public_metrics,author_id',
                'start_time': cutoff_date.isoformat()
            }
            
            if pagination_token:
                params['pagination_token'] = pagination_token
            
            result = self._make_request('GET', f'/users/{user_id}/tweets', params)
            
            if not result or 'data' not in result:
                break
            
            all_tweets.extend(result['data'])
            
            # Check for more pages
            pagination_token = result.get('meta', {}).get('next_token')
            if not pagination_token:
                break
        
        return all_tweets


class RettiwtAPI(TwitterAPIBase):
    """Rettiwt-API implementation (free alternative)"""
    
    def __init__(self, username: str = None, service_url: str = None, cookies: str = None):
        self.username = username  # The logged-in user's username
        self.service_url = service_url or os.getenv('RETTIWT_SERVICE_URL', 'http://localhost:3001')
        self.cookies = cookies  # User's auth cookies (auth_token;ct0 format)
        self._user_cache = {}
    
    def _make_request(self, endpoint: str, params: Dict = None, timeout: int = 30) -> Optional[Dict]:
        """Make a request to the Rettiwt service"""
        url = f"{self.service_url}{endpoint}"
        
        # Build headers with user's cookies if available
        headers = {}
        if self.cookies:
            headers['X-Rettiwt-Cookies'] = self.cookies
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=timeout)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                error_msg = response.json().get('error', 'Unknown error')
                st.warning(f"Rettiwt API: {error_msg}")
                return None
                
        except requests.exceptions.ConnectionError:
            st.error("⚠️ Rettiwt service not running. Start it with: cd rettiwt-service && npm start")
            return None
        except Exception as e:
            st.error(f"Rettiwt request failed: {e}")
            return None
    
    def _check_service_health(self) -> bool:
        """Check if the Rettiwt service is running"""
        try:
            response = requests.get(f"{self.service_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_my_user_info(self) -> Optional[Dict]:
        """Get the authenticated user's information"""
        if not self.username:
            st.error("Username required for Rettiwt API")
            return None
        
        if self.username in self._user_cache:
            return self._user_cache[self.username]
        
        result = self._make_request(f'/api/user/{self.username}')
        
        if result and 'data' in result:
            self._user_cache[self.username] = result['data']
            return result['data']
        return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user details by username"""
        if username in self._user_cache:
            return self._user_cache[username]
        
        result = self._make_request(f'/api/user/{username}')
        
        if result and 'data' in result:
            self._user_cache[username] = result['data']
            return result['data']
        return None
    
    def get_recent_tweets(self, user_id: str, max_results: int = 100) -> List[Dict]:
        """Get user's recent tweets (uses username, not user_id)"""
        # For Rettiwt, we need to use username
        # Try to find username from cache or user_id mapping
        username = self._get_username_from_id(user_id)
        
        if not username:
            st.warning("Could not resolve username from user ID for Rettiwt API")
            return []
        
        result = self._make_request(f'/api/user/{username}/tweets', {'count': max_results})
        
        if result and 'data' in result:
            return result['data']
        return []
    
    def get_followers(self, user_id: str, max_results: int = 100) -> Optional[Dict]:
        """Get user's followers"""
        username = self._get_username_from_id(user_id)
        
        if not username:
            return None
        
        result = self._make_request(f'/api/user/{username}/followers', {'count': max_results})
        return result
    
    def get_following(self, user_id: str, max_results: int = 100) -> Optional[Dict]:
        """Get accounts the user is following"""
        username = self._get_username_from_id(user_id)
        
        if not username:
            return None
        
        result = self._make_request(f'/api/user/{username}/following', {'count': max_results})
        return result
    
    def search_tweets(self, query: str, max_results: int = 50) -> List[Dict]:
        """Search for tweets"""
        result = self._make_request('/api/tweets/search', {'query': query, 'count': max_results})
        
        if result and 'data' in result:
            return result['data']
        return []
    
    def get_all_tweets_since(self, user_id: str, days: int = 30) -> List[Dict]:
        """
        Get all tweets from user within the last N days (with automatic pagination)
        Uses the /api/user/:username/tweets/all endpoint
        """
        username = self._get_username_from_id(user_id)
        
        if not username:
            st.warning("Could not resolve username from user ID for Rettiwt API")
            return []
        
        result = self._make_request(
            f'/api/user/{username}/tweets/all', 
            {'days': days, 'maxTweets': 500},
            timeout=120  # Longer timeout for pagination
        )
        
        if result and 'data' in result:
            return result['data']
        return []
    
    def _get_username_from_id(self, user_id: str) -> Optional[str]:
        """Try to get username from user_id using cache or session"""
        # Check cache for user with this ID
        for username, user_data in self._user_cache.items():
            if user_data.get('id') == user_id:
                return username
        
        # Check session state
        if 'user_info' in st.session_state:
            if st.session_state.user_info.get('id') == user_id:
                return st.session_state.user_info.get('username')
        
        # If we have a default username set, use that
        if self.username:
            return self.username
        
        return None


def get_twitter_api(access_token: str = None, refresh_token: str = None, username: str = None, cookies: str = None) -> TwitterAPIBase:
    """
    Factory function to get the appropriate Twitter API implementation
    
    Environment Variables:
        TWITTER_OFFICIAL=true  - Use official Twitter API (requires OAuth tokens)
        TWITTER_OFFICIAL=false - Use Rettiwt-API (free, requires running rettiwt-service)
    
    Args:
        access_token: OAuth access token (for official API)
        refresh_token: OAuth refresh token (for official API)
        username: Twitter username (for Rettiwt API)
        cookies: User's Rettiwt cookies (for multi-user support)
    
    Returns:
        TwitterAPIBase implementation
    """
    use_official = os.getenv('TWITTER_OFFICIAL', 'false').lower() == 'true'
    
    if use_official:
        if not access_token:
            raise ValueError("Access token required for official Twitter API")
        return OfficialTwitterAPI(access_token, refresh_token)
    else:
        return RettiwtAPI(username=username, cookies=cookies)


def get_api_mode() -> str:
    """Get the current API mode for display purposes"""
    use_official = os.getenv('TWITTER_OFFICIAL', 'false').lower() == 'true'
    return "Official Twitter API" if use_official else "Rettiwt API (Free)"

