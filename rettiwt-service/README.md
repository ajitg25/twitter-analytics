# Rettiwt Service

A Node.js microservice that wraps the [Rettiwt-API](https://github.com/Rishikant181/Rettiwt-API) library and exposes REST endpoints for the Python Twitter Analytics app.

## Quick Start

### 1. Install Dependencies

```bash
cd rettiwt-service
npm install
```

### 2. Configure (Optional)

For authenticated features (posting, DMs, analytics), you need to generate an API key:

```bash
# Login to Twitter and get API key
npx rettiwt-api auth login
```

Then add the API key to your `.env` file:

```
RETTIWT_API_KEY=your_api_key_here
```

### 3. Start the Service

```bash
npm start
```

The service will run on `http://localhost:3001` by default.

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Health check |
| `GET /api/user/:username` | Get user details by username |
| `GET /api/user/:username/tweets` | Get user's tweets |
| `GET /api/user/:username/followers` | Get user's followers |
| `GET /api/user/:username/following` | Get accounts user follows |
| `GET /api/tweets/search?query=...` | Search for tweets |
| `GET /api/tweet/:tweetId` | Get tweet details |

## Guest Mode vs Authenticated Mode

**Important**: Guest mode has very limited functionality. For full access, you need to generate an API key.

| Feature | Guest Mode | Authenticated |
|---------|------------|---------------|
| View public profiles | ⚠️ Limited | ✅ |
| View public tweets | ⚠️ Limited | ✅ |
| Search tweets | ✅ | ✅ |
| Get followers/following | ❌ | ✅ |
| Post tweets | ❌ | ✅ |
| Access DMs | ❌ | ✅ |
| Get analytics | ❌ | ✅ |

### Generating an API Key

To get full functionality, you need to generate an API key from your Twitter cookies:

```bash
# Run the Rettiwt auth command
npx rettiwt-api auth login

# Follow the prompts to log in to Twitter
# The API key will be generated and displayed

# Add it to your .env file
echo "RETTIWT_API_KEY=your_api_key_here" >> ../.env
```

## Response Format

All responses are transformed to match the Twitter API v2 format for compatibility with the existing Python codebase:

```json
{
  "data": {
    "id": "123456789",
    "username": "example",
    "name": "Example User",
    "public_metrics": {
      "followers_count": 1000,
      "following_count": 500,
      "tweet_count": 200
    }
  }
}
```

## Important Notes

⚠️ **Account Risk**: Using Rettiwt-API with your account's cookies carries a small risk of account suspension by Twitter. Use at your own discretion.

⚠️ **Terms of Service**: This may violate Twitter's Terms of Service. Intended for personal/educational use only.

⚠️ **Stability**: Rettiwt-API is an unofficial library and may break when Twitter changes their internal APIs.

