import httpx # type: ignore
from fastapi import Request, HTTPException, Header, Depends
import os

API_KEY = os.getenv("API_KEY")

def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")


async def call_internal_api(method: str, path: str, **kwargs):
    """Call internal API with consistent error handling."""
    caller_headers = kwargs.pop("headers", {})
    headers = {
        "x-api-key": API_KEY,
        **caller_headers,
    }
    url = f"http://127.0.0.1:8000{path}"
    async with httpx.AsyncClient() as client:
        response = await client.request(method, url, headers=headers, **kwargs)
        if response.status_code != 200:
            raise Exception(f"Internal API error {response.status_code}: {response.text}")
        return response.json()

