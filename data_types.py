from typing import Annotated, TypedDict
from fastapi import Query
from pydantic_extra_types.phone_numbers import PhoneNumber
from redis.asyncio import Redis
from pydantic import BaseModel


class State(TypedDict):
    client: Redis


class RUPhone(PhoneNumber):
    default_region_code = "RU"
    supported_regions = ["RU"]


Phone = Annotated[RUPhone, Query(example="tel:+7-999-999-99-99")]


# Potentially we can use smarter model, maybe even some API to verify that
# model, https://dadata.ru/
class HomeAddress(BaseModel):
    street: str
    apartment_number: str
    city: str
    state_province: str
    postal_code: str
    country: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "street": "Кошкина 11",
                    "apartment_number": "12 б.",
                    "city": "Москва",
                    "postal_code": "770000",
                    "country": "Russia",
                }
            ]
        }
    }
