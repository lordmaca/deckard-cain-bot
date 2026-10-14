import asyncio
import aiohttp
from bs4 import BeautifulSoup
import json

async def check_updates():
    headers = {"User-Agent": "Mozilla/5.0"}
    async with aiohttp.ClientSession(headers=headers) as session:
        # D4Builds
        print("Checking D4Builds...")
        async with session.get("https://d4builds.gg/builds/", timeout=15) as r:
            if r.status == 200:
                soup = BeautifulSoup(await r.text(), "lxml")
                script = soup.find("script", id="__NEXT_DATA__")
                if script:
                    data = json.loads(script.string)
                    props = data.get("props", {}).get("pageProps", {})
                    builds = props.get("builds", []) or props.get("initialBuilds", [])
                    if builds:
                        print(f"D4Builds sample keys: {builds[0].keys()}")
                    else:
                        print(f"No builds array found in D4Builds props keys: {props.keys()}")

        # Maxroll
        print("Checking Maxroll...")
        async with session.get("https://maxroll.gg/d4/build-guides", timeout=15) as r:
            if r.status == 200:
                soup = BeautifulSoup(await r.text(), "lxml")
                script = soup.find("script", id="__NEXT_DATA__")
                if script:
                    data = json.loads(script.string)
                    props = data.get("props", {}).get("pageProps", {})
                    guides = props.get("guides", []) or props.get("allGuides", [])
                    if guides:
                        print(f"Maxroll sample keys: {guides[0].keys()}")
                    else:
                        print(f"No guides array found in Maxroll props keys: {props.keys()}")

asyncio.run(check_updates())
