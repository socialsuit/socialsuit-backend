from sqlalchemy import Column, String, DateTime, Integer
from services.database.database import Base

class UserToken(Base):
    tablename = "user_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    access_token = Column(String)
    platform = Column(String)  # e.g. facebook, instagram
    expires_at = Column(DateTime)