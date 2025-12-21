# Twitter OAuth & MongoDB Setup Guide

This guide will help you set up Twitter OAuth authentication and MongoDB database for your Twitter Analytics Dashboard.

## 📋 Prerequisites

- Twitter Developer Account
- MongoDB Atlas Account (free tier available)
- Python 3.8+

## 🐦 Step 1: Set Up Twitter OAuth 2.0

### 1.1 Create Twitter Developer Account

1. Go to [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard)
2. Sign in with your Twitter account
3. Apply for a developer account (if you don't have one)
4. Create a new Project and App

### 1.2 Configure OAuth 2.0 Settings

1. In your app settings, go to **"User authentication settings"**
2. Click **"Set up"** or **"Edit"**
3. Configure the following:

   **App permissions:**
   - ✅ Read

   **Type of App:**
   - ✅ Web App, Automated App or Bot

   **App info:**
   - **Callback URI / Redirect URL:** `http://localhost:8501`
   - **Website URL:** `http://localhost:8501` (or your production URL)

4. Save your settings

### 1.3 Get Your Credentials

1. Go to **"Keys and tokens"** tab
2. Copy your:
   - **Client ID** (OAuth 2.0 Client ID)
   - **Client Secret** (OAuth 2.0 Client Secret)
   - **Bearer Token** (for API calls)

⚠️ **Important:** Keep these credentials secret!

## 🗄️ Step 2: Set Up MongoDB Atlas

### 2.1 Create MongoDB Account

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Sign up for a free account
3. Create a new cluster (free tier M0 is sufficient)

### 2.2 Configure Database Access

1. In MongoDB Atlas, go to **"Database Access"**
2. Click **"Add New Database User"**
3. Create a user with:
   - Username: `your_username`
   - Password: `your_secure_password`
   - Database User Privileges: **Read and write to any database**

### 2.3 Configure Network Access

1. Go to **"Network Access"**
2. Click **"Add IP Address"**
3. For development, click **"Allow Access from Anywhere"** (0.0.0.0/0)
   - ⚠️ For production, restrict to specific IPs

### 2.4 Get Connection String

1. Go to **"Database"** → **"Connect"**
2. Choose **"Connect your application"**
3. Copy the connection string:
   ```
   mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
4. Replace `<username>` and `<password>` with your database user credentials

## ⚙️ Step 3: Configure Environment Variables

### 3.1 Create `.env` File

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your credentials:

```bash
# Twitter API Configuration
TWITTER_BEARER_TOKEN=your_bearer_token_here

# Twitter OAuth 2.0 Configuration
TWITTER_CLIENT_ID=your_client_id_here
TWITTER_CLIENT_SECRET=your_client_secret_here
REDIRECT_URI=http://localhost:8501

# MongoDB Configuration
MONGODB_URI=mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
DATABASE_NAME=twitter_analytics
```

### 3.2 For Streamlit Cloud Deployment

If deploying to Streamlit Cloud:

1. Go to your app settings in Streamlit Cloud
2. Navigate to **"Secrets"**
3. Add the following in TOML format:

```toml
TWITTER_BEARER_TOKEN = "your_bearer_token_here"
TWITTER_CLIENT_ID = "your_client_id_here"
TWITTER_CLIENT_SECRET = "your_client_secret_here"
REDIRECT_URI = "https://your-app-url.streamlit.app"
MONGODB_URI = "mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority"
DATABASE_NAME = "twitter_analytics"
```

⚠️ **Important:** Update `REDIRECT_URI` to match your Streamlit Cloud URL!

## 📦 Step 4: Install Dependencies

Install the required packages:

```bash
pip install -r requirements.txt
```

Or install individually:

```bash
pip install streamlit plotly pandas pymongo python-dotenv requests
```

## 🚀 Step 5: Run the Application

### Local Development

```bash
streamlit run main.py
```

The app will open at `http://localhost:8501`

### Test Authentication

1. Open the app
2. Try to upload a file (without signing in)
3. You should see the authentication modal
4. Click "Sign in with Twitter/X"
5. Authorize the app
6. You'll be redirected back and authenticated!

## 🔍 Troubleshooting

### OAuth Issues

**Problem:** "Invalid redirect URI"
- **Solution:** Make sure the redirect URI in your Twitter app settings matches exactly with your `.env` file

**Problem:** "Authentication failed"
- **Solution:** Check that your Client ID and Client Secret are correct

### MongoDB Issues

**Problem:** "Connection failed"
- **Solution:** 
  - Verify your connection string is correct
  - Check that your IP is whitelisted in Network Access
  - Ensure username/password are correct

**Problem:** "Authentication failed"
- **Solution:** Make sure you're using the database user credentials, not your Atlas account credentials

### General Issues

**Problem:** App shows "OAuth is not configured"
- **Solution:** Make sure your `.env` file exists and contains the Twitter credentials

**Problem:** "Module not found" errors
- **Solution:** Run `pip install -r requirements.txt`

## 📊 Database Collections

The app creates the following MongoDB collections:

### `users`
Stores authenticated user information:
- `twitter_id`: User's Twitter ID (unique)
- `username`: Twitter username
- `name`: Display name
- `profile_image_url`: Profile picture URL
- `verified`: Verification status
- `created_at`: First login timestamp
- `last_login`: Last login timestamp

### `user_data`
Stores upload metadata:
- `user_id`: Reference to users collection
- `upload_date`: When data was uploaded
- `stats`: Summary statistics (tweets, followers, etc.)
- `account_info`: Account information
- `profile_info`: Profile information

### `tweets`
Stores individual tweets for growth tracking:
- `user_id`: Reference to users collection
- `tweet_id`: Unique tweet ID
- `created_at`: Tweet creation date
- `full_text`: Tweet content
- `favorite_count`: Number of likes
- `retweet_count`: Number of retweets
- `is_reply`: Whether it's a reply
- `is_retweet`: Whether it's a retweet

## 🎯 Next Steps

1. **Test the authentication flow** - Sign in and upload data
2. **Verify database storage** - Check MongoDB Atlas to see your data
3. **Customize features** - Add more premium features for authenticated users
4. **Deploy to production** - Deploy to Streamlit Cloud with proper credentials

## 🔐 Security Best Practices

1. **Never commit `.env` file** - It's in `.gitignore` by default
2. **Use environment variables** - Don't hardcode credentials
3. **Rotate secrets regularly** - Update your Twitter and MongoDB credentials periodically
4. **Restrict database access** - Use specific IP whitelisting in production
5. **Use HTTPS in production** - Always use secure connections

## 📚 Additional Resources

- [Twitter OAuth 2.0 Documentation](https://developer.twitter.com/en/docs/authentication/oauth-2-0)
- [MongoDB Atlas Documentation](https://docs.atlas.mongodb.com/)
- [Streamlit Secrets Management](https://docs.streamlit.io/streamlit-community-cloud/get-started/deploy-an-app/connect-to-data-sources/secrets-management)

## 💡 Features Enabled by Authentication

✅ **Upload personal Twitter data**
✅ **Save analytics history**
✅ **Track growth over time**
✅ **Compare multiple uploads**
✅ **Access premium insights**
✅ **Export detailed reports**

---

**Need help?** Open an issue on GitHub or contact support.
