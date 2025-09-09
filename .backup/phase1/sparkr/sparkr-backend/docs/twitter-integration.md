# Twitter API Integration Guide

## Creating a Twitter Developer App

1. **Create a Twitter Developer Account**
   - Go to [Twitter Developer Portal](https://developer.twitter.com/)
   - Sign in with your Twitter account
   - Apply for a developer account if you don't have one already
   - Complete the application process by providing required information about your use case

2. **Create a New Project**
   - Navigate to the Developer Portal Dashboard
   - Click on "+ New Project"
   - Enter a name for your project
   - Select the use case that best describes your application

3. **Create an App within the Project**
   - Within your project, click "+ Add App"
   - Enter a name for your app
   - Provide a description of what your app does
   - Enter your app's website URL
   - Add callback URLs (e.g., `https://yourdomain.com/api/v1/integrations/twitter/callback`)
   - Specify Terms of Service URL and Privacy Policy URL

4. **Get API Keys and Tokens**
   - After creating the app, you'll be provided with:
     - API Key (Consumer Key)
     - API Secret Key (Consumer Secret)
   - These credentials will be used for OAuth authentication

5. **Set App Permissions**
   - Navigate to your app settings
   - Under "User authentication settings", enable OAuth 2.0
   - Select "Web App" as the app type
   - Configure the callback URL
   - Save your changes

## Required Scopes

For the Social Suit application, you'll need the following scopes:

- `tweet.read` - Read Tweets from Twitter timeline
- `users.read` - Read user profile information
- `like.read` - Read user's liked Tweets
- `like.write` - Like or unlike Tweets on behalf of a user
- `tweet.write` - Post Tweets on behalf of a user
- `offline.access` - Get a refresh token to request new access tokens

## OAuth 2.0 Authorization Flow

### Overview

Twitter uses OAuth 2.0 for user authorization. The flow works as follows:

1. Your application redirects the user to Twitter's authorization page
2. User approves the requested permissions
3. Twitter redirects back to your callback URL with an authorization code
4. Your application exchanges the code for access and refresh tokens
5. Your application uses the access token to make API requests on behalf of the user

### Step-by-Step Implementation

1. **Redirect User to Authorization URL**
   - Construct the authorization URL with your client ID, redirect URI, and requested scopes
   - Redirect the user to this URL

2. **Handle the Callback**
   - Twitter redirects back to your callback URL with a `code` parameter
   - Extract the authorization code from the URL

3. **Exchange Code for Tokens**
   - Make a POST request to Twitter's token endpoint
   - Include the authorization code, client ID, client secret, and redirect URI
   - Receive access token, refresh token, and token expiration time

4. **Store Tokens Securely**
   - Save the access token and refresh token in your database
   - Associate the tokens with the user's account

5. **Use Access Token for API Requests**
   - Include the access token in the Authorization header of API requests

6. **Refresh Access Token When Expired**
   - When the access token expires, use the refresh token to get a new one

## Sample Code for Twitter API Interactions

### Checking if a User Liked a Tweet

```python
import requests

def check_if_user_liked_tweet(access_token, user_id, tweet_id):
    """Check if a user has liked a specific tweet.
    
    Args:
        access_token (str): User's OAuth access token
        user_id (str): Twitter user ID
        tweet_id (str): ID of the tweet to check
        
    Returns:
        bool: True if the user liked the tweet, False otherwise
    """
    url = f"https://api.twitter.com/2/users/{user_id}/liked_tweets"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    params = {
        "tweet.fields": "id",
        "max_results": 100  # Adjust as needed
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        return False
    
    data = response.json()
    if "data" not in data:
        return False
    
    liked_tweets = data["data"]
    for tweet in liked_tweets:
        if tweet["id"] == tweet_id:
            return True
    
    # Check if there are more pages of liked tweets
    if "next_token" in data["meta"]:
        # Implement pagination if needed for users with many likes
        pass
    
    return False
```

### Checking if a User Retweeted a Tweet

```python
def check_if_user_retweeted(access_token, user_id, tweet_id):
    """Check if a user has retweeted a specific tweet.
    
    Args:
        access_token (str): User's OAuth access token
        user_id (str): Twitter user ID
        tweet_id (str): ID of the tweet to check
        
    Returns:
        bool: True if the user retweeted the tweet, False otherwise
    """
    url = f"https://api.twitter.com/2/users/{user_id}/retweets"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        return False
    
    data = response.json()
    if "data" not in data:
        return False
    
    retweets = data["data"]
    for retweet in retweets:
        if retweet["id"] == tweet_id:
            return True
    
    return False
```

## Error Handling

When working with the Twitter API, be prepared to handle these common errors:

- Rate limiting (429 Too Many Requests)
- Authentication errors (401 Unauthorized)
- Permission errors (403 Forbidden)
- Resource not found (404 Not Found)

Implement exponential backoff for rate limit errors and proper error logging for debugging.

## Best Practices

1. **Security**
   - Never expose your API keys and tokens in client-side code
   - Store tokens securely in your database
   - Use HTTPS for all API requests

2. **Performance**
   - Cache API responses when appropriate
   - Minimize the number of API calls
   - Use pagination for large datasets

3. **User Experience**
   - Implement proper error handling and user feedback
   - Provide clear instructions for the authorization process
   - Allow users to revoke access to your app

4. **Compliance**
   - Follow Twitter's Developer Agreement and Policy
   - Respect rate limits
   - Implement proper data retention policies