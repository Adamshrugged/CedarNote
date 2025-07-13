import httpx # type: ignore

async def call_internal_api(method: str, path: str, **kwargs):
    """Call internal API with consistent error handling."""
    url = f"http://127.0.0.1:8000{path}"
    async with httpx.AsyncClient() as client:
        response = await client.request(method, url, **kwargs)
        if response.status_code != 200:
            raise Exception(f"Internal API error {response.status_code}: {response.text}")
        return response.json()
