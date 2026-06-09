from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user
from app.db.models.user import User
from app.crud.address import (
    create_address,
    delete_address,
    get_address,
    get_user_addresses,
    update_address,
)
from app.schemas.address import AddressCreate, AddressRead, AddressUpdate

import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=List[AddressRead], summary="List user's saved addresses")
def list_addresses(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    try:
        logger.debug(f"Fetching addresses for user {current_user.id}")
        addresses = get_user_addresses(db, current_user.id)
        logger.debug(f"Found {len(addresses)} addresses for user {current_user.id}")
        return addresses
    except Exception as exc:
        logger.exception(f"Error fetching addresses for user {current_user.id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching addresses"
        )


@router.post("", response_model=AddressRead, status_code=status.HTTP_201_CREATED, summary="Create a new address")
def create_new_address(
    address_in: AddressCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    try:
        logger.debug(f"Creating address for user {current_user.id}: {address_in}")
        result = create_address(db, current_user.id, address_in)
        logger.debug(f"Address created successfully: {result.id}")
        return result
    except Exception as exc:
        logger.exception(f"Error creating address for user {current_user.id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating address"
        )


@router.put("/{address_id}", response_model=AddressRead, summary="Update an address")
def update_existing_address(
    address_id: str,
    address_in: AddressUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    address = get_address(db, address_id)
    if not address:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found.")
    if str(address.user_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")

    return update_address(db, address, address_in)


@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete an address")
def delete_existing_address(
    address_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    address = get_address(db, address_id)
    if not address:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found.")
    if str(address.user_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")

    delete_address(db, address)
    return None
