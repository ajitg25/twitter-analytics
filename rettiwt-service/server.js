/**
 * Twitter API Microservice
 * 
 * Uses Twitter cookies directly to call Twitter's internal GraphQL API.
 * This bypasses Rettiwt library issues with cookie formats.
 */

import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

dotenv.config({ path: '../.env' });

const app = express();
const PORT = process.env.RETTIWT_PORT || 3001;

app.use(cors());
app.use(express.json());

// Parse cookies - supports per-request cookies via header OR fallback to .env
function getAuthHeaders(req = null) {
    let apiKey = '';
    
    // Priority 1: Per-request cookies via X-Rettiwt-Cookies header (for multi-user)
    if (req && req.headers['x-rettiwt-cookies']) {
        apiKey = req.headers['x-rettiwt-cookies'];
    }
    // Priority 2: Fall back to environment variable (single-user/admin mode)
    else {
        apiKey = process.env.RETTIWT_API_KEY || '';
    }
    
    if (!apiKey || /^\d+$/.test(apiKey)) {
        // Guest mode or numeric guest token
        return null;
    }
    
    // Parse auth_token;ct0 format
    const [authToken, ct0] = apiKey.split(';');
    
    if (!authToken || !ct0) {
        console.log('⚠️ Invalid cookie format. Expected: auth_token;ct0');
        return null;
    }
    
    return {
        'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
        'cookie': `auth_token=${authToken}; ct0=${ct0}`,
        'x-csrf-token': ct0,
        'x-twitter-auth-type': 'OAuth2Session',
        'x-twitter-active-user': 'yes',
        'x-twitter-client-language': 'en',
        'content-type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    };
}

// Twitter GraphQL endpoints
const GRAPHQL_URL = 'https://x.com/i/api/graphql';

// Feature flags required by Twitter (updated for 2024/2025)
const FEATURES = {
    "hidden_profile_subscriptions_enabled": true,
    "rweb_tipjar_consumption_enabled": true,
    "responsive_web_graphql_exclude_directive_enabled": true,
    "verified_phone_label_enabled": false,
    "subscriptions_verification_info_is_identity_verified_enabled": true,
    "subscriptions_verification_info_verified_since_enabled": true,
    "highlights_tweets_tab_ui_enabled": true,
    "responsive_web_twitter_article_notes_tab_enabled": true,
    "subscriptions_feature_can_gift_premium": true,
    "creator_subscriptions_tweet_preview_api_enabled": true,
    "responsive_web_graphql_skip_user_profile_image_extensions_enabled": false,
    "responsive_web_graphql_timeline_navigation_enabled": true,
    // Additional required features
    "tweet_awards_web_tipping_enabled": true,
    "longform_notetweets_consumption_enabled": true,
    "responsive_web_jetfuel_frame": false,
    "c9s_tweet_anatomy_moderator_badge_enabled": true,
    "responsive_web_grok_analysis_button_from_backend": false,
    "responsive_web_grok_share_attachment_enabled": false,
    "responsive_web_grok_analyze_post_followups_enabled": false,
    "responsive_web_enhance_cards_enabled": false,
    "responsive_web_edit_tweet_api_enabled": true,
    "standardized_nudges_misinfo": true,
    "rweb_video_timestamps_enabled": true,
    "profile_label_improvements_pcf_label_in_post_enabled": false,
    "articles_preview_enabled": true,
    "graphql_is_translatable_rweb_tweet_is_translatable_enabled": true,
    "responsive_web_grok_analyze_button_fetch_trends_enabled": false,
    "longform_notetweets_rich_text_read_enabled": true,
    "responsive_web_grok_image_annotation_enabled": false,
    "responsive_web_twitter_article_tweet_consumption_enabled": true,
    "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": true,
    "communities_web_enable_tweet_community_results_fetch": true,
    "longform_notetweets_inline_media_enabled": true,
    "premium_content_api_read_enabled": true,
    "freedom_of_speech_not_reach_fetch_enabled": true,
    "view_counts_everywhere_api_enabled": true,
    "creator_subscriptions_quote_tweet_preview_enabled": true
};

async function twitterGraphQL(queryId, operationName, variables) {
    const headers = getAuthHeaders(req);
    if (!headers) {
        throw new Error('Not authenticated');
    }
    
    const url = `${GRAPHQL_URL}/${queryId}/${operationName}?variables=${encodeURIComponent(JSON.stringify(variables))}&features=${encodeURIComponent(JSON.stringify(FEATURES))}`;
    
    const response = await fetch(url, {
        method: 'GET',
        headers
    });
    
    if (!response.ok) {
        const text = await response.text();
        throw new Error(`Twitter API error: ${response.status} - ${text.substring(0, 200)}`);
    }
    
    return response.json();
}

// Health check endpoint
app.get('/health', (req, res) => {
    const headers = getAuthHeaders(req);
    res.json({ 
        status: 'ok', 
        service: 'twitter-api-service',
        version: '2.0.0',
        authenticated: !!headers
    });
});

// Get user details by username
app.get('/api/user/:username', async (req, res) => {
    try {
        const headers = getAuthHeaders(req);
        if (!headers) {
            return res.status(401).json({ error: 'Not authenticated. Run: npm run auth' });
        }
        
        // Use Twitter's UserByScreenName endpoint
        const variables = {
            screen_name: req.params.username,
            withSafetyModeUserFields: true
        };
        
        const url = `https://x.com/i/api/graphql/xmU6X_CKVnQ5lSrCbAmJsg/UserByScreenName?variables=${encodeURIComponent(JSON.stringify(variables))}&features=${encodeURIComponent(JSON.stringify(FEATURES))}`;
        
        const response = await fetch(url, { headers });
        
        if (!response.ok) {
            const text = await response.text();
            console.error('Twitter API error:', response.status, text.substring(0, 500));
            return res.status(response.status).json({ error: 'Twitter API error' });
        }
        
        const data = await response.json();
        const user = data?.data?.user?.result;
        
        if (!user || user.__typename === 'UserUnavailable') {
            return res.status(404).json({ error: 'User not found' });
        }
        
        const legacy = user.legacy || {};
        
        // Transform to match Twitter API v2 format
        res.json({
            data: {
                id: user.rest_id,
                username: legacy.screen_name,
                name: legacy.name,
                description: legacy.description,
                profile_image_url: legacy.profile_image_url_https,
                public_metrics: {
                    followers_count: legacy.followers_count || 0,
                    following_count: legacy.friends_count || 0,
                    tweet_count: legacy.statuses_count || 0,
                    listed_count: legacy.listed_count || 0
                },
                verified: legacy.verified || user.is_blue_verified,
                created_at: legacy.created_at
            }
        });
    } catch (error) {
        console.error('Error fetching user:', error.message);
        res.status(500).json({ error: error.message });
    }
});

// Get user's tweets (timeline)
app.get('/api/user/:username/tweets', async (req, res) => {
    try {
        const headers = getAuthHeaders(req);
        if (!headers) {
            return res.status(401).json({ error: 'Not authenticated' });
        }
        
        const { count = 20, cursor } = req.query;
        
        // First get user ID
        const userVars = { screen_name: req.params.username, withSafetyModeUserFields: true };
        const userUrl = `https://x.com/i/api/graphql/xmU6X_CKVnQ5lSrCbAmJsg/UserByScreenName?variables=${encodeURIComponent(JSON.stringify(userVars))}&features=${encodeURIComponent(JSON.stringify(FEATURES))}`;
        
        const userResponse = await fetch(userUrl, { headers });
        const userData = await userResponse.json();
        const userId = userData?.data?.user?.result?.rest_id;
        
        if (!userId) {
            return res.status(404).json({ error: 'User not found' });
        }
        
        // Get user tweets
        const variables = {
            userId: userId,
            count: parseInt(count),
            includePromotedContent: false,
            withQuickPromoteEligibilityTweetFields: false,
            withVoice: false,
            withV2Timeline: true
        };
        
        if (cursor) {
            variables.cursor = cursor;
        }
        
        const tweetsUrl = `https://x.com/i/api/graphql/Y9WM4Id6UcGFE8Z-hbnixw/UserTweets?variables=${encodeURIComponent(JSON.stringify(variables))}&features=${encodeURIComponent(JSON.stringify(FEATURES))}`;
        
        const response = await fetch(tweetsUrl, { headers });
        const data = await response.json();
        
        // Parse tweets from timeline
        const instructions = data?.data?.user?.result?.timeline_v2?.timeline?.instructions || [];
        const entries = instructions.find(i => i.type === 'TimelineAddEntries')?.entries || [];
        
        const tweets = entries
            .filter(e => e.content?.entryType === 'TimelineTimelineItem')
            .map(e => {
                const tweet = e.content?.itemContent?.tweet_results?.result;
                if (!tweet || tweet.__typename !== 'Tweet') return null;
                
                const legacy = tweet.legacy || {};
                return {
                    id: tweet.rest_id,
                    text: legacy.full_text,
                    created_at: legacy.created_at,
                    author_id: userId,
                    public_metrics: {
                        like_count: legacy.favorite_count || 0,
                        retweet_count: legacy.retweet_count || 0,
                        reply_count: legacy.reply_count || 0,
                        quote_count: legacy.quote_count || 0,
                        impression_count: 0,  // Not available in this endpoint
                        bookmark_count: legacy.bookmark_count || 0
                    }
                };
            })
            .filter(Boolean);
        
        // Find cursor for next page
        const cursorEntry = entries.find(e => e.content?.cursorType === 'Bottom');
        const nextCursor = cursorEntry?.content?.value;
        
        res.json({
            data: tweets,
            meta: {
                result_count: tweets.length,
                next_token: nextCursor || null
            }
        });
    } catch (error) {
        console.error('Error fetching tweets:', error.message);
        res.status(500).json({ error: error.message });
    }
});

// Get ALL tweets from last N days (with automatic pagination)
app.get('/api/user/:username/tweets/all', async (req, res) => {
    try {
        const headers = getAuthHeaders(req);
        if (!headers) {
            return res.status(401).json({ error: 'Not authenticated' });
        }
        
        const { days = 30, maxTweets = 500 } = req.query;
        const daysInt = parseInt(days);
        const maxTweetsInt = parseInt(maxTweets);
        
        // Calculate cutoff date
        const cutoffDate = new Date();
        cutoffDate.setDate(cutoffDate.getDate() - daysInt);
        
        console.log(`\n📊 Fetching all tweets for @${req.params.username} from last ${daysInt} days`);
        console.log(`📅 Cutoff date: ${cutoffDate.toISOString()}`);
        
        // First get user ID
        const userVars = { screen_name: req.params.username, withSafetyModeUserFields: true };
        const userUrl = `https://x.com/i/api/graphql/xmU6X_CKVnQ5lSrCbAmJsg/UserByScreenName?variables=${encodeURIComponent(JSON.stringify(userVars))}&features=${encodeURIComponent(JSON.stringify(FEATURES))}`;
        
        const userResponse = await fetch(userUrl, { headers });
        const userData = await userResponse.json();
        const userId = userData?.data?.user?.result?.rest_id;
        
        if (!userId) {
            return res.status(404).json({ error: 'User not found' });
        }
        
        console.log(`👤 User ID: ${userId}`);
        
        // Paginate through all tweets
        let allTweets = [];
        let cursor = null;
        let page = 0;
        let reachedCutoff = false;
        
        while (!reachedCutoff && allTweets.length < maxTweetsInt && page < 20) {
            page++;
            console.log(`📄 Page ${page}: fetching tweets...`);
            
            const variables = {
                userId: userId,
                count: 40, // Max per request
                includePromotedContent: false,
                withQuickPromoteEligibilityTweetFields: true,
                withVoice: true,
                withV2Timeline: true
            };
            
            if (cursor) {
                variables.cursor = cursor;
            }
            
            const tweetsUrl = `https://x.com/i/api/graphql/Y9WM4Id6UcGFE8Z-hbnixw/UserTweets?variables=${encodeURIComponent(JSON.stringify(variables))}&features=${encodeURIComponent(JSON.stringify(FEATURES))}`;
            
            const response = await fetch(tweetsUrl, { headers });
            const data = await response.json();
            
            if (data.errors) {
                console.log('❌ API Error:', data.errors[0]?.message);
                break;
            }
            
            // Parse tweets from timeline
            const instructions = data?.data?.user?.result?.timeline_v2?.timeline?.instructions || [];
            const entries = instructions.find(i => i.type === 'TimelineAddEntries')?.entries || [];
            
            // Also check for pinned tweet
            const pinnedEntry = instructions.find(i => i.type === 'TimelinePinEntry');
            if (pinnedEntry?.entry?.content?.itemContent?.tweet_results?.result && page === 1) {
                const pinnedTweet = pinnedEntry.entry.content.itemContent.tweet_results.result;
                if (pinnedTweet.__typename === 'Tweet') {
                    const legacy = pinnedTweet.legacy || {};
                    const tweetDate = new Date(legacy.created_at);
                    if (tweetDate >= cutoffDate) {
                        allTweets.push({
                            id: pinnedTweet.rest_id,
                            text: legacy.full_text,
                            created_at: legacy.created_at,
                            author_id: userId,
                            is_pinned: true,
                            public_metrics: {
                                like_count: legacy.favorite_count || 0,
                                retweet_count: legacy.retweet_count || 0,
                                reply_count: legacy.reply_count || 0,
                                quote_count: legacy.quote_count || 0,
                                impression_count: parseInt(pinnedTweet.views?.count) || 0,
                                bookmark_count: legacy.bookmark_count || 0
                            }
                        });
                    }
                }
            }
            
            // Parse timeline tweets
            let tweetsThisPage = 0;
            for (const entry of entries) {
                if (entry.content?.entryType === 'TimelineTimelineItem') {
                    const tweet = entry.content?.itemContent?.tweet_results?.result;
                    if (!tweet || tweet.__typename !== 'Tweet') continue;
                    
                    const legacy = tweet.legacy || {};
                    const tweetDate = new Date(legacy.created_at);
                    
                    // Check if we've gone past the cutoff date
                    if (tweetDate < cutoffDate) {
                        console.log(`⏹️ Reached cutoff date at tweet from ${legacy.created_at}`);
                        reachedCutoff = true;
                        break;
                    }
                    
                    // Skip retweets if they're from other users
                    if (legacy.retweeted_status_result) {
                        continue; // Skip retweets
                    }
                    
                    allTweets.push({
                        id: tweet.rest_id,
                        text: legacy.full_text,
                        created_at: legacy.created_at,
                        author_id: userId,
                        public_metrics: {
                            like_count: legacy.favorite_count || 0,
                            retweet_count: legacy.retweet_count || 0,
                            reply_count: legacy.reply_count || 0,
                            quote_count: legacy.quote_count || 0,
                            impression_count: parseInt(tweet.views?.count) || 0,
                            bookmark_count: legacy.bookmark_count || 0
                        }
                    });
                    tweetsThisPage++;
                }
            }
            
            console.log(`   Found ${tweetsThisPage} tweets this page, total: ${allTweets.length}`);
            
            // Find cursor for next page
            const cursorEntry = entries.find(e => e.content?.cursorType === 'Bottom');
            cursor = cursorEntry?.content?.value;
            
            if (!cursor || tweetsThisPage === 0) {
                console.log('📭 No more tweets to fetch');
                break;
            }
            
            // Small delay to avoid rate limiting
            await new Promise(resolve => setTimeout(resolve, 500));
        }
        
        console.log(`\n✅ Total tweets fetched: ${allTweets.length}`);
        
        // Remove duplicates based on tweet ID
        const uniqueTweets = Array.from(
            new Map(allTweets.map(t => [t.id, t])).values()
        );
        
        res.json({
            data: uniqueTweets,
            meta: {
                result_count: uniqueTweets.length,
                days_fetched: daysInt,
                cutoff_date: cutoffDate.toISOString(),
                pages_fetched: page,
                user_id: userId
            }
        });
        
    } catch (error) {
        console.error('Error fetching all tweets:', error.message);
        res.status(500).json({ error: error.message });
    }
});

// Get user's followers
app.get('/api/user/:username/followers', async (req, res) => {
    try {
        const headers = getAuthHeaders(req);
        if (!headers) {
            return res.status(401).json({ error: 'Not authenticated' });
        }
        
        const { count = 20, cursor } = req.query;
        
        // First get user ID
        const userVars = { screen_name: req.params.username, withSafetyModeUserFields: true };
        const userUrl = `https://x.com/i/api/graphql/xmU6X_CKVnQ5lSrCbAmJsg/UserByScreenName?variables=${encodeURIComponent(JSON.stringify(userVars))}&features=${encodeURIComponent(JSON.stringify(FEATURES))}`;
        
        const userResponse = await fetch(userUrl, { headers });
        const userData = await userResponse.json();
        const userId = userData?.data?.user?.result?.rest_id;
        
        if (!userId) {
            return res.status(404).json({ error: 'User not found' });
        }
        
        // Get followers
        const variables = {
            userId: userId,
            count: parseInt(count),
            includePromotedContent: false
        };
        if (cursor) variables.cursor = cursor;
        
        const followersUrl = `https://x.com/i/api/graphql/pd8Tt3WAAQQ8cjMm1o-S1w/Followers?variables=${encodeURIComponent(JSON.stringify(variables))}&features=${encodeURIComponent(JSON.stringify(FEATURES))}`;
        
        const response = await fetch(followersUrl, { headers });
        const data = await response.json();
        
        const instructions = data?.data?.user?.result?.timeline?.timeline?.instructions || [];
        const entries = instructions.find(i => i.type === 'TimelineAddEntries')?.entries || [];
        
        const followers = entries
            .filter(e => e.content?.entryType === 'TimelineTimelineItem')
            .map(e => {
                const user = e.content?.itemContent?.user_results?.result;
                if (!user) return null;
                const legacy = user.legacy || {};
                return {
                    id: user.rest_id,
                    username: legacy.screen_name,
                    name: legacy.name,
                    description: legacy.description,
                    profile_image_url: legacy.profile_image_url_https,
                    created_at: legacy.created_at,
                    public_metrics: {
                        followers_count: legacy.followers_count || 0,
                        following_count: legacy.friends_count || 0,
                        tweet_count: legacy.statuses_count || 0,
                        listed_count: legacy.listed_count || 0
                    },
                    verified: legacy.verified || user.is_blue_verified || false
                };
            })
            .filter(Boolean);
        
        const cursorEntry = entries.find(e => e.content?.cursorType === 'Bottom');
        
        res.json({
            data: followers,
            meta: {
                result_count: followers.length,
                next_token: cursorEntry?.content?.value || null
            }
        });
    } catch (error) {
        console.error('Error fetching followers:', error.message);
        res.status(500).json({ error: error.message });
    }
});

// Get user's following
app.get('/api/user/:username/following', async (req, res) => {
    try {
        const headers = getAuthHeaders(req);
        if (!headers) {
            return res.status(401).json({ error: 'Not authenticated' });
        }
        
        const { count = 20, cursor } = req.query;
        
        // First get user ID
        const userVars = { screen_name: req.params.username, withSafetyModeUserFields: true };
        const userUrl = `https://x.com/i/api/graphql/xmU6X_CKVnQ5lSrCbAmJsg/UserByScreenName?variables=${encodeURIComponent(JSON.stringify(userVars))}&features=${encodeURIComponent(JSON.stringify(FEATURES))}`;
        
        const userResponse = await fetch(userUrl, { headers });
        const userData = await userResponse.json();
        const userId = userData?.data?.user?.result?.rest_id;
        
        if (!userId) {
            return res.status(404).json({ error: 'User not found' });
        }
        
        // Get following
        const variables = {
            userId: userId,
            count: parseInt(count),
            includePromotedContent: false
        };
        if (cursor) variables.cursor = cursor;
        
        const followingUrl = `https://x.com/i/api/graphql/JPZiqKjET7_M1r5Tlr8pyA/Following?variables=${encodeURIComponent(JSON.stringify(variables))}&features=${encodeURIComponent(JSON.stringify(FEATURES))}`;
        
        const response = await fetch(followingUrl, { headers });
        const data = await response.json();
        
        const instructions = data?.data?.user?.result?.timeline?.timeline?.instructions || [];
        const entries = instructions.find(i => i.type === 'TimelineAddEntries')?.entries || [];
        
        const following = entries
            .filter(e => e.content?.entryType === 'TimelineTimelineItem')
            .map(e => {
                const user = e.content?.itemContent?.user_results?.result;
                if (!user) return null;
                const legacy = user.legacy || {};
                return {
                    id: user.rest_id,
                    username: legacy.screen_name,
                    name: legacy.name,
                    description: legacy.description,
                    profile_image_url: legacy.profile_image_url_https,
                    created_at: legacy.created_at,
                    public_metrics: {
                        followers_count: legacy.followers_count || 0,
                        following_count: legacy.friends_count || 0,
                        tweet_count: legacy.statuses_count || 0,
                        listed_count: legacy.listed_count || 0
                    },
                    verified: legacy.verified || user.is_blue_verified || false
                };
            })
            .filter(Boolean);
        
        const cursorEntry = entries.find(e => e.content?.cursorType === 'Bottom');
        
        res.json({
            data: following,
            meta: {
                result_count: following.length,
                next_token: cursorEntry?.content?.value || null
            }
        });
    } catch (error) {
        console.error('Error fetching following:', error.message);
        res.status(500).json({ error: error.message });
    }
});

// Search tweets
app.get('/api/tweets/search', async (req, res) => {
    try {
        const headers = getAuthHeaders(req);
        if (!headers) {
            return res.status(401).json({ error: 'Not authenticated' });
        }
        
        const { query, count = 20, cursor } = req.query;
        
        if (!query) {
            return res.status(400).json({ error: 'Query parameter is required' });
        }
        
        const variables = {
            rawQuery: query,
            count: parseInt(count),
            querySource: 'typed_query',
            product: 'Latest'
        };
        if (cursor) variables.cursor = cursor;
        
        const searchUrl = `https://x.com/i/api/graphql/UN1i3zUiCWa-6r-Uaho4fw/SearchTimeline?variables=${encodeURIComponent(JSON.stringify(variables))}&features=${encodeURIComponent(JSON.stringify(FEATURES))}`;
        
        const response = await fetch(searchUrl, { headers });
        const data = await response.json();
        
        const instructions = data?.data?.search_by_raw_query?.search_timeline?.timeline?.instructions || [];
        const entries = instructions.find(i => i.type === 'TimelineAddEntries')?.entries || [];
        
        const tweets = entries
            .filter(e => e.content?.entryType === 'TimelineTimelineItem')
            .map(e => {
                const tweet = e.content?.itemContent?.tweet_results?.result;
                if (!tweet || tweet.__typename !== 'Tweet') return null;
                const legacy = tweet.legacy || {};
                return {
                    id: tweet.rest_id,
                    text: legacy.full_text,
                    created_at: legacy.created_at,
                    author_id: tweet.core?.user_results?.result?.rest_id,
                    public_metrics: {
                        like_count: legacy.favorite_count || 0,
                        retweet_count: legacy.retweet_count || 0,
                        reply_count: legacy.reply_count || 0,
                        quote_count: legacy.quote_count || 0,
                        impression_count: 0,
                        bookmark_count: legacy.bookmark_count || 0
                    }
                };
            })
            .filter(Boolean);
        
        const cursorEntry = entries.find(e => e.content?.cursorType === 'Bottom');
        
        res.json({
            data: tweets,
            meta: {
                result_count: tweets.length,
                next_token: cursorEntry?.content?.value || null
            }
        });
    } catch (error) {
        console.error('Error searching tweets:', error.message);
        res.status(500).json({ error: error.message });
    }
});

// Get tweet details by ID
app.get('/api/tweet/:tweetId', async (req, res) => {
    try {
        const headers = getAuthHeaders(req);
        if (!headers) {
            return res.status(401).json({ error: 'Not authenticated' });
        }
        
        const variables = {
            tweetId: req.params.tweetId,
            withCommunity: false,
            includePromotedContent: false,
            withVoice: false
        };
        
        const tweetUrl = `https://x.com/i/api/graphql/xOhkmRac04YFZmOzU9PJHg/TweetDetail?variables=${encodeURIComponent(JSON.stringify(variables))}&features=${encodeURIComponent(JSON.stringify(FEATURES))}`;
        
        const response = await fetch(tweetUrl, { headers });
        const data = await response.json();
        
        const entries = data?.data?.tweetResult?.result?.timeline_response?.timeline?.instructions?.[0]?.entries || [];
        const tweetEntry = entries.find(e => e.content?.itemContent?.tweet_results);
        const tweet = tweetEntry?.content?.itemContent?.tweet_results?.result;
        
        if (!tweet) {
            return res.status(404).json({ error: 'Tweet not found' });
        }
        
        const legacy = tweet.legacy || {};
        
        res.json({
            data: {
                id: tweet.rest_id,
                text: legacy.full_text,
                created_at: legacy.created_at,
                author_id: tweet.core?.user_results?.result?.rest_id,
                public_metrics: {
                    like_count: legacy.favorite_count || 0,
                    retweet_count: legacy.retweet_count || 0,
                    reply_count: legacy.reply_count || 0,
                    quote_count: legacy.quote_count || 0,
                    impression_count: 0,
                    bookmark_count: legacy.bookmark_count || 0
                }
            }
        });
    } catch (error) {
        console.error('Error fetching tweet:', error.message);
        res.status(500).json({ error: error.message });
    }
});

// DEBUG: Get full tweet data for a user (logs everything)
app.get('/api/debug/tweets/:username', async (req, res) => {
    try {
        const headers = getAuthHeaders(req);
        if (!headers) {
            return res.status(401).json({ error: 'Not authenticated' });
        }
        
        // First get user ID
        const userVars = { screen_name: req.params.username, withSafetyModeUserFields: true };
        const userUrl = `https://x.com/i/api/graphql/xmU6X_CKVnQ5lSrCbAmJsg/UserByScreenName?variables=${encodeURIComponent(JSON.stringify(userVars))}&features=${encodeURIComponent(JSON.stringify(FEATURES))}`;
        
        const userResponse = await fetch(userUrl, { headers });
        const userData = await userResponse.json();
        const userId = userData?.data?.user?.result?.rest_id;
        
        if (!userId) {
            return res.status(404).json({ error: 'User not found' });
        }
        
        console.log('\n' + '='.repeat(80));
        console.log(`📊 DEBUG: Fetching tweets for @${req.params.username} (ID: ${userId})`);
        console.log('='.repeat(80));
        
        // Try GraphQL with correct UserTweets query
        const variables = {
            userId: userId,
            count: 20,
            includePromotedContent: false,
            withQuickPromoteEligibilityTweetFields: true,
            withVoice: true,
            withV2Timeline: true
        };
        
        // Try multiple query IDs as Twitter changes them frequently
        const queryIds = [
            'Y9WM4Id6UcGFE8Z-hbnixw', // UserTweets
            'CdG2Vuc1v6F5JyEngGpxVw', // UserTweets (alt)
            'V7H0Ap3_Hh2FyS75OCDO3Q', // UserTweetsAndReplies
        ];
        
        let tweetsUrl = `https://x.com/i/api/graphql/${queryIds[0]}/UserTweets?variables=${encodeURIComponent(JSON.stringify(variables))}&features=${encodeURIComponent(JSON.stringify(FEATURES))}`;
        
        console.log('\n📡 Request URL:', tweetsUrl.substring(0, 120) + '...');
        
        const response = await fetch(tweetsUrl, { headers });
        const responseText = await response.text();
        
        console.log('\n📥 Response Status:', response.status);
        console.log('📥 Response Length:', responseText.length, 'bytes');
        
        let data;
        try {
            data = JSON.parse(responseText);
        } catch (e) {
            console.log('❌ Failed to parse JSON:', responseText.substring(0, 500));
            return res.status(500).json({ error: 'Invalid response from Twitter' });
        }
        
        // Log full structure
        console.log('\n📋 Full Response Structure:');
        console.log(JSON.stringify(data, null, 2));
        
        // Also log errors if present
        if (data.errors) {
            console.log('\n❌ Errors in response:', JSON.stringify(data.errors, null, 2));
        }
        
        // Parse GraphQL response
        const instructions = data?.data?.user?.result?.timeline_v2?.timeline?.instructions || [];
        console.log('\n📌 Instructions found:', instructions.length);
        
        instructions.forEach((inst, i) => {
            console.log(`  [${i}] type: ${inst.type}`);
        });
        
        // Also check for pinned tweet in TimelinePinEntry
        const pinnedEntry = instructions.find(i => i.type === 'TimelinePinEntry');
        if (pinnedEntry) {
            console.log('\n📍 Found pinned tweet entry!');
            console.log(JSON.stringify(pinnedEntry, null, 2).substring(0, 2000));
        }
        
        const entries = instructions.find(i => i.type === 'TimelineAddEntries')?.entries || [];
        console.log('\n📝 Entries found:', entries.length);
        
        // Log all entry types
        entries.forEach((entry, i) => {
            console.log(`  [${i}] entryId: ${entry.entryId}, type: ${entry.content?.entryType}`);
        });
        
        // Log each tweet's full data
        const tweets = [];
        
        // Helper function to extract tweet data
        const extractTweet = (tweet, idx) => {
            if (!tweet || tweet.__typename !== 'Tweet') return null;
            
            console.log(`\n${'─'.repeat(60)}`);
            console.log(`🐦 Tweet #${idx + 1}`);
            console.log(`${'─'.repeat(60)}`);
            
            const legacy = tweet.legacy || {};
            
            console.log('📌 Tweet ID:', tweet.rest_id);
            console.log('📝 Text:', legacy.full_text?.substring(0, 100) + '...');
            console.log('📅 Created:', legacy.created_at);
            
            console.log('\n📊 METRICS (legacy object):');
            console.log('  - favorite_count (likes):', legacy.favorite_count);
            console.log('  - retweet_count:', legacy.retweet_count);
            console.log('  - reply_count:', legacy.reply_count);
            console.log('  - quote_count:', legacy.quote_count);
            console.log('  - bookmark_count:', legacy.bookmark_count);
            
            // Check for views/impressions
            console.log('\n👁️ VIEWS DATA:');
            console.log('  - views (tweet.views):', JSON.stringify(tweet.views));
            console.log('  - view_count:', tweet.views?.count);
            
            // Check for other metrics
            console.log('\n🔍 OTHER FIELDS:');
            console.log('  - is_quote_status:', legacy.is_quote_status);
            console.log('  - possibly_sensitive:', legacy.possibly_sensitive);
            console.log('  - lang:', legacy.lang);
            console.log('  - source:', legacy.source?.substring(0, 50));
            
            // Full legacy object keys
            console.log('\n📦 All legacy keys:', Object.keys(legacy).join(', '));
            
            // Full tweet object keys
            console.log('📦 All tweet keys:', Object.keys(tweet).join(', '));
            
            return {
                id: tweet.rest_id,
                text: legacy.full_text,
                created_at: legacy.created_at,
                metrics: {
                    likes: legacy.favorite_count,
                    retweets: legacy.retweet_count,
                    replies: legacy.reply_count,
                    quotes: legacy.quote_count,
                    bookmarks: legacy.bookmark_count,
                    views: tweet.views?.count || null
                },
                raw_views: tweet.views,
                all_legacy_keys: Object.keys(legacy),
                all_tweet_keys: Object.keys(tweet)
            };
        };
        
        // Check pinned tweet first
        if (pinnedEntry?.entry?.content?.itemContent?.tweet_results?.result) {
            const pinnedTweet = extractTweet(pinnedEntry.entry.content.itemContent.tweet_results.result, tweets.length);
            if (pinnedTweet) {
                pinnedTweet.is_pinned = true;
                tweets.push(pinnedTweet);
            }
        }
        
        // Process timeline entries
        entries.forEach((entry, i) => {
            if (entry.content?.entryType === 'TimelineTimelineItem') {
                const tweet = entry.content?.itemContent?.tweet_results?.result;
                const tweetData = extractTweet(tweet, tweets.length);
                if (tweetData) tweets.push(tweetData);
            }
        });
        
        console.log('\n' + '='.repeat(80));
        console.log(`✅ Found ${tweets.length} tweets`);
        console.log('='.repeat(80) + '\n');
        
        res.json({
            user: {
                id: userId,
                username: req.params.username
            },
            tweets_count: tweets.length,
            tweets: tweets
        });
        
    } catch (error) {
        console.error('❌ Error:', error.message);
        res.status(500).json({ error: error.message });
    }
});

// ============================================================================
// AUTHENTICATION ENDPOINTS
// ============================================================================

// Auth status tracking
let authInProgress = false;
let authBrowserContext = null;

// Dynamic import for playwright (only when needed)
let chromium = null;
async function getPlaywright() {
    if (!chromium) {
        const playwright = await import('playwright');
        chromium = playwright.chromium;
    }
    return chromium;
}

// Read saved session info
function getSavedSession() {
    try {
        const sessionPath = path.join(__dirname, '.session.json');
        if (fs.existsSync(sessionPath)) {
            return JSON.parse(fs.readFileSync(sessionPath, 'utf8'));
        }
    } catch (e) {}
    return null;
}

// Save session info
function saveSession(userInfo) {
    try {
        const sessionPath = path.join(__dirname, '.session.json');
        fs.writeFileSync(sessionPath, JSON.stringify(userInfo, null, 2));
    } catch (e) {
        console.error('Failed to save session:', e.message);
    }
}

// Clear session
function clearSession() {
    try {
        const sessionPath = path.join(__dirname, '.session.json');
        if (fs.existsSync(sessionPath)) {
            fs.unlinkSync(sessionPath);
        }
    } catch (e) {}
}

// Check current auth status
app.get('/api/auth/status', async (req, res) => {
    const apiKey = process.env.RETTIWT_API_KEY || '';
    const hasValidAuth = apiKey && !(/^\d+$/.test(apiKey)) && apiKey.includes(';');
    
    if (!hasValidAuth) {
        return res.json({
            authenticated: false,
            auth_in_progress: authInProgress,
            message: 'No valid session found'
        });
    }
    
    // Check saved session first
    const savedSession = getSavedSession();
    if (savedSession && savedSession.username) {
        // Verify session is still valid by making a simple API call
        try {
            const headers = getAuthHeaders(req);
            if (headers) {
                // Try to fetch user info for the saved username
                const userVars = { screen_name: savedSession.username, withSafetyModeUserFields: true };
                const userUrl = `https://x.com/i/api/graphql/xmU6X_CKVnQ5lSrCbAmJsg/UserByScreenName?variables=${encodeURIComponent(JSON.stringify(userVars))}&features=${encodeURIComponent(JSON.stringify(FEATURES))}`;
                
                const userResponse = await fetch(userUrl, { headers });
                const userData = await userResponse.json();
                
                const user = userData?.data?.user?.result;
                
                if (user) {
                    const legacy = user.legacy || {};
                    return res.json({
                        authenticated: true,
                        user: {
                            id: user.rest_id,
                            username: legacy.screen_name,
                            name: legacy.name,
                            profile_image_url: legacy.profile_image_url_https?.replace('_normal', '_400x400'),
                            description: legacy.description,
                            verified: user.is_blue_verified || false,
                            followers_count: legacy.followers_count,
                            following_count: legacy.friends_count,
                            tweet_count: legacy.statuses_count,
                            created_at: legacy.created_at
                        },
                        cookies: apiKey  // Include cookies for Streamlit to use
                    });
                }
            }
        } catch (error) {
            console.error('Session validation failed:', error.message);
        }
    }
    
    // If no saved session, we have cookies but don't know the user
    // Return authenticated with limited info
    return res.json({ 
        authenticated: true,
        user: savedSession || null,
        message: savedSession ? 'Session valid' : 'Authenticated but user info not available. Please re-login.'
    });
});

// Start authentication (opens Playwright browser)
app.post('/api/auth/start', async (req, res) => {
    if (authInProgress) {
        return res.status(409).json({ 
            error: 'Authentication already in progress',
            message: 'Please complete the login in the browser window'
        });
    }
    
    authInProgress = true;
    
    try {
        console.log('\n🔐 Starting Playwright authentication...');
        
        const userDataDir = path.join(__dirname, '.playwright-profile');
        const playwright = await getPlaywright();
        
        authBrowserContext = await playwright.launchPersistentContext(userDataDir, {
            headless: false,
            viewport: { width: 1280, height: 800 },
            userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            args: ['--disable-blink-features=AutomationControlled']
        });
        
        const page = authBrowserContext.pages()[0] || await authBrowserContext.newPage();
        
        // Navigate to Twitter login
        console.log('🌐 Opening Twitter login page...');
        await page.goto('https://x.com/i/flow/login', { waitUntil: 'domcontentloaded', timeout: 60000 });
        
        res.json({
            success: true,
            message: 'Browser opened. Please log in to Twitter.',
            instructions: [
                '1. Log in with your Twitter credentials in the browser window',
                '2. Complete 2FA if required',
                '3. Once you see your feed, call POST /api/auth/complete'
            ]
        });
        
    } catch (error) {
        authInProgress = false;
        console.error('Auth start failed:', error.message);
        res.status(500).json({ error: error.message });
    }
});

// Complete authentication (capture cookies and get user info)
app.post('/api/auth/complete', async (req, res) => {
    if (!authInProgress || !authBrowserContext) {
        return res.status(400).json({ 
            error: 'No authentication in progress',
            message: 'Call POST /api/auth/start first'
        });
    }
    
    try {
        console.log('🔄 Completing authentication...');
        
        const page = authBrowserContext.pages()[0];
        
        // Navigate to home to ensure cookies are set
        await page.goto('https://x.com/home', { waitUntil: 'domcontentloaded', timeout: 30000 });
        await page.waitForTimeout(3000);
        
        // Get all cookies
        const cookies = await authBrowserContext.cookies();
        
        const authToken = cookies.find(c => c.name === 'auth_token');
        const ct0 = cookies.find(c => c.name === 'ct0');
        
        if (!authToken || !ct0) {
            return res.status(401).json({
                error: 'Login not completed',
                message: 'Please log in to Twitter in the browser window first',
                found_cookies: cookies.map(c => c.name)
            });
        }
        
        // Update .env with new API key
        const apiKey = `${authToken.value};${ct0.value}`;
        
        const envPath = path.join(__dirname, '..', '.env');
        
        let envContent = '';
        if (fs.existsSync(envPath)) {
            envContent = fs.readFileSync(envPath, 'utf8');
        }
        
        if (envContent.includes('RETTIWT_API_KEY=')) {
            envContent = envContent.replace(/RETTIWT_API_KEY=.*/, `RETTIWT_API_KEY=${apiKey}`);
        } else {
            envContent += `\nRETTIWT_API_KEY=${apiKey}\n`;
        }
        
        fs.writeFileSync(envPath, envContent);
        
        // Update process.env immediately
        process.env.RETTIWT_API_KEY = apiKey;
        
        console.log('✅ Cookies saved to .env');
        
        // Get current user info using new cookies
        // Build headers directly with the new cookies
        const headers = {
            'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
            'cookie': `auth_token=${authToken.value}; ct0=${ct0.value}`,
            'x-csrf-token': ct0.value,
            'x-twitter-auth-type': 'OAuth2Session',
            'x-twitter-active-user': 'yes',
            'content-type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        };
        let userInfo = null;
        
        // Use Viewer GraphQL endpoint to get current user info
        try {
            const viewerUrl = 'https://x.com/i/api/graphql/2A6VqXzLLCfPplvYlmYGpQ/Viewer?variables=%7B%22withCommunitiesMemberships%22%3Atrue%7D&features=%7B%22creator_subscriptions_tweet_preview_api_enabled%22%3Atrue%7D';
            const viewerResponse = await fetch(viewerUrl, { headers });
            
            if (viewerResponse.status === 200) {
                const viewerData = await viewerResponse.json();
                const viewer = viewerData?.data?.viewer?.user_results?.result;
                
                if (viewer) {
                    const legacy = viewer.legacy || {};
                    userInfo = {
                        id: viewer.rest_id,
                        username: legacy.screen_name,
                        name: legacy.name,
                        profile_image_url: legacy.profile_image_url_https?.replace('_normal', '_400x400'),
                        description: legacy.description,
                        verified: viewer.is_blue_verified || false,
                        followers_count: legacy.followers_count,
                        following_count: legacy.friends_count,
                        tweet_count: legacy.statuses_count,
                        created_at: legacy.created_at
                    };
                    console.log(`✅ Logged in as @${userInfo.username}`);
                    
                    // Save session to file for persistence
                    saveSession(userInfo);
                }
            } else {
                console.log(`⚠️ Viewer endpoint returned status ${viewerResponse.status}`);
                // Try to get username from profile link in the page
                const page = authBrowserContext.pages()[0];
                if (page) {
                    try {
                        await page.goto('https://x.com/home', { waitUntil: 'domcontentloaded', timeout: 30000 });
                        await page.waitForTimeout(3000);
                        
                        // Look for the profile link which contains the username
                        const profileLink = await page.evaluate(() => {
                            // Find profile link in sidebar
                            const links = document.querySelectorAll('a[href^="/"]');
                            for (const link of links) {
                                const href = link.getAttribute('href');
                                // Profile link is usually just /username
                                if (href && href.match(/^\/[a-zA-Z0-9_]+$/) && !href.includes('/home') && !href.includes('/explore') && !href.includes('/notifications') && !href.includes('/messages') && !href.includes('/i/')) {
                                    // Check if it looks like a profile link (has profile image nearby)
                                    const img = link.querySelector('img');
                                    if (img && img.src && img.src.includes('profile_images')) {
                                        return href.substring(1); // Remove leading /
                                    }
                                }
                            }
                            // Alternative: look for aria-label="Profile"
                            const profileBtn = document.querySelector('a[aria-label="Profile"]');
                            if (profileBtn) {
                                const href = profileBtn.getAttribute('href');
                                if (href) return href.substring(1);
                            }
                            return null;
                        });
                        
                        if (profileLink) {
                            console.log(`📍 Found username from page: @${profileLink}`);
                            
                            // Fetch user info using the username
                            const userVars = { screen_name: profileLink, withSafetyModeUserFields: true };
                            const userUrl = `https://x.com/i/api/graphql/xmU6X_CKVnQ5lSrCbAmJsg/UserByScreenName?variables=${encodeURIComponent(JSON.stringify(userVars))}&features=${encodeURIComponent(JSON.stringify(FEATURES))}`;
                            
                            const userResponse = await fetch(userUrl, { headers });
                            if (userResponse.status === 200) {
                                const userData = await userResponse.json();
                                const user = userData?.data?.user?.result;
                                
                                if (user) {
                                    const legacy = user.legacy || {};
                                    userInfo = {
                                        id: user.rest_id,
                                        username: legacy.screen_name,
                                        name: legacy.name,
                                        profile_image_url: legacy.profile_image_url_https?.replace('_normal', '_400x400'),
                                        description: legacy.description,
                                        verified: user.is_blue_verified || false,
                                        followers_count: legacy.followers_count,
                                        following_count: legacy.friends_count,
                                        tweet_count: legacy.statuses_count,
                                        created_at: legacy.created_at
                                    };
                                    console.log(`✅ Logged in as @${userInfo.username}`);
                                    saveSession(userInfo);
                                }
                            }
                        } else {
                            console.log('⚠️ Could not find username in page');
                        }
                    } catch (pageError) {
                        console.error('Error extracting username from page:', pageError.message);
                    }
                }
            }
        } catch (viewerError) {
            console.error('Error fetching viewer info:', viewerError.message);
        }
        
        // Close browser
        await authBrowserContext.close();
        authBrowserContext = null;
        authInProgress = false;
        
        res.json({
            success: true,
            message: 'Authentication completed successfully',
            user: userInfo,
            // Full cookies for storing in DB (per-user)
            cookies: apiKey,
            session: {
                auth_token: authToken.value.substring(0, 10) + '...',
                ct0: ct0.value.substring(0, 10) + '...',
                expires: authToken.expires
            }
        });
        
    } catch (error) {
        console.error('Auth complete failed:', error.message);
        
        // Clean up
        if (authBrowserContext) {
            await authBrowserContext.close().catch(() => {});
            authBrowserContext = null;
        }
        authInProgress = false;
        
        res.status(500).json({ error: error.message });
    }
});

// Cancel authentication
app.post('/api/auth/cancel', async (req, res) => {
    if (authBrowserContext) {
        await authBrowserContext.close().catch(() => {});
        authBrowserContext = null;
    }
    authInProgress = false;
    
    res.json({ success: true, message: 'Authentication cancelled' });
});

// Logout (clear session)
app.post('/api/auth/logout', async (req, res) => {
    try {
        // Clear cookies from .env
        const envPath = path.join(__dirname, '..', '.env');
        
        if (fs.existsSync(envPath)) {
            let envContent = fs.readFileSync(envPath, 'utf8');
            envContent = envContent.replace(/RETTIWT_API_KEY=.*\n?/, '');
            fs.writeFileSync(envPath, envContent);
        }
        
        // Clear from process
        delete process.env.RETTIWT_API_KEY;
        
        // Clear session file
        clearSession();
        
        // Clear Playwright profile
        const profilePath = path.join(__dirname, '.playwright-profile');
        
        try {
            fs.rmSync(profilePath, { recursive: true, force: true });
        } catch (e) {
            // Profile might not exist
        }
        
        res.json({ success: true, message: 'Logged out successfully' });
        
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Start server
app.listen(PORT, () => {
    console.log(`🚀 Rettiwt Service running on http://localhost:${PORT}`);
    console.log(`📊 Authentication: ${process.env.RETTIWT_API_KEY ? 'API Key configured' : 'Guest mode'}`);
});
