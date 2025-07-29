from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.sql import func
from services.database.database import Base

class PlatformToken(Base):
    __tablename__ = "platform_tokens"   # ✅ Correct magic attribute

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), index=True)
    platform = Column(String, index=True)  # e.g. facebook, instagram, twitter
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    channel_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def repr(self):   # ✅ Also better to name this repr
        return f"<PlatformToken(platform={self.platform}, user_id={self.user_id})>"