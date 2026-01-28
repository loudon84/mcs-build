"""Test schema examples and validation."""

import pytest

from mcs_contracts import (
    Contact,
    ContactMatchResult,
    Customer,
    EmailAttachment,
    EmailEvent,
    ErrorInfo,
    MasterData,
    OrchestratorRunResult,
    StatusEnum,
)


def test_email_event_parse_success():
    """Test EmailEvent parsing success."""
    event = EmailEvent(
        provider="imap",
        account="sales@example.com",
        folder="INBOX",
        uid="12345",
        message_id="<msg@example.com>",
        from_email="customer@example.com",
        to=["sales@example.com"],
        subject="采购合同",
        body_text="请查看附件中的采购合同",
        received_at="2024-01-01T00:00:00Z",
        attachments=[
            EmailAttachment(
                attachment_id="att1",
                filename="contract.pdf",
                content_type="application/pdf",
                size=1024,
                sha256="a" * 64,
            )
        ],
    )
    assert event.from_email == "customer@example.com"
    assert len(event.attachments) == 1


def test_email_event_from_email_normalization():
    """Test EmailEvent from_email normalization."""
    event = EmailEvent(
        provider="imap",
        account="sales@example.com",
        folder="INBOX",
        uid="12345",
        message_id="<msg@example.com>",
        from_email="  Customer@Example.COM  ",
        to=[],
        subject="Test",
        body_text="Test",
        received_at="2024-01-01T00:00:00Z",
    )
    assert event.from_email == "customer@example.com"


def test_email_event_missing_field_fails():
    """Test EmailEvent missing required field fails."""
    with pytest.raises(Exception):  # Pydantic validation error
        EmailEvent(
            provider="imap",
            account="sales@example.com",
            folder="INBOX",
            uid="12345",
            # message_id missing
            from_email="customer@example.com",
            to=[],
            subject="Test",
            body_text="Test",
            received_at="2024-01-01T00:00:00Z",
        )


def test_masterdata_example():
    """Test MasterData example."""
    masterdata = MasterData(
        customers=[
            Customer(customer_id="c1", customer_num="C001", name="Customer 1")
        ],
        contacts=[
            Contact(
                contact_id="ct1",
                email="contact@example.com",
                name="Contact 1",
                customer_id="c1",
            )
        ],
        companys=[],
        products=[],
    )
    assert len(masterdata.customers) == 1
    assert masterdata.get_customer_by_id("c1") is not None
    assert masterdata.get_contact_by_email("contact@example.com") is not None


def test_contact_match_result():
    """Test ContactMatchResult."""
    result = ContactMatchResult(
        ok=True,
        contact_id="ct1",
        warnings=[],
        errors=[],
    )
    assert result.ok is True
    assert result.contact_id == "ct1"


def test_orchestrator_run_result():
    """Test OrchestratorRunResult."""
    result = OrchestratorRunResult(
        run_id="run1",
        message_id="msg1",
        status=StatusEnum.SUCCESS,
        started_at="2024-01-01T00:00:00Z",
        finished_at="2024-01-01T00:01:00Z",
        sales_order_no="SO001",
        order_url="https://example.com/orders/SO001",
    )
    assert result.status == StatusEnum.SUCCESS
    assert result.sales_order_no == "SO001"

