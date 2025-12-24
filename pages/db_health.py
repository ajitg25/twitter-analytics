"""Database Health Check Page"""

import streamlit as st
import os
from database import get_database

# Initialize authentication
from auth import init_auth_state, handle_oauth_callback, get_current_user
init_auth_state()
handle_oauth_callback()

# Page config
st.set_page_config(
    page_title="Database Health Check", 
    page_icon="🏥", 
    layout="wide"
)

# Admin Access Control
ADMIN_USER = "unfiltered_ajit"
user = get_current_user()

if not user or user.get('username') != ADMIN_USER:
    st.error("🚫 Access Denied: You do not have permission to view this page.")
    if st.button("🏠 Back to Safety"):
        st.switch_page("main.py")
    st.stop()

st.title("🏥 Database Health Check")
st.markdown("---")

# Get environment variables
mongodb_uri = os.getenv('MONGODB_URI', st.secrets.get('MONGODB_URI', ''))
database_name = os.getenv('DATABASE_NAME', st.secrets.get('DATABASE_NAME', 'twitter_analytics'))

# Display configuration (hide password)
st.subheader("📋 Configuration")

if mongodb_uri:
    # Mask password in URI
    import re
    masked_uri = re.sub(r'://([^:]+):([^@]+)@', r'://\1:****@', mongodb_uri)
    st.code(f"MONGODB_URI: {masked_uri}", language="text")
else:
    st.error("❌ MONGODB_URI not configured")

st.code(f"DATABASE_NAME: {database_name}", language="text")

st.markdown("---")

# Test connection
st.subheader("🔌 Connection Test")

if st.button("Test Database Connection", type="primary", use_container_width=True):
    with st.spinner("Testing connection..."):
        db = get_database()
        
        if db.is_connected():
            st.success("✅ **Database connected successfully!**")
            
            # Show database info
            try:
                # List collections
                collections = db.db.list_collection_names()
                
                st.markdown("### 📊 Database Information")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Database Name", database_name)
                    st.metric("Collections", len(collections))
                
                with col2:
                    st.markdown("**Collections:**")
                    if collections:
                        for coll in collections:
                            count = db.db[coll].count_documents({})
                            st.write(f"- `{coll}`: {count} documents")
                    else:
                        st.info("No collections yet")
                
                # Test operations
                st.markdown("### 🧪 Test Operations")
                
                # Test write
                try:
                    test_doc = {"test": "health_check", "timestamp": "now"}
                    result = db.db.test_collection.insert_one(test_doc)
                    st.success(f"✅ Write test passed (ID: {result.inserted_id})")
                    
                    # Test read
                    found = db.db.test_collection.find_one({"_id": result.inserted_id})
                    if found:
                        st.success("✅ Read test passed")
                    
                    # Clean up
                    db.db.test_collection.delete_one({"_id": result.inserted_id})
                    st.success("✅ Delete test passed")
                    
                except Exception as e:
                    st.error(f"❌ Operation test failed: {e}")
                
            except Exception as e:
                st.error(f"❌ Error getting database info: {e}")
        else:
            st.error("❌ **Database connection failed!**")
            st.warning("Please check your MongoDB URI and network connection.")
            
            # Common issues
            st.markdown("### 🔍 Common Issues:")
            st.markdown("""
            1. **Invalid URI format** - Check your connection string
            2. **Wrong cluster name** - Should be like `cluster0.xxxxx.mongodb.net`
            3. **Network access** - Make sure your IP is whitelisted in MongoDB Atlas
            4. **Wrong credentials** - Verify username and password
            5. **Database user not created** - Create a database user in MongoDB Atlas
            """)

st.markdown("---")

# Manual URI input for testing
with st.expander("🔧 Test Custom URI"):
    st.markdown("**Test a different MongoDB URI:**")
    
    test_uri = st.text_input(
        "MongoDB URI",
        placeholder="mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority",
        type="password"
    )
    
    if st.button("Test Custom URI"):
        if test_uri:
            try:
                from pymongo import MongoClient
                
                with st.spinner("Testing custom URI..."):
                    client = MongoClient(test_uri, serverSelectionTimeoutMS=5000)
                    client.admin.command('ping')
                    st.success("✅ Custom URI connection successful!")
                    client.close()
            except Exception as e:
                st.error(f"❌ Custom URI connection failed: {e}")
        else:
            st.warning("Please enter a MongoDB URI")

st.markdown("---")

# Instructions
st.subheader("📚 How to Fix Connection Issues")

st.markdown("""
### Step 1: Get Your Correct MongoDB URI

1. Go to [MongoDB Atlas](https://cloud.mongodb.com)
2. Click **"Database"** → **"Connect"**
3. Choose **"Connect your application"**
4. Copy the connection string - it should look like:
   ```
   mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
   
### Step 2: Replace Placeholders

- Replace `<username>` with your database username
- Replace `<password>` with your database password
- The `cluster0.xxxxx` part should be your actual cluster name

### Step 3: Update Your .env File

```bash
MONGODB_URI=mongodb+srv://your_username:your_password@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
DATABASE_NAME=twitter_analytics
```

### Step 4: Whitelist Your IP

1. In MongoDB Atlas, go to **"Network Access"**
2. Click **"Add IP Address"**
3. Add your current IP or use `0.0.0.0/0` for testing (allow from anywhere)

### Step 5: Restart Streamlit

After updating `.env`, restart your Streamlit app for changes to take effect.
""")

# Back button
if st.button("🔙 Back to Main App"):
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
