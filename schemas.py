from typing import List, Optional
from pydantic import BaseModel, Field

class HoldingIn(BaseModel):
    symbol: str = Field(..., example="AAPL")
    quantity: float = Field(..., gt=0)

class PortfolioCreate(BaseModel):
    name: str
    holdings: List[HoldingIn]

class HoldingCreate(BaseModel):
    symbol: str = Field(..., example="MSFT")
    quantity: float = Field(..., gt=0)

class HoldingResponse(BaseModel):
    id: int
    symbol: str
    quantity: float
    
    class Config:
        from_attributes = True

class PortfolioResponse(BaseModel):
    id: int
    name: str
    holdings: Optional[List[HoldingResponse]] = None
    
    class Config:
        from_attributes = True

class ProfitResponse(BaseModel):
    portfolio_id: int
    start_value: float
    end_value: float
    profit: float
    annualized_return: float

    class Config:
        from_attributes = True