from fastapi import FastAPI, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from dateutil.parser import parse as parse_date
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from models import Portfolio, Holding
from schemas import PortfolioCreate, ProfitResponse
from helpers import fetch_price, annualized_return
from database import get_session, async_engine, Base

app = FastAPI(title="Portfolio Tracker")

@app.on_event("startup")
async def startup():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# 1. Create portfolio -----------------------------------------------------------
@app.post("/portfolio", status_code=201)
async def create_portfolio(port: PortfolioCreate, session: AsyncSession = Depends(get_session)):
    new_portfolio = Portfolio(name=port.name)
    new_portfolio.holdings = [Holding(symbol=h.symbol.upper(), quantity=h.quantity)
                              for h in port.holdings]
    session.add(new_portfolio)
    await session.commit()
    await session.refresh(new_portfolio)
    return {"id": new_portfolio.id, "name": new_portfolio.name}

# 2. Profit calculation ---------------------------------------------------------
@app.get("/portfolio/{portfolio_id}/profit", response_model=ProfitResponse)
async def portfolio_profit(
    portfolio_id: int,
    start_date: str = Query(..., regex=r"\d{4}-\d{2}-\d{2}"),
    end_date: str   = Query(..., regex=r"\d{4}-\d{2}-\d{2}"),
    session: AsyncSession = Depends(get_session),
):
    try:
        start_dt, end_dt = map(parse_date, (start_date, end_date))
    except ValueError:
        raise HTTPException(400, "Dates must be YYYY-MM-DD")

    if end_dt <= start_dt:
        raise HTTPException(400, "end_date must be after start_date")

    # Fetch portfolio with holdings in a single query
    stmt = select(Portfolio).where(Portfolio.id == portfolio_id).options(selectinload(Portfolio.holdings))
    result = await session.execute(stmt)
    portfolio = result.scalars().first()
    
    if not portfolio:
        raise HTTPException(404, "Portfolio not found")

    start_val, end_val = 0.0, 0.0
    for h in portfolio.holdings:
        price_start = await fetch_price(h.symbol, start_dt, session)
        price_end   = await fetch_price(h.symbol, end_dt, session)
        start_val  += price_start * h.quantity
        end_val    += price_end   * h.quantity

    profit = end_val - start_val
    days   = (end_dt - start_dt).days
    ar     = annualized_return(start_val, end_val, days)

    return ProfitResponse(
        portfolio_id=portfolio_id,
        start_value=round(start_val, 2),
        end_value=round(end_val, 2),
        profit=round(profit, 2),
        annualized_return=round(ar, 4),
    )