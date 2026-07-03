import os
import sys
import json
import asyncio
import logging

# Add backend to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.mongo_models import get_db, init_db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_database")

async def main():
    logger.info("Initializing database seed script...")
    init_db_connection()
    
    db = await get_db()
    
    library_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "capability_library.json")
    if not os.path.exists(library_path):
        logger.error(f"Capability library file not found: {library_path}")
        return

    with open(library_path, "r") as f:
        records = json.load(f)

    logger.info(f"Loaded {len(records)} capability records from {library_path}")

    # Clear old collection
    await db.capability_records.delete_many({})
    logger.info("Cleared existing capability records.")

    # Convert ID key
    for r in records:
        r["_id"] = r.pop("id")

    # Ingest records
    result = await db.capability_records.insert_many(records)
    logger.info(f"Successfully seeded {len(result.inserted_ids)} capability records into MongoDB!")

if __name__ == "__main__":
    asyncio.run(main())
