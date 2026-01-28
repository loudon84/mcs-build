"""API routes for mcs-masterdata."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from mcs_contracts import Company, Contact, Customer, MasterData, Product
from api.deps import get_cache, get_db_session, get_repo, get_settings
from cache.memory_cache import MemoryCache
from cache.redis_cache import RedisCache
from db.repo import MasterDataRepo
from settings import Settings

router = APIRouter(prefix="/v1/masterdata", tags=["masterdata"])


@router.get("/customers", response_model=list[Customer])
async def get_customers(
    repo: Annotated[MasterDataRepo, Depends(get_repo)],
    session: Annotated[Session, Depends(get_db_session)],
):
    """Get all customers."""
    masterdata = repo.get_all_masterdata()
    return masterdata.customers


@router.get("/contacts", response_model=list[Contact])
async def get_contacts(
    repo: Annotated[MasterDataRepo, Depends(get_repo)],
    session: Annotated[Session, Depends(get_db_session)],
):
    """Get all contacts."""
    masterdata = repo.get_all_masterdata()
    return masterdata.contacts


@router.get("/companies", response_model=list[Company])
async def get_companies(
    repo: Annotated[MasterDataRepo, Depends(get_repo)],
    session: Annotated[Session, Depends(get_db_session)],
):
    """Get all companies."""
    masterdata = repo.get_all_masterdata()
    return masterdata.companys


@router.get("/products", response_model=list[Product])
async def get_products(
    repo: Annotated[MasterDataRepo, Depends(get_repo)],
    session: Annotated[Session, Depends(get_db_session)],
):
    """Get all products."""
    masterdata = repo.get_all_masterdata()
    return masterdata.products


@router.get("/all", response_model=MasterData)
async def get_all(
    repo: Annotated[MasterDataRepo, Depends(get_repo)],
    cache: Annotated[MemoryCache | RedisCache, Depends(get_cache)],
    session: Annotated[Session, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
):
    """Get all master data (with caching)."""
    version = repo.get_version()

    # Try cache first
    if isinstance(cache, RedisCache):
        cached_data = await cache.get_all(version)
    else:
        cached_data = cache.get_all(version)

    if cached_data:
        return cached_data

    # Cache miss, load from DB
    masterdata = repo.get_all_masterdata()

    # Update cache
    if isinstance(cache, RedisCache):
        await cache.set_all(masterdata, version)
    else:
        cache.set_all(masterdata, version)

    return masterdata


@router.get("/version", response_model=dict[str, int])
async def get_version(
    repo: Annotated[MasterDataRepo, Depends(get_repo)],
    session: Annotated[Session, Depends(get_db_session)],
):
    """Get current master data version."""
    version = repo.get_version()
    return {"version": version}


@router.post("/customers", response_model=Customer, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer: Customer,
    repo: Annotated[MasterDataRepo, Depends(get_repo)],
    session: Annotated[Session, Depends(get_db_session)],
    cache: Annotated[MemoryCache | RedisCache, Depends(get_cache)],
):
    """Create or update a customer."""
    try:
        repo.create_customer(customer)
        # Invalidate cache
        if isinstance(cache, RedisCache):
            await cache.invalidate()
        else:
            cache.invalidate()
        return customer
    except ValueError as e:
        if "already exists" in str(e):
            # Update instead
            repo.update_customer(customer)
            if isinstance(cache, RedisCache):
                await cache.invalidate()
            else:
                cache.invalidate()
            return customer
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/contacts", response_model=Contact, status_code=status.HTTP_201_CREATED)
async def create_contact(
    contact: Contact,
    repo: Annotated[MasterDataRepo, Depends(get_repo)],
    session: Annotated[Session, Depends(get_db_session)],
    cache: Annotated[MemoryCache | RedisCache, Depends(get_cache)],
):
    """Create or update a contact."""
    try:
        repo.create_contact(contact)
        # Invalidate cache
        if isinstance(cache, RedisCache):
            await cache.invalidate()
        else:
            cache.invalidate()
        return contact
    except ValueError as e:
        if "already exists" in str(e):
            # Update instead
            repo.update_contact(contact)
            if isinstance(cache, RedisCache):
                await cache.invalidate()
            else:
                cache.invalidate()
            return contact
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/bulk", status_code=status.HTTP_204_NO_CONTENT)
async def bulk_update(
    masterdata: MasterData,
    repo: Annotated[MasterDataRepo, Depends(get_repo)],
    session: Annotated[Session, Depends(get_db_session)],
    cache: Annotated[MemoryCache | RedisCache, Depends(get_cache)],
):
    """Bulk update master data."""
    try:
        repo.bulk_update(masterdata)
        # Invalidate cache
        if isinstance(cache, RedisCache):
            await cache.invalidate()
        else:
            cache.invalidate()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

