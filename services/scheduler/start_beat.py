# start_beat.py
import asyncio
from os import name
from celery_beat_scheduler import beat_job

async def run_beat():
    while True:
        await beat_job()
        await asyncio.sleep(60)  # every 60 seconds

if name == "main":
    asyncio.run(run_beat())