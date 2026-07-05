import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.models import base as models_base
from app.processors.content_generator import ContentGenerator


async def main():
    print("Initializing Database Connection...")
    models_base.init_db(settings.DATABASE_URL)

    print("Running Content Generator...")
    created = await ContentGenerator().run()
    print(f"Created {created} content piece(s).")


if __name__ == "__main__":
    asyncio.run(main())
