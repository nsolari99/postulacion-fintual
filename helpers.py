from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import yfinance as yf

from models import Price

async def fetch_price(symbol: str, day: datetime, session: AsyncSession) -> float:
    """Return adjusted close for the closest ≤day trading date, caching in DB."""
    # 1.  Check cache
    stmt = select(Price).where(Price.symbol == symbol, Price.date == day.date())
    if price := (await session.execute(stmt)).scalar_one_or_none():
        return price.adjclose

    # 2.  Hit yfinance – we request a small window around the target date
    window_start = day - timedelta(days=7)
    ticker = yf.Ticker(symbol)
    try:
        hist = ticker.history(start=window_start.strftime("%Y-%m-%d"),
                              end=(day + timedelta(days=1)).strftime("%Y-%m-%d"),
                              auto_adjust=False)
    except Exception as e:
        raise HTTPException(400, f"Error fetching {symbol}: {e}")

    if hist.empty:
        raise HTTPException(400, f"Ticker '{symbol}' not supported or has no data.")

    # pick the last trading day ≤ requested date
    hist = hist[hist.index <= str(day.date())]
    if hist.empty:
        raise HTTPException(400, f"No price for {symbol} on or before {day.date()}")

    adjclose = float(hist["Adj Close"].iloc[-1])
    actual_date = hist.index[-1].to_pydatetime().date()

    # 3.  Cache it
    session.add(Price(symbol=symbol, date=actual_date, adjclose=adjclose))
    await session.commit()
    return adjclose

def annualized_return(start_value: float, end_value: float, days: int) -> float:
    if days == 0:
        return 0.0
    return (end_value / start_value) ** (365 / days) - 1