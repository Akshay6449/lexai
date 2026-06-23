"""
Seed Script — loads standard playbook clauses into Qdrant.
Run: python -m scripts.seed_playbooks
"""
import asyncio
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# ── Playbook Data ─────────────────────────────────────────────
# In production these are loaded from the database (Playbook + PlaybookClause tables).
# This seed script bootstraps the initial vector store.

NDA_CLAUSES = [
    {
        "id": "nda-liability-1",
        "clause_type": "liability",
        "title": "NDA Standard — Mutual Liability Cap",
        "standard_text": (
            "Neither party's aggregate liability under this Agreement shall exceed the greater of "
            "(a) five hundred thousand dollars ($500,000) or (b) the total fees paid by Customer "
            "in the twelve (12) month period preceding the event giving rise to the claim, "
            "regardless of the form of action and whether in contract, tort, or otherwise."
        ),
    },
    {
        "id": "nda-confidentiality-1",
        "clause_type": "confidentiality",
        "title": "NDA Standard — Confidentiality Obligation",
        "standard_text": (
            "Each party shall protect the other party's Confidential Information using at least "
            "the same degree of care used to protect its own confidential information of similar "
            "sensitivity, but in no event less than reasonable care, for a period of five (5) years "
            "from the date of disclosure."
        ),
    },
    {
        "id": "nda-termination-1",
        "clause_type": "termination",
        "title": "NDA Standard — Termination for Convenience",
        "standard_text": (
            "Either party may terminate this Agreement for any reason or no reason upon thirty (30) "
            "days prior written notice to the other party. Termination shall not affect any rights "
            "or obligations accrued prior to the effective date of termination."
        ),
    },
    {
        "id": "nda-governing-1",
        "clause_type": "governing_law",
        "title": "NDA Standard — Governing Law (Delaware)",
        "standard_text": (
            "This Agreement shall be governed by and construed in accordance with the laws of the "
            "State of Delaware, without regard to its conflict of law provisions. Any disputes "
            "shall be resolved by binding arbitration under AAA Commercial Arbitration Rules."
        ),
    },
]

MSA_CLAUSES = [
    {
        "id": "msa-indemnification-1",
        "clause_type": "indemnification",
        "title": "MSA Standard — Mutual Indemnification with Cap",
        "standard_text": (
            "Each party ('Indemnitor') shall indemnify, defend, and hold harmless the other party "
            "('Indemnitee') from and against any third-party claims arising from the Indemnitor's "
            "gross negligence or willful misconduct. The Indemnitor's aggregate indemnification "
            "obligations shall not exceed two times (2x) the annual contract value."
        ),
    },
    {
        "id": "msa-ip-1",
        "clause_type": "intellectual_property",
        "title": "MSA Standard — IP Ownership",
        "standard_text": (
            "Each party retains all right, title, and interest in its pre-existing intellectual "
            "property. Any work product created by Vendor specifically for Customer under a "
            "Statement of Work shall be owned by Customer upon full payment. Vendor retains "
            "ownership of its general tools, methodologies, and know-how."
        ),
    },
    {
        "id": "msa-payment-1",
        "clause_type": "payment",
        "title": "MSA Standard — Payment Terms",
        "standard_text": (
            "Customer shall pay all undisputed invoices within thirty (30) days of receipt. "
            "Late payments shall accrue interest at the lesser of 1.5% per month or the maximum "
            "rate permitted by law. Vendor may suspend services after sixty (60) days of non-payment "
            "following written notice."
        ),
    },
    {
        "id": "msa-data-1",
        "clause_type": "data_privacy",
        "title": "MSA Standard — Data Processing & GDPR/CCPA",
        "standard_text": (
            "Vendor shall process Customer's personal data solely as a data processor on Customer's "
            "documented instructions. Vendor shall implement appropriate technical and organizational "
            "measures to ensure security of personal data per GDPR Article 32 and CCPA §1798.100. "
            "Vendor shall notify Customer of any data breach within seventy-two (72) hours of discovery."
        ),
    },
]

SLA_CLAUSES = [
    {
        "id": "sla-liability-1",
        "clause_type": "liability",
        "title": "SLA Standard — Service Credit Cap",
        "standard_text": (
            "Customer's sole remedy for any SLA breach shall be service credits as defined in "
            "Schedule A. Total service credits in any calendar month shall not exceed fifteen percent "
            "(15%) of the monthly recurring fees. Service credits do not apply to downtime caused "
            "by Customer's actions, third-party failures, or force majeure events."
        ),
    },
    {
        "id": "sla-termination-1",
        "clause_type": "termination",
        "title": "SLA Standard — Termination for Cause",
        "standard_text": (
            "Either party may terminate this Agreement for material breach upon thirty (30) days "
            "written notice if the breach is not cured within such period. Customer may terminate "
            "immediately if Vendor fails to meet the agreed SLA for three (3) consecutive months."
        ),
    },
]

PLAYBOOKS = [
    {
        "id": "pb-nda-001",
        "name": "NDA Standards",
        "contract_type": "NDA",
        "clauses": NDA_CLAUSES,
    },
    {
        "id": "pb-msa-001",
        "name": "MSA Standards",
        "contract_type": "MSA",
        "clauses": MSA_CLAUSES,
    },
    {
        "id": "pb-sla-001",
        "name": "SLA Standards",
        "contract_type": "SLA",
        "clauses": SLA_CLAUSES,
    },
]


async def seed():
    from rag.qdrant_client import init_qdrant, upsert_playbook_clauses

    logger.info("Initializing Qdrant collection...")
    await init_qdrant()

    total = 0
    for playbook in PLAYBOOKS:
        logger.info(f"Seeding playbook: {playbook['name']} ({len(playbook['clauses'])} clauses)")
        count = await upsert_playbook_clauses(
            playbook_id=playbook["id"],
            playbook_name=playbook["name"],
            contract_type=playbook["contract_type"],
            clauses=playbook["clauses"],
        )
        total += count
        logger.info(f"  ✓ {count} vectors upserted")

    logger.info(f"\n✅ Seeding complete. Total vectors: {total}")


if __name__ == "__main__":
    asyncio.run(seed())
