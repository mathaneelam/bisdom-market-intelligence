import asyncio
from sqlalchemy import text
from app.models import base as models_base
from app.config import settings

async def clean_noise():
    models_base.init_db(settings.DATABASE_URL)
    async with models_base.AsyncSessionLocal() as session:
        queries = [
            "raw_content ILIKE '%JD.com%'",
            "raw_content ILIKE '%decarbonisation%'",
            "raw_content ILIKE '%returns friction%'",
            "raw_content ILIKE '%Abercrombie & Fitch%'"
        ]
        
        where_clause = " OR ".join(queries)
        
        res = await session.execute(text(f"SELECT id FROM signals WHERE {where_clause}"))
        s_ids = [str(r[0]) for r in res.fetchall()]
        if not s_ids:
            print('No noise found.')
            return
            
        print(f'Found {len(s_ids)} noisy signals.')
        s_ids_str = ','.join(f"'{i}'" for i in s_ids)
        
        res2 = await session.execute(text(f"SELECT id FROM processed_signals WHERE signal_id IN ({s_ids_str})"))
        ps_ids = [str(r[0]) for r in res2.fetchall()]
        
        if ps_ids:
            ps_ids_str = ','.join(f"'{i}'" for i in ps_ids)
            await session.execute(text(f"DELETE FROM signal_patterns WHERE signal_id IN ({ps_ids_str})"))
            
        await session.execute(text(f"DELETE FROM signal_patterns WHERE signal_id IN ({s_ids_str})"))
        await session.execute(text(f"DELETE FROM processed_signals WHERE signal_id IN ({s_ids_str})"))
        await session.execute(text(f"DELETE FROM signals WHERE id IN ({s_ids_str})"))
        
        await session.commit()
        print('Noise cleaned up successfully!')

if __name__ == '__main__':
    asyncio.run(clean_noise())
