from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from app.db.models.promotion import Promotion, PromotionUsage
from app.db.models.user import User
from types import SimpleNamespace
from sqlalchemy import text


def list_active_promotions(db: Session) -> List[Promotion]:
    now = datetime.utcnow()
    # Use a raw query that adapts to whether the DB column is `metadata_json` or legacy `metadata`.
    engine = db.get_bind()
    with engine.connect() as conn:
        col_check = conn.execute(
            text("SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='promotions' AND column_name='metadata_json')")
        ).scalar()
        meta_col = 'metadata_json' if col_check else 'metadata'
        sql = text(f"SELECT id, code, description, discount_amount, discount_percent, is_active, scheduled_start_at, scheduled_end_at, target_segment, is_stackable, stack_priority, {meta_col} as metadata_json, created_at, updated_at FROM promotions WHERE is_active = true AND (scheduled_start_at IS NULL OR scheduled_start_at <= :now) AND (scheduled_end_at IS NULL OR scheduled_end_at >= :now) ORDER BY stack_priority DESC")
        rows = conn.execute(sql, {'now': now}).fetchall()
        results = []
        for r in rows:
            obj = SimpleNamespace()
            for k in r.keys():
                setattr(obj, k, r[k])
            results.append(obj)
        return results


def _get_metadata(promo: Promotion) -> dict:
    # Support both new (`metadata_json`) and legacy (`metadata`) column names.
    val = getattr(promo, "metadata_json", None)
    if val is None:
        val = getattr(promo, "metadata", None)
    return val or {}


def get_promotion_by_code(db: Session, code: str) -> Optional[Promotion]:
    # Fetch lightweight promotion object using raw SQL to avoid selecting non-existent migration columns.
    engine = db.get_bind()
    with engine.connect() as conn:
        col_check = conn.execute(
            text("SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='promotions' AND column_name='metadata_json')")
        ).scalar()
        meta_col = 'metadata_json' if col_check else 'metadata'
        sql = text(f"SELECT id, code, description, discount_amount, discount_percent, is_active, scheduled_start_at, scheduled_end_at, target_segment, is_stackable, stack_priority, {meta_col} as metadata_json, created_at, updated_at FROM promotions WHERE code = :code AND is_active = true LIMIT 1")
        row = conn.execute(sql, {'code': code}).fetchone()
        if not row:
            return None
        obj = SimpleNamespace()
        for k in row.keys():
            setattr(obj, k, row[k])
        return obj


def validate_promo_for_user(db: Session, user_id, code: str, cart_total_cents: int) -> dict:
    promo = get_promotion_by_code(db, code)
    if not promo:
        return {'valid': False, 'reason': 'not_found'}

    # placeholder rule: if metadata.min_order_amount exists, enforce it
    min_amt = None
    meta = _get_metadata(promo)
    if isinstance(meta, dict):
        min_amt = meta.get('min_order_amount')
    if min_amt and cart_total_cents < int(min_amt):
        return {'valid': False, 'reason': 'min_order_amount'}

    # TODO: check per-user usage limits, segments, etc.
    discount = 0
    if promo.discount_amount:
        discount = int(promo.discount_amount)
    elif promo.discount_percent:
        discount = int((promo.discount_percent / 100.0) * cart_total_cents)

    return {'valid': True, 'discount_cents': discount, 'promo_id': str(promo.id), 'code': promo.code}


def record_promotion_usage(db: Session, promotion_id, user_id, order_id, discount_applied_cents):
    pu = PromotionUsage(promotion_id=promotion_id, user_id=user_id, order_id=order_id, discount_applied=discount_applied_cents)
    db.add(pu)
    db.commit()
    db.refresh(pu)
    return pu


def evaluate_promotions(db: Session, user_id, cart_total_cents: int, codes: list[str] | None = None) -> dict:
    """Evaluate a list of promo codes (or auto-apply available promos) and return the best combination.

    Simple rules implemented:
    - If `codes` provided, validate each; reject those that fail.
    - Non-stackable promos: pick the single highest-discount non-stackable promo.
    - Stackable promos: combine all stackable promos (if provided) with the chosen non-stackable promo.
    - If no codes provided, return active auto-applied promos (is_stackable or platform-wide) that meet min_order_amount.
    Returns: { applied: [{code, promo_id, discount_cents}], total_discount_cents, rejected: [{code, reason}] }
    """
    applied = []
    rejected = []
    total_discount = 0

    active_promos = list_active_promotions(db)

    def promo_min_ok(p):
        meta = _get_metadata(p)
        if isinstance(meta, dict):
            min_amt = meta.get('min_order_amount')
            if min_amt and cart_total_cents < int(min_amt):
                return False
        return True

    promo_map = {p.code.lower(): p for p in active_promos}

    candidates = []
    if codes:
        for c in codes:
            p = promo_map.get(c.lower())
            if not p:
                rejected.append({'code': c, 'reason': 'not_found'})
                continue
            if not promo_min_ok(p):
                rejected.append({'code': c, 'reason': 'min_order_amount'})
                continue
            candidates.append(p)
    else:
        # auto-apply eligible promos
        for p in active_promos:
            if promo_min_ok(p):
                candidates.append(p)

    # separate stackable vs non-stackable
    stackable = [p for p in candidates if p.is_stackable]
    non_stackable = [p for p in candidates if not p.is_stackable]

    chosen_non_stack = None
    if non_stackable:
        # pick highest discount amount for non-stackable
        def compute_discount(p):
            if p.discount_amount:
                return int(p.discount_amount)
            if p.discount_percent:
                return int((p.discount_percent / 100.0) * cart_total_cents)
            return 0

        non_stackable.sort(key=compute_discount, reverse=True)
        chosen_non_stack = non_stackable[0]

    final_promos = []
    if chosen_non_stack:
        final_promos.append(chosen_non_stack)
    final_promos.extend(stackable)

    for p in final_promos:
        if not promo_min_ok(p):
            rejected.append({'code': p.code, 'reason': 'min_order_amount'})
            continue
        if p.discount_amount:
            disc = int(p.discount_amount)
        elif p.discount_percent:
            disc = int((p.discount_percent / 100.0) * cart_total_cents)
        else:
            disc = 0
        total_discount += disc
        applied.append({'code': p.code, 'promo_id': str(p.id), 'discount_cents': disc})

    return {'applied': applied, 'total_discount_cents': total_discount, 'rejected': rejected}
