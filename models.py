from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base


class Portfolio(Base):
    __tablename__ = "portfolios"

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String, nullable=False)
    holdings    = relationship("Holding", back_populates="portfolio", cascade="all, delete-orphan")


class Holding(Base):
    __tablename__ = "holdings"

    id           = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    symbol       = Column(String, nullable=False, index=True)
    quantity     = Column(Float, nullable=False)

    portfolio = relationship("Portfolio", back_populates="holdings")


class Price(Base):
    __tablename__ = "prices"
    __table_args__ = (UniqueConstraint("symbol", "date", name="_symbol_date_uc"),)

    id      = Column(Integer, primary_key=True)
    symbol  = Column(String, index=True)
    date    = Column(Date, index=True)
    adjclose = Column(Float, nullable=False)