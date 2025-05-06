# FastAPI Portfolio Tracker

A robust and efficient API for tracking stock portfolios, calculating profit, and computing annualized returns.

## Features

- Create and manage stock portfolios with multiple holdings
- Calculate portfolio performance between any two dates
- Compute profit and annualized return for a portfolio
- Efficiently cache stock price data to minimize external API calls
- Handle non-trading days gracefully

## Project Structure

- `main.py`: Database configuration and application entry point
- `models.py`: SQLAlchemy database models
- `schemas.py`: Pydantic models for request/response validation
- `helpers.py`: Utility functions for price fetching and calculations
- `router.py`: FastAPI route handlers

## API Endpoints

### 1. Create Portfolio

**Endpoint**: `POST /portfolio`

**Request Body**:
```json
{
  "name": "My Portfolio",
  "holdings": [
    {"symbol": "AAPL", "quantity": 10},
    {"symbol": "MSFT", "quantity": 5}
  ]
}
```

**Response**:
```json
{
  "id": 1,
  "name": "My Portfolio"
}
```

### 2. Calculate Profit and Annualized Return

**Endpoint**: `GET /portfolio/{portfolio_id}/profit?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`

**Response**:
```json
{
  "portfolio_id": 1,
  "start_value": 1500.0,
  "end_value": 1800.0,
  "profit": 300.0,
  "annualized_return": 0.1847
}
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/postulacion-fintual.git
cd postulacion-fintual
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install fastapi "uvicorn[standard]" sqlalchemy aiosqlite pydantic yfinance python-dateutil
```

## Running the Application

```bash
python main.py
```

The API will be available at http://localhost:8000

## API Documentation

FastAPI automatically generates interactive API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Dependencies

- FastAPI: Web framework
- SQLAlchemy: ORM for database operations
- yfinance: Yahoo Finance API for stock data
- Pydantic: Data validation and settings management
- python-dateutil: Extensions to the standard datetime module