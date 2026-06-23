"""
Seed default users matching the UI quick-login buttons.
"""
import asyncio
import logging

from sqlalchemy import select

from auth.jwt_handler import hash_password
from core.database import AsyncSessionLocal, User, UserRole

logger = logging.getLogger(__name__)

DEFAULT_PASSWORD = "Admin@1234"

USERS = [
    {
        "email": "admin@lexai.com",
        "full_name": "Admin User",
        "role": UserRole.admin,
    },
    {
        "email": "manager@lexai.com",
        "full_name": "Legal Manager",
        "role": UserRole.legal_manager,
    },
    {
        "email": "reviewer@lexai.com",
        "full_name": "Legal Reviewer",
        "role": UserRole.legal_reviewer,
    },
]


async def seed() -> int:
    created = 0
    async with AsyncSessionLocal() as db:
        for spec in USERS:
            existing = (
                await db.execute(select(User).where(User.email == spec["email"]))
            ).scalar_one_or_none()
            if existing:
                logger.info(f"  skip user (exists): {spec['email']}")
                continue

            db.add(User(
                email=spec["email"],
                full_name=spec["full_name"],
                password_hash=hash_password(DEFAULT_PASSWORD),
                role=spec["role"],
            ))
            created += 1
            logger.info(f"  created user: {spec['email']} ({spec['role'].value})")

        await db.commit()

    logger.info(f"Users: {created} created, {len(USERS) - created} skipped")
    return created


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    asyncio.run(seed())
