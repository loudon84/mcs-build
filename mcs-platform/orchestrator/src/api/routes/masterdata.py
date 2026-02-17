"""Masterdata API routes."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.deps import get_masterdata_service, get_masterdata_session, get_settings
from mcs_contracts import Company, Contact, Customer, MasterData, Product
from services.masterdata_service import MasterDataService
from settings import Settings

router = APIRouter(prefix="/v1/masterdata", tags=["masterdata"])


@router.get("/customers", response_model=list[Customer])
async def get_customers(
    masterdata_service: Annotated[MasterDataService, Depends(get_masterdata_service)],
):
    """Get all customers."""
    masterdata = masterdata_service.get_all()
    return masterdata.customers


@router.get("/contacts", response_model=list[Contact])
async def get_contacts(
    masterdata_service: Annotated[MasterDataService, Depends(get_masterdata_service)],
):
    """Get all contacts."""
    masterdata = masterdata_service.get_all()
    return masterdata.contacts


@router.get("/companies", response_model=list[Company])
async def get_companies(
    masterdata_service: Annotated[MasterDataService, Depends(get_masterdata_service)],
):
    """Get all companies."""
    masterdata = masterdata_service.get_all()
    return masterdata.companys


@router.get("/products", response_model=list[Product])
async def get_products(
    masterdata_service: Annotated[MasterDataService, Depends(get_masterdata_service)],
):
    """Get all products."""
    masterdata = masterdata_service.get_all()
    return masterdata.products


@router.get("/all", response_model=MasterData)
async def get_all(
    masterdata_service: Annotated[MasterDataService, Depends(get_masterdata_service)],
):
    """Get all master data (with caching)."""
    return masterdata_service.get_all()


@router.get("/version", response_model=dict[str, int])
async def get_version(
    masterdata_service: Annotated[MasterDataService, Depends(get_masterdata_service)],
):
    """Get current master data version."""
    version = masterdata_service.get_version()
    return {"version": version}


@router.post("/customers", response_model=Customer, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer: Customer,
    masterdata_service: Annotated[MasterDataService, Depends(get_masterdata_service)],
):
    """Create or update a customer."""
    if not (customer.customer_id or customer.customer_id.strip()):
        customer = customer.model_copy(update={"customer_id": str(uuid.uuid4())})
    try:
        return masterdata_service.create_customer(customer)
    except ValueError as e:
        if "already exists" in str(e):
            # Update instead
            return masterdata_service.update_customer(customer)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/contacts", response_model=Contact, status_code=status.HTTP_201_CREATED)
async def create_contact(
    contact: Contact,
    masterdata_service: Annotated[MasterDataService, Depends(get_masterdata_service)],
):
    """Create or update a contact."""
    if not (contact.contact_id or contact.contact_id.strip()):
        contact = contact.model_copy(update={"contact_id": str(uuid.uuid4())})
    try:
        return masterdata_service.create_contact(contact)
    except ValueError as e:
        if "already exists" in str(e):
            # Update instead
            return masterdata_service.update_contact(contact)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/bulk", status_code=status.HTTP_204_NO_CONTENT)
async def bulk_update(
    masterdata: MasterData,
    masterdata_service: Annotated[MasterDataService, Depends(get_masterdata_service)],
):
    """Bulk update master data."""
    try:
        masterdata_service.bulk_update(masterdata)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
