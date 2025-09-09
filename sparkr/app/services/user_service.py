from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from sparkr.app.models.models import User


async def get_user_by_email(email: str, session: AsyncSession) -> Optional[User]:
    """Get a user by email"""
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def authenticate_user(email: str, password: str, session: AsyncSession) -> Optional[User]:
    """Authenticate a user"""
    from sparkr.app.core.security import verify_password
    
    user = await get_user_by_email(email, session)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user