import asyncio
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import AsyncSessionLocal
from app.db.models import Item

async def seed_items():
    async with AsyncSessionLocal() as session:
        # Check if items already exist
        result = await session.execute(select(Item))
        existing_items = result.scalars().all()
        
        if existing_items:
            print("Items already seeded in the database.")
            return

        print("Seeding default items...")
        
        default_items = [
            Item(
                item_id=str(uuid.uuid4()),
                name="Focus Potion",
                type="consumable",
                icon_url="/static/items/focus_potion.webp",
                effects={"focus_multiplier": 1.5, "duration_minutes": 30},
                cost=50,
                is_buyable=True
            ),
            Item(
                item_id=str(uuid.uuid4()),
                name="XP Boost",
                type="consumable",
                icon_url="/static/items/xp_boost.webp",
                effects={"xp_multiplier": 2.0, "duration_minutes": 60},
                cost=100,
                is_buyable=True
            ),
            Item(
                item_id=str(uuid.uuid4()),
                name="Coffee",
                type="consumable",
                icon_url="/static/items/coffee.webp",
                effects={"focus_multiplier": 1.2, "duration_minutes": 15},
                cost=20,
                is_buyable=True
            ),
            Item(
                item_id=str(uuid.uuid4()),
                name="Study Mascot (Owl)",
                type="cosmetic",
                icon_url="/static/items/owl_mascot.webp",
                effects={"profile_badge": "owl"},
                cost=500,
                is_buyable=True
            )
        ]
        
        session.add_all(default_items)
        await session.commit()
        
        print("Successfully seeded default items!")

if __name__ == "__main__":
    asyncio.run(seed_items())
