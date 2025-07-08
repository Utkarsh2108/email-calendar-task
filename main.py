from fastapi import FastAPI
from routes import auth, user, email, draft, calendar
from extra.service import GmailService

# Tags metadata
tags_metadata = [
    {"name": "Authentication"},
    {"name": "Users"},
    {"name": "Calendar Events"},
    {"name": "Inbox"},
    {"name": "Email Sending"},
    {"name": "Email Actions"},
    {"name": "Email Star"},
    {"name": "Drafts"},

]

# Create FastAPI app
app = FastAPI(title="Gmail and Calendar", openapi_tags=tags_metadata)

# Initialize Gmail service (shared across routers)
gmail_service = GmailService()

# Include routers
app.include_router(auth.router, dependencies=[])
app.include_router(user.router, dependencies=[])
app.include_router(calendar.router, dependencies=[])
app.include_router(email.router, dependencies=[])
app.include_router(draft.router, dependencies=[])


# Make gmail_service available to routers
app.state.gmail_service = gmail_service

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)