from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from database import get_db, User
from extra.service import GmailService

router = APIRouter()
gmail_service = GmailService()

@router.get("/auth/login", tags=["Authentication"])
async def login():
    auth_url, _ = gmail_service.get_auth_url()
    return {"auth_url": auth_url}

@router.get("/auth/callback", tags=["Authentication"])
async def callback(request: Request, db: Session = Depends(get_db)):
    try:
        # Extract code from query parameters
        code = request.query_params.get("code")
        
        if not code:
            raise HTTPException(status_code=400, detail="Authorization code not provided")
        
        # Exchange code for tokens
        credentials = gmail_service.exchange_code_for_tokens(code)
        
        # Get user info from Google's userinfo endpoint
        user_info = gmail_service.get_user_info(credentials.token)
        if not user_info:
            raise HTTPException(status_code=400, detail="Failed to get user info")
        
        # Check if user exists by email
        user = db.query(User).filter(User.email == user_info['email']).first()
        
        if user:
            # Update existing user tokens
            user.access_token = credentials.token
            user.refresh_token = credentials.refresh_token
            if not user.google_id:  # Update google_id if it's empty
                user.google_id = user_info['id']
            if not user.name:  # Update name if it's empty
                user.name = user_info.get('name', '')
        else:
            # Create new user
            user = User(
                email=user_info['email'],
                name=user_info.get('name', ''),
                google_id=user_info['id'],
                access_token=credentials.token,
                refresh_token=credentials.refresh_token
            )
            db.add(user)
        
        db.commit()
        
        # Redirect to FastAPI Swagger UI with success message
        return RedirectResponse(url=f"/auth/success?email={user.email}&name={user.name}")
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")

@router.get("/auth/success", response_class=HTMLResponse, tags=["Authentication"])
async def auth_success(email: str = Query(...), name: str = Query(...)):
    """Success page after OAuth authentication"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Authentication Successful</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .success-container {{
                background-color: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                text-align: center;
            }}
            .success-icon {{
                font-size: 48px;
                color: #4CAF50;
                margin-bottom: 20px;
            }}
            .user-info {{
                background-color: #f8f9fa;
                padding: 20px;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .api-links {{
                margin-top: 30px;
            }}
            .api-links a {{
                display: inline-block;
                margin: 10px;
                padding: 12px 24px;
                background-color: #007bff;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                transition: background-color 0.3s;
            }}
            .api-links a:hover {{
                background-color: #0056b3;
            }}
            .endpoint-example {{
                background-color: #f8f9fa;
                padding: 15px;
                border-left: 4px solid #007bff;
                margin: 10px 0;
                font-family: monospace;
                text-align: left;
            }}
        </style>
    </head>
    <body>
        <div class="success-container">
            <div class="success-icon">✅</div>
            <h1>Authentication Successful!</h1>
            <p>Welcome to your Gmail-like App API</p>
            
            <div class="user-info">
                <h3>User Information</h3>
                <p><strong>Email:</strong> {email}</p>
                <p><strong>Name:</strong> {name}</p>
            </div>
            
            <div class="api-links">
                <h3>Quick Access</h3>
                <a href="/docs" target="_blank">📋 API Documentation (Swagger UI)</a>
                <a href="/redoc" target="_blank">📖 API Documentation (ReDoc)</a>
                <a href="/users/me?email={email}" target="_blank">👤 View Your Profile</a>
            </div>
            
            <div style="margin-top: 30px;">
                <h3>Next Steps</h3>
                <p>Now you can use the following endpoints with your email parameter:</p>
                
                <div class="endpoint-example">
                    <strong>Sync Emails:</strong><br>
                    POST /emails/sync?email={email}
                </div>
                
                <div class="endpoint-example">
                    <strong>Get Emails:</strong><br>
                    GET /emails?email={email}
                </div>
                
                <div class="endpoint-example">
                    <strong>Send Email:</strong><br>
                    POST /emails/send?email={email}&to=recipient@example.com&subject=Test&body=Hello
                </div>
                
                <div class="endpoint-example">
                    <strong>Create Draft:</strong><br>
                    POST /drafts?email={email}
                </div>
                <div class="endpoint-example">
                    <strong>Create Calendar Event:</strong><br>
                    POST /calendar/events?email={email}
                </div>
                <div class="endpoint-example">
                    <strong>List Calendar Events:</strong><br>
                    GET /calendar/events?email={email}
                </div>
            </div>
            
            <p style="margin-top: 30px; color: #666;">
                <small>You can now close this tab and use the API endpoints in Swagger UI</small>
            </p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)