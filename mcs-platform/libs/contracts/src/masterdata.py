"""Master data models."""

from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class Customer(BaseModel):
    """Customer model."""

    customer_id: str = Field(..., description="Customer identifier")
    customer_num: str = Field(..., description="Customer number")
    name: str = Field(..., description="Customer name")
    company_id: Optional[str] = Field(None, description="Associated company ID")


class Contact(BaseModel):
    """Contact model."""

    contact_id: str = Field(..., description="Contact identifier")
    email: EmailStr = Field(..., description="Contact email address")
    name: str = Field(..., description="Contact name")
    customer_id: str = Field(..., description="Associated customer ID")
    telephone: Optional[str] = Field(None, description="Contact telephone")


class Company(BaseModel):
    """Company model."""

    company_id: str = Field(..., description="Company identifier")
    name: str = Field(..., description="Company name")
    address: Optional[str] = Field(None, description="Company address")


class Product(BaseModel):
    """Product model."""

    product_id: str = Field(..., description="Product identifier")
    name: str = Field(..., description="Product name")
    unit_price: Optional[float] = Field(None, description="Unit price", ge=0)


class MasterData(BaseModel):
    """Master data container."""

    customers: list[Customer] = Field(default_factory=list, description="Customer list")
    contacts: list[Contact] = Field(default_factory=list, description="Contact list")
    companys: list[Company] = Field(default_factory=list, description="Company list")
    products: list[Product] = Field(default_factory=list, description="Product list")

    def get_customer_by_id(self, customer_id: str) -> Customer | None:
        """Get customer by ID."""
        return next((c for c in self.customers if c.customer_id == customer_id), None)

    def get_contact_by_email(self, email: str) -> Contact | None:
        """Get contact by email (case-insensitive)."""
        email_lower = email.lower().strip()
        return next((c for c in self.contacts if c.email.lower() == email_lower), None)

    def get_company_by_id(self, company_id: str) -> Company | None:
        """Get company by ID."""
        return next((c for c in self.companys if c.company_id == company_id), None)

    def get_product_by_id(self, product_id: str) -> Product | None:
        """Get product by ID."""
        return next((p for p in self.products if p.product_id == product_id), None)

