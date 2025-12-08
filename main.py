from contextlib import asynccontextmanager
from os import getenv
from typing import Annotated, AsyncIterator
from redis.asyncio import Redis
from fastapi import Body, Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from data_types import HomeAddress, Phone, State

REDIS_HOST = getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(getenv("REDIS_PORT", 6379))

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[State]:
    """
    Integrate redis client using FastAPI lifespan events and request state.

    https://starlette.dev/lifespan/#lifespan-state
    """
    client = Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    yield {"client": client}
    await client.aclose()


app = FastAPI(lifespan=lifespan)


async def client(request: Request) -> Redis:
    """
    Shared redis client dependency.
    """
    return request.state.client


ClientDep = Annotated[Redis, Depends(client)]


@app.get("/", include_in_schema=False)
async def docs_redirect(request: Request):
    """
    UI not implemented, redirect directly to docs.
    """
    return RedirectResponse(url="/docs")


@app.post("/home-address", status_code=status.HTTP_201_CREATED)
async def create_address(
    phone: Phone,
    home_address: Annotated[
        HomeAddress,
        Body(),
    ],
    client: ClientDep,
):
    """
    Creating new phone->home_address collection.
    """

    print(phone)

    if await client.exists(phone):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Извините, ваш телефон ({phone}) уже в базе данных.",
        )

    await client.hmset(phone, home_address.model_dump())  # type: ignore


@app.get("/home-address", response_model=HomeAddress)
async def read_address(
    phone: Phone,
    client: ClientDep,
):
    """
    Return phone->home_address collection.
    """

    print(phone)

    address = await client.exists(phone)
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Извините, ваш телефон ({phone}) не найден.",
        )

    return await client.hgetall(phone)


@app.put("/home-address")
async def update_address(
    phone: Phone,
    home_address: Annotated[
        HomeAddress,
        Body(),
    ],
    client: ClientDep,
):
    """
    Updating phone->home_address collection.
    """
    if not await client.exists(phone):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Извините, ваш телефон ({phone}) не найден.",
        )

    await client.hmset(phone, home_address.model_dump())  # type: ignore


@app.delete("/home-address", status_code=status.HTTP_204_NO_CONTENT)
async def delete_address(
    phone: Phone,
    client: ClientDep,
):
    """
    Delete phone->home_address collection.
    """
    keys = await client.hkeys(phone)
    if not keys:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Извините, ваш телефон ({phone}) не найден.",
        )

    await client.hdel(phone, *keys)
