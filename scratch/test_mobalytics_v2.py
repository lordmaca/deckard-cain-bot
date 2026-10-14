import asyncio
import aiohttp
from bs4 import BeautifulSoup

async def test_mobalytics_v2():
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
                    for a in soup.find_all('a', href=True):
                        href = a['href']
                        if '/diablo-4/builds/' in href and href != '/diablo-4/builds':
                            # Let's get the title
                            title_div = a.find('p') or a.find('h3') or a.find('h2') or a.find('span')
                            title = title_div.get_text(strip=True) if title_div else a.get_text(strip=True)
                            print(f"URL: {href} | TITLE: {title}")
        except Exception as e:
            print(f"Error: {e}")

asyncio.run(test_mobalytics_v2())
