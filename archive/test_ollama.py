import httpx
import asyncio
import logging


async def test_httpx(url):
    logging.debug(f"Testing httpx with url: {url}")
    try:
        async with httpx.AsyncClient(base_url=url) as client:
            response = await client.get("/")  # Simple GET request
            logging.debug(f"httpx response from {url}: {response.status_code}")
            return response.status_code
    except Exception as e:
        logging.error(f"httpx error with {url}: {e}")
        return None


async def main():
    urls = ["http://localhost:11434", "http://localhost:11435"]
    tasks = [test_httpx(url) for url in urls]
    results = await asyncio.gather(*tasks)
    logging.info(f"httpx test results: {results}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
