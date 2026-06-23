"""
Master seed script — users, playbooks (Postgres + Qdrant), demo contracts.
Run: python -m scripts.seed
"""
import asyncio
import logging

from scripts import seed_users, seed_playbooks_db, seed_playbooks, seed_demo_data

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


async def seed_all():
    logger.info("=== Step 1/4: Users ===")
    await seed_users.seed()

    logger.info("=== Step 2/4: Playbooks (PostgreSQL) ===")
    await seed_playbooks_db.seed()

    logger.info("=== Step 3/4: Playbooks (Qdrant vectors) ===")
    vector_map = await seed_playbooks.seed()
    await seed_playbooks_db.sync_vector_ids(vector_map)

    logger.info("=== Step 4/4: Demo contracts ===")
    await seed_demo_data.seed()

    logger.info("\n✅ All seed steps complete.")
    logger.info("Login: admin@lexai.com / Admin@1234  (also manager@, reviewer@)")


if __name__ == "__main__":
    asyncio.run(seed_all())
