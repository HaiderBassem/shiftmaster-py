import asyncio
import httpx
from datetime import datetime

async def main():
    async with httpx.AsyncClient(base_url='http://api:8000') as client:
        # We need a valid token. Let's just bypass it or use the token from test
        pass
