import aiohttp
import asyncio
import json
from bs4 import BeautifulSoup

async def test_d4builds():
    url = "https://d4builds.gg/builds/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(url, timeout=15) as response:
                print(f"Status: {response.status}")
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, "lxml")
                    script = soup.find("script", id="__NEXT_DATA__")
                    if script:
                        data = json.loads(script.string)
                        page_props = data.get("props", {}).get("pageProps", {})
                        builds = page_props.get("builds", []) or page_props.get("initialBuilds", [])
                        print(f"D4Builds: Found {len(builds)} builds")
                        for b in builds[:3]:
                            print(f"- {b.get('title')} (Season: {b.get('season')})")
                    else:
                        print("D4Builds: Could not find __NEXT_DATA__")
        except Exception as e:
            print(f"D4Builds Error: {e}")

async def test_maxroll():
    url = "https://maxroll.gg/d4/build-guides"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(url, timeout=15) as response:
                print(f"Status: {response.status}")
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, "lxml")
                    script = soup.find("script", id="__NEXT_DATA__")
                    if script:
                        data = json.loads(script.string)
                        page_props = data.get("props", {}).get("pageProps", {})
                        guides = page_props.get("guides", []) or page_props.get("allGuides", [])
                        print(f"Maxroll: Found {len(guides)} guides")
                        for g in guides[:3]:
                            print(f"- {g.get('title')}")
                    else:
                        print("Maxroll: Could not find __NEXT_DATA__")
        except Exception as e:
            print(f"Maxroll Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_d4builds())
    asyncio.run(test_maxroll())
