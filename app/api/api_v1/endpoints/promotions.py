from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_active_user
from app.services import promotions as promotions_service

router = APIRouter()


class ValidateRequest(BaseModel):
    # support either single `code` or list `codes`
    code: str | None = None
    codes: list[str] | None = None
    cart_total_cents: int


@router.get('/active')
def list_active(db: Session = Depends(get_db)):
    promos = promotions_service.list_active_promotions(db)
    return {'promotions': [{'id': str(p.id), 'code': p.code, 'description': p.description, 'discount_amount': p.discount_amount, 'discount_percent': p.discount_percent} for p in promos]}


@router.post('/validate')
def validate(req: ValidateRequest, current_user=Depends(get_current_active_user), db: Session = Depends(get_db)):
    # support single code for backward compatibility
    if req.code and not req.codes:
        res = promotions_service.validate_promo_for_user(db, current_user.id, req.code, req.cart_total_cents)
        if not res.get('valid'):
            raise HTTPException(status_code=400, detail=res.get('reason', 'invalid'))
        return {'applied': [{'code': res.get('code'), 'promo_id': res.get('promo_id'), 'discount_cents': int(res.get('discount_cents', 0))}], 'total_discount_cents': int(res.get('discount_cents', 0)), 'rejected': []}

    codes = req.codes or ([] if not req.code else [req.code])
    res = promotions_service.evaluate_promotions(db, current_user.id, req.cart_total_cents, codes)
    return res



@router.get('/restaurants/{restaurant_id}')
def list_restaurant_promotions(restaurant_id: str, db: Session = Depends(get_db)):
    promos = promotions_service.list_active_promotions(db)
    # filter by restaurant_id if promotion targets a restaurant via metadata
    out = []
    for p in promos:
        md = getattr(p, 'metadata_json', None) or {}
        target_rest = md.get('restaurant_id')
        if target_rest and str(target_rest) != str(restaurant_id):
            continue
        out.append({'id': str(p.id), 'code': p.code, 'description': p.description, 'discount_amount': p.discount_amount, 'discount_percent': p.discount_percent})
    return {'promotions': out}
