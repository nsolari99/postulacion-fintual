from typing import List
from pydantic import BaseModel, Field

class HoldingIn(BaseModel):
    symbol: str = Field(..., example="AAPL")
    quantity: float = Field(..., gt=0)

class PortfolioCreate(BaseModel):
    name: str
    holdings: List[HoldingIn]

class ProfitResponse(BaseModel):
    portfolio_id: int
    start_value: float
    end_value: float
    profit: float
    annualized_return: float

    class Config:
        from_attributes = True