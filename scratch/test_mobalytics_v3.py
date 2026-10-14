import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
import json

async def test_mobalytics_v3():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            print("Checking Mobalytics...")
            async with session.get("https://mobalytics.gg/diablo-4/builds", timeout=15) as response:
                if response.status == 200:
                    html = await response.text()
                    # Mobalytics often puts state in window.__initialState or similar
                    match = re.search(r'window\.__initialState\s*=\s*(\{.*?\});', html)
                    if match:
                        print("Found __initialState")
                        # Just checking if we can parse it
                    else:
                        print("No __initialState found")
                        soup = BeautifulSoup(html, "lxml")
                        scripts = soup.find_all('script')
                        for s in scripts:
                            if s.string and 'build' in s.string.lower():
                                print(f"Script len: {len(s.string)}")
                                if len(s.string) > 1000:
                                    print("Large script containing 'build' found")
        except Exception as e:
            print(f"Error: {e}")

asyncio.run(test_mobalytics_v3())
