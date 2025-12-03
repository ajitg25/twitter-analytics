# Twitter Analytics - Available Engagement Metrics

## Summary

Based on the analysis of your Twitter archive data, here's what engagement metrics are available:

### ✅ AVAILABLE Metrics

1. **Likes (favorite_count)** - Number of likes/favorites on each tweet
2. **Retweets (retweet_count)** - Number of retweets for each tweet

### ❌ NOT AVAILABLE Metrics

Unfortunately, the following metrics are **NOT included** in the Twitter archive export:

1. **Impressions/Views (impression_count, view_count)** - How many times your tweets were viewed
2. **Replies (reply_count)** - Number of replies to your tweets
3. **Quote Tweets (quote_count)** - Number of quote tweets
4. **Bookmarks (bookmark_count)** - Number of times your tweets were bookmarked

## Why Are Impressions/Views Not Available?

Twitter's data archive export has **limited engagement metrics**. The archive primarily focuses on:
- Your tweet content and metadata
- Your followers and following lists
- Your likes and DMs
- Basic engagement (likes and retweets only)

**Impressions and view counts are NOT included** in the standard Twitter archive export because:
1. Twitter considers this analytics data separate from your personal data archive
2. These metrics are only available through Twitter Analytics dashboard or API
3. The archive is designed for data portability, not comprehensive analytics

## What You CAN Analyze

With your current Twitter archive, you can analyze:

### Tweet Engagement
- ✅ **Likes** - Total likes per tweet
- ✅ **Retweets** - Total retweets per tweet
- ✅ **Tweet content** - Full text of all your tweets
- ✅ **Tweet timing** - When you posted (date, time, day of week)
- ✅ **Tweet types** - Original tweets, replies, retweets

### Network Analysis
- ✅ **Followers** - Who follows you
- ✅ **Following** - Who you follow
- ✅ **Mutual connections** - People who follow you back
- ✅ **One-sided follows** - People you follow who don't follow back

### Content Analysis
- ✅ **Hashtags** - Most used hashtags
- ✅ **Mentions** - Who you mention most
- ✅ **Activity patterns** - Best posting times
- ✅ **Liked tweets** - Tweets you've liked

## Alternative Ways to Get Impressions/Views

If you need impression and view data, you have these options:

### 1. Twitter Analytics Dashboard (Web)
- Go to https://analytics.twitter.com
- View impressions, engagements, profile visits
- Export data for the last 90 days
- **Limitation**: Only recent data (90 days)

### 2. Twitter API v2
- Use Twitter's API with elevated access
- Fetch tweet metrics programmatically
- Requires API keys and developer account
- **Limitation**: Rate limits and API access requirements

### 3. Third-Party Analytics Tools
- Tools like Hootsuite, Buffer, Sprout Social
- Provide comprehensive analytics
- **Limitation**: Usually paid, and only track from when you start using them

## Current Analytics Capabilities

Your current setup can provide insights like:

```
📊 Tweet Performance
- Total tweets: 335
- Average likes per tweet
- Average retweets per tweet
- Most liked tweets
- Most retweeted tweets

📈 Engagement Trends
- Engagement over time
- Best performing content
- Optimal posting times
- Content mix (original vs replies vs retweets)

👥 Network Insights
- Follower growth patterns
- Mutual connection rate
- Engagement rate with followers
```

## Recommendation

Since **impressions/views are not available** in the Twitter archive:

1. **For historical data**: Unfortunately, if you didn't track it before, historical impression data is not recoverable

2. **For future tracking**: 
   - Enable Twitter Analytics and export data regularly
   - Consider using a social media management tool
   - Use Twitter API to track metrics programmatically

3. **Work with available data**:
   - Focus on likes and retweets as engagement indicators
   - Analyze content patterns and timing
   - Use follower growth as a proxy for reach

## Available Fields in Your Twitter Archive

Complete list of tweet fields in your data:
- created_at
- display_text_range
- edit_info
- entities (hashtags, mentions, URLs)
- extended_entities (media)
- **favorite_count** ✅
- favorited
- full_text
- id / id_str
- in_reply_to_* (reply information)
- lang
- possibly_sensitive
- **retweet_count** ✅
- retweeted
- source
- truncated

---

**Bottom Line**: Your Twitter archive includes **likes and retweets** but does **NOT include impressions/views**. These metrics are only available through Twitter Analytics or the API, not in the data export.
