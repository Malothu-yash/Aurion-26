# app/auth_flow.py
# This file handles the entire Google OAuth 2.0 flow
# for multiple users, storing tokens in Neo4j.

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from googleapiclient.discovery import build, Resource
import os.path

from app.services.memory import get_neo4j_driver  # Import Neo4j driver getter function
from app.core.config import settings

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
# This MUST match the redirect URI in your Google Cloud Console
# Uses BASE_URL from environment (updates automatically for production)
REDIRECT_URI = f"{settings.BASE_URL}/api/v1/auth/google/callback"

auth_router = APIRouter()

def _get_google_flow() -> Flow:
    """Creates a Google Flow object from your credentials file."""
    if not os.path.exists('credentials.json'):
        raise FileNotFoundError(
            "credentials.json not found. "
            "Please download it from Google Cloud Console."
        )
        
    return Flow.from_client_secrets_file(
        'credentials.json',
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )

# --- 1. The "Login" Endpoint (User clicks "Connect Calendar") ---

@auth_router.get("/auth/google/login")
async def auth_google_login(user_id: str = "test-user-123"):
    """
    Generates the Google login URL and redirects the user to it.
    
    Args:
        user_id: The user's ID. In production, this would come from session/JWT.
    """
    flow = _get_google_flow()
    authorization_url, state = flow.authorization_url(
        access_type='offline',    # 'offline' is CRITICAL to get a refresh_token
        prompt='consent',
        state=user_id  # We use 'state' to pass the user_id securely
    )
    
    print(f"🔐 Redirecting user {user_id} to Google for auth...")
    return RedirectResponse(authorization_url)

# --- 2. The "Callback" Endpoint (Google redirects user back here) ---

@auth_router.get("/auth/google/callback")
async def auth_google_callback(request: Request):
    """
    Handles the redirect from Google. Exchanges the code for a
    refresh token and saves it to Neo4j.
    """
    try:
        # 1. Get the code and state from the URL query parameters
        code = request.query_params.get('code')
        user_id = request.query_params.get('state')  # Get user_id back from 'state'

        if not code or not user_id:
            raise HTTPException(400, "Invalid auth callback: missing code or state.")

        # 2. Re-create the flow and exchange the code for tokens
        flow = _get_google_flow()
        flow.fetch_token(code=code)
        
        credentials = flow.credentials
        refresh_token = credentials.refresh_token

        if not refresh_token:
            raise HTTPException(400, "No refresh token received. Make sure 'access_type=offline' was set.")

        # 3. SAVE THE REFRESH TOKEN TO NEO4J
        print(f"💾 Saving refresh token for user {user_id} to Neo4j...")
        neo4j_driver = get_neo4j_driver()
        if not neo4j_driver:
            raise HTTPException(500, "Neo4j driver not initialized.")
            
        async with neo4j_driver.session() as session:
            await session.run(
                """
                MERGE (u:User {id: $user_id})
                MERGE (u)-[r:HAS_CREDENTIAL]->(c:Credential {service: 'google_calendar'})
                SET c.refresh_token = $refresh_token, c.updated_at = timestamp()
                """,
                user_id=user_id,
                refresh_token=refresh_token
            )
        
        print(f"✅ Successfully authenticated user {user_id}!")
        
        # 4. Redirect user back to the (future) frontend
        # For now, just show a success message
        return {
            "message": f"Successfully authenticated user {user_id}! You can close this tab.",
            "status": "success",
            "user_id": user_id
        }

    except Exception as e:
        print(f"❌ Google Auth Callback Error: {e}")
        raise HTTPException(500, f"Authentication failed: {e}")


# --- 3. The Multi-User Service Function (Our tools will use this) ---

async def get_calendar_service_for_user(user_id: str) -> Resource | None:
    """
    Builds a Google Calendar service for a *specific user*
    by fetching their refresh_token from Neo4j.
    
    Returns:
        Google Calendar API service object, or None if not authenticated.
    """
    neo4j_driver = get_neo4j_driver()
    if not neo4j_driver:
        print("⚠️  Neo4j driver not initialized, cannot get calendar service.")
        return None

    # 1. Fetch the user's secret "Valet Key" from Neo4j
    refresh_token = None
    try:
        async with neo4j_driver.session() as session:
            result = await session.run(
                """
                MATCH (u:User {id: $user_id})-[:HAS_CREDENTIAL]->(c:Credential {service: 'google_calendar'})
                RETURN c.refresh_token AS token
                """,
                user_id=user_id
            )
            record = await result.single()
            if record:
                refresh_token = record["token"]
    except Exception as e:
        print(f"❌ Error fetching refresh token from Neo4j: {e}")
        return None
        
    if not refresh_token:
        print(f"⚠️  No Google Calendar refresh token found for user {user_id}.")
        # We will handle this in the orchestrator by asking them to log in
        return None

    try:
        # 2. Build credentials *from* the stored refresh token
        flow = _get_google_flow()
        creds_data = {
            'token': None,  # We don't have a live access token yet
            'refresh_token': refresh_token,
            'client_id': flow.client_config['client_id'],
            'client_secret': flow.client_config['client_secret'],
            'scopes': SCOPES
        }
        creds = Credentials.from_authorized_user_info(creds_data)

        # 3. If the token is expired (it always will be), refresh it
        if not creds.valid or creds.expired:
            print(f"🔄 Token for {user_id} expired. Refreshing...")
            creds.refresh(GoogleRequest())
            # Note: We don't need to re-save the token unless the
            # refresh_token itself is rotated, which is rare.
        
        # 4. Build and return the API service
        service = build('calendar', 'v3', credentials=creds)
        print(f"✅ Successfully built calendar service for user {user_id}")
        return service
        
    except Exception as e:
        print(f"❌ Error building calendar service for {user_id}: {e}")
        # This can happen if the user revoked permission
        return None


# --- 4. Helper Function to Check Auth Status ---

@auth_router.get("/auth/google/status")
async def check_calendar_auth_status(user_id: str):
    """
    Check if a user has connected their Google Calendar.
    
    Args:
        user_id: The user's ID to check.
        
    Returns:
        JSON with auth status.
    """
    service = await get_calendar_service_for_user(user_id)
    
    if service:
        return {
            "status": "connected",
            "user_id": user_id,
            "message": "Google Calendar is connected."
        }
    else:
        return {
            "status": "not_connected",
            "user_id": user_id,
            "message": "Google Calendar not connected. Please authenticate.",
            "auth_url": f"/api/v1/auth/google/login?user_id={user_id}"
        }
