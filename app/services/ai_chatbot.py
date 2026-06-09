"""AI chatbot service for customer queries about restaurants, menu items, locations, etc.

Uses OpenRouter API (OpenAI-compatible) to provide natural-language answers
based on live database data.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from openai import OpenAI
from sqlalchemy.orm import Session

from app.core.config import settings

logger = logging.getLogger(__name__)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openai/gpt-4o-mini"  # Fast, cheap, and widely available on OpenRouter


def _gather_restaurant_context(db: Session) -> dict[str, Any]:
    """Collect all relevant restaurant data for AI context."""
    from app.db.models.menu_item import MenuItem
    from app.db.models.restaurant import Restaurant

    restaurants = db.query(Restaurant).filter(Restaurant.is_active == True).all()
    rows = []
    for r in restaurants:
        items = (
            db.query(MenuItem)
            .filter(MenuItem.restaurant_id == r.id, MenuItem.is_available == True)
            .all()
        )
        rows.append({
            "name": r.name,
            "cuisine": r.cuisine,
            "description": r.description,
            "address": r.address,
            "rating": r.rating,
            "delivery_time_minutes": r.delivery_time,
            "menu_items": [
                {
                    "name": i.name,
                    "category": i.category,
                    "description": i.description,
                    "price": i.price,
                    "is_veg": i.is_veg,
                }
                for i in items
            ],
        })
    return {"restaurants": rows}


def _build_system_prompt(context: dict[str, Any]) -> str:
    """Build a system prompt with the restaurant data context."""
    restaurant_data = json.dumps(context, indent=2, ensure_ascii=False, default=str)
    return f"""You are QuickBites AI, a helpful restaurant assistant for the QuickBites food delivery app.
Your role is to answer customer questions about restaurants, menu items, cuisines, pricing, locations, and availability.

Rules:
- Answer ONLY based on the restaurant data provided below. Do not make up information.
- If you don't know the answer, say so politely and suggest the customer browse the app.
- Be friendly, concise, and helpful.
- When suggesting dishes, mention the restaurant name and price.
- You can help with: restaurant suggestions, menu recommendations, cuisine filtering, price ranges, dietary preferences (veg/non-veg), and general information.
- Keep responses under 150 words unless the user asks for more detail.

Here is the current restaurant data:
{restaurant_data}"""


def answer_question(db: Session, question: str) -> str:
    """Answer a customer's question using OpenRouter API and live DB data."""
    api_key = settings.OPENROUTER_API_KEY
    if not api_key:
        return "Sorry, the AI assistant is not configured yet. Please contact support."

    try:
        client = OpenAI(
            base_url=OPENROUTER_BASE_URL,
            api_key=api_key,
        )

        context = _gather_restaurant_context(db)
        system_prompt = _build_system_prompt(context)

        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
            temperature=0.7,
            max_tokens=500,
            top_p=0.9,
            extra_headers={
                "HTTP-Referer": "https://quickbites.app",
                "X-Title": "QuickBites AI Chat",
            },
        )

        reply = response.choices[0].message.content
        return reply.strip() if reply else "I couldn't generate an answer. Please try rephrasing your question."

    except Exception as e:
        error_str = str(e)
        logger.exception("AI chatbot error: %s", error_str)
        if "quota" in error_str.lower() or "insufficient_quota" in error_str.lower() or "rate_limit" in error_str.lower():
            return "The AI assistant has reached its usage limit. Please try again later or contact support to upgrade the API plan."
        return "Sorry, I encountered an issue processing your request. Please try again later."
