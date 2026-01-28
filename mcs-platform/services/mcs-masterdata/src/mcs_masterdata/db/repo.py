"""Data access layer for mcs-masterdata."""

from typing import Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from mcs_contracts import Company, Contact, Customer, MasterData, Product
from mcs_masterdata.db.models import Company as CompanyModel
from mcs_masterdata.db.models import Contact as ContactModel
from mcs_masterdata.db.models import Customer as CustomerModel
from mcs_masterdata.db.models import MasterDataVersion
from mcs_masterdata.db.models import Product as ProductModel
from mcs_masterdata.errors import DATABASE_ERROR, DUPLICATE_ENTRY


class MasterDataRepo:
    """Repository for master data operations."""

    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session

    def get_all_masterdata(self) -> MasterData:
        """Get all master data."""
        customers = self.session.scalars(select(CustomerModel)).all()
        contacts = self.session.scalars(select(ContactModel)).all()
        companys = self.session.scalars(select(CompanyModel)).all()
        products = self.session.scalars(select(ProductModel)).all()

        return MasterData(
            customers=[self._customer_to_contract(c) for c in customers],
            contacts=[self._contact_to_contract(c) for c in contacts],
            companys=[self._company_to_contract(c) for c in companys],
            products=[self._product_to_contract(p) for p in products],
        )

    def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Get customer by ID."""
        customer = self.session.get(CustomerModel, customer_id)
        return self._customer_to_contract(customer) if customer else None

    def get_contact_by_email(self, email: str) -> Optional[Contact]:
        """Get contact by email."""
        stmt = select(ContactModel).where(ContactModel.email == email.lower().strip())
        contact = self.session.scalar(stmt)
        return self._contact_to_contract(contact) if contact else None

    def get_company(self, company_id: str) -> Optional[Company]:
        """Get company by ID."""
        company = self.session.get(CompanyModel, company_id)
        return self._company_to_contract(company) if company else None

    def get_product(self, product_id: str) -> Optional[Product]:
        """Get product by ID."""
        product = self.session.get(ProductModel, product_id)
        return self._product_to_contract(product) if product else None

    def create_customer(self, customer: Customer) -> CustomerModel:
        """Create a new customer."""
        existing = self.session.get(CustomerModel, customer.customer_id)
        if existing:
            raise ValueError(f"{DUPLICATE_ENTRY}: Customer {customer.customer_id} already exists")

        db_customer = CustomerModel(
            customer_id=customer.customer_id,
            customer_num=customer.customer_num,
            name=customer.name,
            company_id=customer.company_id,
        )
        self.session.add(db_customer)
        self.session.commit()
        self._increment_version()
        return db_customer

    def create_contact(self, contact: Contact) -> ContactModel:
        """Create a new contact."""
        existing = self.session.get(ContactModel, contact.contact_id)
        if existing:
            raise ValueError(f"{DUPLICATE_ENTRY}: Contact {contact.contact_id} already exists")

        db_contact = ContactModel(
            contact_id=contact.contact_id,
            email=contact.email.lower().strip(),
            name=contact.name,
            customer_id=contact.customer_id,
            telephone=contact.telephone,
        )
        self.session.add(db_contact)
        self.session.commit()
        self._increment_version()
        return db_contact

    def update_customer(self, customer: Customer) -> CustomerModel:
        """Update an existing customer."""
        db_customer = self.session.get(CustomerModel, customer.customer_id)
        if not db_customer:
            raise ValueError(f"Customer {customer.customer_id} not found")

        db_customer.customer_num = customer.customer_num
        db_customer.name = customer.name
        db_customer.company_id = customer.company_id
        self.session.commit()
        self._increment_version()
        return db_customer

    def update_contact(self, contact: Contact) -> ContactModel:
        """Update an existing contact."""
        db_contact = self.session.get(ContactModel, contact.contact_id)
        if not db_contact:
            raise ValueError(f"Contact {contact.contact_id} not found")

        db_contact.email = contact.email.lower().strip()
        db_contact.name = contact.name
        db_contact.customer_id = contact.customer_id
        db_contact.telephone = contact.telephone
        self.session.commit()
        self._increment_version()
        return db_contact

    def bulk_update(self, masterdata: MasterData) -> None:
        """Bulk update master data."""
        try:
            # Clear existing data (or implement merge logic)
            self.session.execute(select(CustomerModel)).delete()
            self.session.execute(select(ContactModel)).delete()
            self.session.execute(select(CompanyModel)).delete()
            self.session.execute(select(ProductModel)).delete()

            # Insert new data
            for customer in masterdata.customers:
                self.session.add(self._customer_to_model(customer))
            for contact in masterdata.contacts:
                self.session.add(self._contact_to_model(contact))
            for company in masterdata.companys:
                self.session.add(self._company_to_model(company))
            for product in masterdata.products:
                self.session.add(self._product_to_model(product))

            self.session.commit()
            self._increment_version()
        except Exception as e:
            self.session.rollback()
            raise ValueError(f"{DATABASE_ERROR}: {str(e)}") from e

    def get_version(self) -> int:
        """Get current master data version."""
        stmt = select(MasterDataVersion).order_by(MasterDataVersion.version.desc()).limit(1)
        version_record = self.session.scalar(stmt)
        return version_record.version if version_record else 0

    def _increment_version(self) -> None:
        """Increment master data version."""
        current_version = self.get_version()
        new_version = MasterDataVersion(version=current_version + 1)
        self.session.add(new_version)
        self.session.commit()

    # Conversion helpers
    def _customer_to_contract(self, db_customer: CustomerModel) -> Customer:
        """Convert database model to contract."""
        return Customer(
            customer_id=db_customer.customer_id,
            customer_num=db_customer.customer_num,
            name=db_customer.name,
            company_id=db_customer.company_id,
        )

    def _contact_to_contract(self, db_contact: ContactModel) -> Contact:
        """Convert database model to contract."""
        return Contact(
            contact_id=db_contact.contact_id,
            email=db_contact.email,
            name=db_contact.name,
            customer_id=db_contact.customer_id,
            telephone=db_contact.telephone,
        )

    def _company_to_contract(self, db_company: CompanyModel) -> Company:
        """Convert database model to contract."""
        return Company(
            company_id=db_company.company_id,
            name=db_company.name,
            address=db_company.address,
        )

    def _product_to_contract(self, db_product: ProductModel) -> Product:
        """Convert database model to contract."""
        return Product(
            product_id=db_product.product_id,
            name=db_product.name,
            unit_price=db_product.unit_price,
        )

    def _customer_to_model(self, customer: Customer) -> CustomerModel:
        """Convert contract to database model."""
        return CustomerModel(
            customer_id=customer.customer_id,
            customer_num=customer.customer_num,
            name=customer.name,
            company_id=customer.company_id,
        )

    def _contact_to_model(self, contact: Contact) -> ContactModel:
        """Convert contract to database model."""
        return ContactModel(
            contact_id=contact.contact_id,
            email=contact.email.lower().strip(),
            name=contact.name,
            customer_id=contact.customer_id,
            telephone=contact.telephone,
        )

    def _company_to_model(self, company: Company) -> CompanyModel:
        """Convert contract to database model."""
        return CompanyModel(
            company_id=company.company_id,
            name=company.name,
            address=company.address,
        )

    def _product_to_model(self, product: Product) -> ProductModel:
        """Convert contract to database model."""
        return ProductModel(
            product_id=product.product_id,
            name=product.name,
            unit_price=product.unit_price,
        )

