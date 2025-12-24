from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict, Any

Stage = Literal["INIT","RESEARCH_DONE","PRICING_DONE","CONTENT_DONE","HUMAN_REVIEW","APPROVED","REJECTED","STOPPED"]

class ResearchOut(BaseModel):
    summary: str
    market_position: Literal["low","low-mid","mid","mid-high","high"]
    risks: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    confidence: Literal["low","medium","high"]
    next: Literal["PRICING","STOP"]

class PricingOut(BaseModel):
    suggested_price_range: List[int]
    assumptions: List[str] = Field(default_factory=list)
    margin_estimate: Literal["poor","ok","good"]
    notes: List[str] = Field(default_factory=list)
    next: Literal["CONTENT","STOP"]

class ContentOut(BaseModel):
    title: str
    bullets: List[str]
    faq: List[str]
    claims_risk: Literal["low","medium","high"]
    next: Literal["HUMAN_REVIEW"]

class State(BaseModel):
    stage: Stage = "INIT"
    product_name: str = "Foldbar laptop-stand"
    supplier_cost: float = 12.5
    shipping_days: int = 9
    supplier_rating: float = 4.3
    research: Optional[ResearchOut] = None
    pricing: Optional[PricingOut] = None
    content: Optional[ContentOut] = None
    audit_log: List[Dict[str, Any]] = Field(default_factory=list)
