from pydantic import BaseModel, Field


class Stock(BaseModel):
    qty: int
    wh: int


class Size(BaseModel):
    size_name: str = Field(alias="origName")
    stocks: list[Stock]


class Product(BaseModel):
    sizes: list[Size]
