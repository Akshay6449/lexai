"""
Seed playbook and playbook_clause rows in PostgreSQL.
"""
import asyncio
import logging
from datetime import datetime

from sqlalchemy import select

from core.database import (
    AsyncSessionLocal,
    Playbook,
    PlaybookClause,
    User,
    ContractType,
    ClauseType,
)
from scripts.seed_data import PLAYBOOKS

logger = logging.getLogger(__name__)


async def seed() -> int:
    created_playbooks = 0
    created_clauses = 0

    async with AsyncSessionLocal() as db:
        admin = (
            await db.execute(select(User).where(User.email == "admin@lexai.com"))
        ).scalar_one_or_none()

        for pb_data in PLAYBOOKS:
            existing = (
                await db.execute(select(Playbook).where(Playbook.name == pb_data["name"]))
            ).scalar_one_or_none()

            if existing:
                playbook = existing
                logger.info(f"  skip playbook (exists): {pb_data['name']}")
            else:
                playbook = Playbook(
                    name=pb_data["name"],
                    description=pb_data.get("description"),
                    contract_type=ContractType(pb_data["contract_type"]),
                    clause_count=len(pb_data["clauses"]),
                    qdrant_synced=False,
                    created_by=admin.id if admin else None,
                )
                db.add(playbook)
                await db.flush()
                created_playbooks += 1
                logger.info(f"  created playbook: {pb_data['name']}")

            for clause_data in pb_data["clauses"]:
                clause_exists = (
                    await db.execute(
                        select(PlaybookClause).where(
                            PlaybookClause.playbook_id == playbook.id,
                            PlaybookClause.title == clause_data["title"],
                        )
                    )
                ).scalar_one_or_none()

                if clause_exists:
                    continue

                db.add(PlaybookClause(
                    playbook_id=playbook.id,
                    clause_type=ClauseType(clause_data["clause_type"]),
                    title=clause_data["title"],
                    standard_text=clause_data["standard_text"],
                    notes=f"seed_id:{clause_data['id']}",
                ))
                created_clauses += 1

            playbook.clause_count = len(pb_data["clauses"])

        await db.commit()

    logger.info(
        f"Playbooks DB: {created_playbooks} playbooks, {created_clauses} clauses created"
    )
    return created_playbooks + created_clauses


async def sync_vector_ids(vector_map: dict[str, str]) -> int:
    """Link Qdrant vector IDs to playbook_clause rows after vector upsert."""
    if not vector_map:
        return 0

    updated = 0
    now = datetime.utcnow()

    async with AsyncSessionLocal() as db:
        for pb_data in PLAYBOOKS:
            playbook = (
                await db.execute(select(Playbook).where(Playbook.name == pb_data["name"]))
            ).scalar_one_or_none()
            if not playbook:
                continue

            for clause_data in pb_data["clauses"]:
                seed_id = clause_data["id"]
                vector_id = vector_map.get(seed_id)
                if not vector_id:
                    continue

                clause = (
                    await db.execute(
                        select(PlaybookClause).where(
                            PlaybookClause.playbook_id == playbook.id,
                            PlaybookClause.title == clause_data["title"],
                        )
                    )
                ).scalar_one_or_none()
                if clause:
                    clause.qdrant_vector_id = vector_id
                    updated += 1

            playbook.qdrant_synced = True
            playbook.last_synced_at = now

        await db.commit()

    logger.info(f"Playbooks DB: {updated} clause vector IDs synced")
    return updated


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    asyncio.run(seed())
