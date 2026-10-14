import asyncio
import aiohttp
from bs4 import BeautifulSoup
import json

async def test_mobalytics():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            print("Checking Mobalytics...")
            async with session.get("https://mobalytics.gg/diablo-4/builds", timeout=15) as response:
                print(f"Status: {response.status}")
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, "lxml")
                    # Looking for NEXT_DATA
                    script = soup.find("script", id="__NEXT_DATA__")
                    if script:
                        print("Found NEXT_DATA")
                        data = json.loads(script.string)
                        # We don't know the exact path yet, let's just dump some keys
                        print(list(data.keys()))
                        print(list(data.get('props', {}).keys()))
                        print(list(data.get('props', {}).get('pageProps', {}).keys()))
                    else:
                        print("No NEXT_DATA found, checking links")
                        for a in soup.find_all('a', href=True):
                            if '/diablo-4/builds/' in a['href']:
                                print(a['href'])
        except Exception as e:
            print(f"Error: {e}")

asyncio.run(test_mobalytics())
