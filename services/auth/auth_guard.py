from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services.core.dependencies import get_current_user
from sqlalchemy.orm import Session
from services.database.database import get_db

security = HTTPBearer()

def auth_required(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    return get_current_user(token=token, db=db)
