import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re

def slug_to_title(slug):
    return " ".join(word.capitalize() for word in slug.split("-"))

async def test_mobalytics_v4():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            print("Checking Mobalytics...")
            async with session.get("https://mobalytics.gg/diablo-4/builds", timeout=15) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, "lxml")
                    
                    # Encontrar todos os links de builds
                    links = set()
                    for a in soup.find_all('a', href=True):
                        href = a['href']
                        if href.startswith('/diablo-4/builds/') and href != '/diablo-4/builds/':
                            links.add(href)
                            
                    for href in list(links)[:10]: # Check first 10
                        slug = href.split('/')[-1]
                        build_name = slug_to_title(slug)
                        full_url = f"https://mobalytics.gg{href}"
                        print(f"Name: {build_name} | URL: {full_url}")
        except Exception as e:
            print(f"Error: {e}")

asyncio.run(test_mobalytics_v4())
