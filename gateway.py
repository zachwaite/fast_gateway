import json

import httpx
from fastapi import APIRouter, FastAPI, Request, Response

app = FastAPI()


async def ensure_valid_key(expected_key: str, observed_key: str) -> bool:
    if expected_key == observed_key:
        return True
    else:
        raise ValueError("BAD API KEY")

def proxy(service_route, valid_api_key):
    async def proxied(request: Request, response: Response):
        await ensure_valid_key(valid_api_key, request.headers['x-api-key'])
        content = await request.body()
        async with httpx.AsyncClient() as client:
            proxy = await client.post(service_route, content=content)
        response.body = proxy.content
        response.status_code = proxy.status_code
        return response
    return proxied

def load_proxy_mappings():
    with open('config.json', 'r') as f:
        raw = json.load(f)
    return raw['proxy_mappings']

proxy_mappings = load_proxy_mappings()
router = APIRouter()
for rec in proxy_mappings:
    router.add_api_route(
        rec['gateway'],
        proxy(rec['service'], rec['api_key']),
        methods=[rec['method']]
    )

app.include_router(router)

