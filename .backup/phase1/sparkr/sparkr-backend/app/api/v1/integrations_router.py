from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlmodel import Session
import requests
import secrets
from urllib.parse import urlencode

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.services.auth import get_current_user

router = APIRouter(prefix="/integrations", tags=["integrations"])

# Twitter OAuth configuration
TWITTER_CLIENT_ID = settings.TWITTER_CLIENT_ID
TWITTER_CLIENT_SECRET = settings.TWITTER_CLIENT_SECRET
TWITTER_REDIRECT_URI = f"{settings.API_BASE_URL}/api/v1/integrations/twitter/callback"
TWITTER_AUTH_URL = "https://twitter.com/i/oauth2/authorize"
TWITTER_TOKEN_URL = "https://api.twitter.com/2/oauth2/token"

# Scopes required for the application
TWITTER_SCOPES = [
    "tweet.read",
    "users.read",
    "like.read",
    "like.write",
    "tweet.write",
    "offline.access"
]

@router.get("/twitter/start")
async def twitter_oauth_start(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Start the Twitter OAuth flow by redirecting the user to Twitter's authorization page.
    """
    # Generate a state parameter to prevent CSRF attacks
    state = secrets.token_urlsafe(32)
    
    # Store the state in the session or database to verify it later
    # For this example, we'll assume there's a user_oauth_state table
    # db.execute("INSERT INTO user_oauth_state (user_id, state, provider) VALUES (:user_id, :state, 'twitter')",
    #           {"user_id": current_user.id, "state": state})
    # db.commit()
    
    # Construct the authorization URL
    params = {
        "response_type": "code",
        "client_id": TWITTER_CLIENT_ID,
        "redirect_uri": TWITTER_REDIRECT_URI,
        "scope": " ".join(TWITTER_SCOPES),
        "state": state,
        "code_challenge": "challenge",  # For PKCE, generate a proper challenge
        "code_challenge_method": "plain"  # Use S256 in production
    }
    
    auth_url = f"{TWITTER_AUTH_URL}?{urlencode(params)}"
    return RedirectResponse(auth_url)

@router.get("/twitter/callback")
async def twitter_oauth_callback(request: Request, code: str, state: str, db: Session = Depends(get_db)):
    """
    Handle the callback from Twitter after user authorization.
    """
    # Verify the state parameter to prevent CSRF attacks
    # user_state = db.execute("SELECT * FROM user_oauth_state WHERE state = :state AND provider = 'twitter'",
    #                        {"state": state}).fetchone()
    # if not user_state:
    #     raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    # Exchange the authorization code for access and refresh tokens
    token_data = {
        "code": code,
        "grant_type": "authorization_code",
        "client_id": TWITTER_CLIENT_ID,
        "redirect_uri": TWITTER_REDIRECT_URI,
        "code_verifier": "challenge"  # Should match the challenge used in the authorization request
    }
    
    # Basic auth with client ID and secret
    auth = (TWITTER_CLIENT_ID, TWITTER_CLIENT_SECRET)
    
    try:
        response = requests.post(TWITTER_TOKEN_URL, data=token_data, auth=auth)
        response.raise_for_status()
        tokens = response.json()
        
        # Extract tokens
        access_token = tokens["access_token"]
        refresh_token = tokens.get("refresh_token")
        expires_in = tokens["expires_in"]
        
        # Get user info from Twitter
        user_response = requests.get(
            "https://api.twitter.com/2/users/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        user_response.raise_for_status()
        twitter_user = user_response.json()["data"]
        twitter_id = twitter_user["id"]
        twitter_username = twitter_user["username"]
        
        # Store the tokens and user info in your database
        # user_id = user_state["user_id"]
        # db.execute("""
        #     INSERT INTO user_social_accounts (user_id, provider, provider_user_id, username, access_token, refresh_token, expires_at)
        #     VALUES (:user_id, 'twitter', :twitter_id, :username, :access_token, :refresh_token, NOW() + :expires_in * INTERVAL '1 second')
        #     ON CONFLICT (user_id, provider) DO UPDATE SET
        #         provider_user_id = :twitter_id,
        #         username = :username,
        #         access_token = :access_token,
        #         refresh_token = :refresh_token,
        #         expires_at = NOW() + :expires_in * INTERVAL '1 second'
        # """, {
        #     "user_id": user_id,
        #     "twitter_id": twitter_id,
        #     "username": twitter_username,
        #     "access_token": access_token,
        #     "refresh_token": refresh_token,
        #     "expires_in": expires_in
        # })
        # db.commit()
        
        # Clean up the state
        # db.execute("DELETE FROM user_oauth_state WHERE state = :state", {"state": state})
        # db.commit()
        
        # Redirect to a success page
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/settings/integrations?status=success&provider=twitter")
        
    except requests.RequestException as e:
        # Log the error
        print(f"Error during Twitter OAuth: {str(e)}")
        # Redirect to an error page
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/settings/integrations?status=error&provider=twitter&message={str(e)}")