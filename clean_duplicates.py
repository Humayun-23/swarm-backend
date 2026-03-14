import asyncio
from sqlalchemy import select, func, delete
from app.database.session import AsyncSessionLocal
from app.database.models import Participant

async def clean_duplicates():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Participant))
        participants = result.scalars().all()
        
        seen = set()
        to_delete = []
        for p in participants:
            key = (p.event_id, p.email)
            if key in seen:
                to_delete.append(p.id)
            else:
                seen.add(key)
        
        if to_delete:
            await db.execute(delete(Participant).where(Participant.id.in_(to_delete)))
            await db.commit()
            print(f"Deleted {len(to_delete)} duplicate participants.")
        else:
            print("No duplicates found.")

if __name__ == "__main__":
    asyncio.run(clean_duplicates())
