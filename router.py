from fastapi import FastAPI, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from dateutil.parser import parse as parse_date
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from typing import List

from models import Portfolio, Holding
from schemas import PortfolioCreate, ProfitResponse, PortfolioResponse, HoldingCreate, HoldingResponse
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

# 3. Get all portfolios ---------------------------------------------------------
@app.get("/portfolios", response_model=List[PortfolioResponse])
async def get_all_portfolios(session: AsyncSession = Depends(get_session)):
    # Fetch all portfolios with their holdings
    stmt = select(Portfolio).options(selectinload(Portfolio.holdings))
    result = await session.execute(stmt)
    portfolios = result.scalars().all()
    
    return portfolios

# 4. Add holding to portfolio ---------------------------------------------------
@app.post("/portfolio/{portfolio_id}/holding", response_model=PortfolioResponse)
async def add_holding(
    portfolio_id: int,
    holding: HoldingCreate,
    session: AsyncSession = Depends(get_session)
):
    # Find the portfolio
    stmt = select(Portfolio).where(Portfolio.id == portfolio_id).options(selectinload(Portfolio.holdings))
    result = await session.execute(stmt)
    portfolio = result.scalars().first()
    
    if not portfolio:
        raise HTTPException(404, "Portfolio not found")
    
    # Check if holding with same symbol already exists
    for existing_holding in portfolio.holdings:
        if existing_holding.symbol == holding.symbol.upper():
            # Update quantity instead of creating new
            existing_holding.quantity += holding.quantity
            await session.commit()
            await session.refresh(portfolio)
            return portfolio
    
    # Add new holding
    new_holding = Holding(
        portfolio_id=portfolio_id,
        symbol=holding.symbol.upper(),
        quantity=holding.quantity
    )
    
    session.add(new_holding)
    await session.commit()
    
    # Refresh portfolio to include the new holding
    await session.refresh(portfolio)
    
    return portfolio