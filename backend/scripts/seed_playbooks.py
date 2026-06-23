"""
Seed Script — loads standard playbook clauses into Qdrant.
Run: python -m scripts.seed_playbooks
"""
import asyncio
import logging

from scripts.seed_data import PLAYBOOKS

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


async def seed() -> dict[str, str]:
    from rag.qdrant_client import init_qdrant, upsert_playbook_clauses

    logger.info("Initializing Qdrant collection...")
    await init_qdrant()

    vector_map: dict[str, str] = {}
    for playbook in PLAYBOOKS:
        logger.info(f"Seeding playbook: {playbook['name']} ({len(playbook['clauses'])} clauses)")
        mapping = await upsert_playbook_clauses(
            playbook_id=playbook["id"],
            playbook_name=playbook["name"],
            contract_type=playbook["contract_type"],
            clauses=playbook["clauses"],
        )
        vector_map.update(mapping)
        logger.info(f"  ✓ {len(mapping)} vectors upserted")

    logger.info(f"\n✅ Qdrant seeding complete. Total vectors: {len(vector_map)}")
    return vector_map


if __name__ == "__main__":
    asyncio.run(seed())
