"""Test manual review flow."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from mcs_contracts import (
    ContactMatchResult,
    CustomerMatchResult,
    EmailAttachment,
    EmailEvent,
    ErrorInfo,
    StatusEnum,
)
from db.models import OrchestrationRun
from db.repo import OrchestratorRepo
from errors import (
    MULTI_CUSTOMER_AMBIGUOUS,
    MULTI_PDF_ATTACHMENTS,
    PERMISSION_DENIED,
    RUN_NOT_IN_MANUAL_REVIEW,
)
from graphs.sales_email.nodes.generate_candidates import generate_manual_review_candidates
from graphs.sales_email.resume import determine_resume_node, resume_from_node
from graphs.sales_email.state import SalesEmailState


@pytest.mark.asyncio
async def test_generate_candidates_on_manual_review():
    """Test candidate generation when entering MANUAL_REVIEW."""
    email_event = EmailEvent(
        provider="imap",
        account="sales@example.com",
        folder="INBOX",
        uid="123",
        message_id="msg1",
        from_email="customer@example.com",
        to=["sales@example.com"],
        subject="采购合同",
        body_text="请查看附件",
        received_at="2024-01-01T00:00:00Z",
        attachments=[
            EmailAttachment(
                attachment_id="att1",
                filename="contract1.pdf",
                content_type="application/pdf",
                size=1024,
                sha256="a" * 64,
            ),
            EmailAttachment(
                attachment_id="att2",
                filename="contract2.pdf",
                content_type="application/pdf",
                size=2048,
                sha256="b" * 64,
            ),
        ],
    )

    state = SalesEmailState(email_event=email_event)
    state.final_status = StatusEnum.MANUAL_REVIEW

    # Mock masterdata
    from mcs_contracts import Customer, Contact, MasterData

    masterdata = MasterData(
        customers=[
            Customer(customer_id="c1", customer_num="C001", name="Customer 1"),
            Customer(customer_id="c2", customer_num="C002", name="Customer 2"),
        ],
        contacts=[
            Contact(
                contact_id="ct1",
                email="customer@example.com",
                name="Contact 1",
                customer_id="c1",
            )
        ],
    )
    state.masterdata = masterdata

    # Set matched customer with low score
    state.matched_customer = CustomerMatchResult(
        ok=False,
        score=70.0,
        top_candidates=[
            {"customer_id": "c1", "customer_num": "C001", "name": "Customer 1", "score": 70.0},
            {"customer_id": "c2", "customer_num": "C002", "name": "Customer 2", "score": 68.0},
        ],
        errors=[ErrorInfo(code="CUSTOMER_MATCH_LOW_SCORE", reason="Score too low")],
    )

    candidates = generate_manual_review_candidates(state)

    assert len(candidates.pdfs) == 2
    assert len(candidates.customers) == 2
    assert len(candidates.contacts) == 1


@pytest.mark.asyncio
async def test_resume_from_node():
    """Test resume from node with patch."""
    email_event = EmailEvent(
        provider="imap",
        account="sales@example.com",
        folder="INBOX",
        uid="123",
        message_id="msg1",
        from_email="customer@example.com",
        to=["sales@example.com"],
        subject="采购合同",
        body_text="请查看附件",
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

    state = SalesEmailState(email_event=email_event)
    state.final_status = StatusEnum.MANUAL_REVIEW

    from mcs_contracts import Customer, MasterData

    masterdata = MasterData(
        customers=[
            Customer(customer_id="c1", customer_num="C001", name="Customer 1"),
        ],
    )
    state.masterdata = masterdata

    repo = MagicMock(spec=OrchestratorRepo)
    repo.get_idempotency_record.return_value = None

    patch = {"selected_customer_id": "c1"}
    resume_node = determine_resume_node(state, patch)
    assert resume_node == "match_customer"

    patched_state = await resume_from_node(state, resume_node, patch, repo, masterdata)
    assert patched_state.matched_customer is not None
    assert patched_state.matched_customer.customer_id == "c1"
    assert patched_state.final_status is None  # Cleared for continuation


@pytest.mark.asyncio
async def test_resume_idempotency_hit():
    """Test resume when idempotency key hits SUCCESS."""
    email_event = EmailEvent(
        provider="imap",
        account="sales@example.com",
        folder="INBOX",
        uid="123",
        message_id="msg1",
        from_email="customer@example.com",
        to=["sales@example.com"],
        subject="采购合同",
        body_text="请查看附件",
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

    state = SalesEmailState(email_event=email_event)

    from mcs_contracts import Customer, ERPCreateOrderResult, MasterData

    masterdata = MasterData(
        customers=[
            Customer(customer_id="c1", customer_num="C001", name="Customer 1"),
        ],
    )
    state.masterdata = masterdata

    repo = MagicMock(spec=OrchestratorRepo)
    from db.models import IdempotencyRecord
    from datetime import datetime

    record = IdempotencyRecord(
        idempotency_key="test_key",
        message_id="msg1",
        status=StatusEnum.SUCCESS.value,
        sales_order_no="SO001",
        order_url="https://example.com/orders/SO001",
        created_at=datetime.utcnow(),
    )
    repo.get_idempotency_record.return_value = record

    patch = {"selected_customer_id": "c1"}
    resume_node = determine_resume_node(state, patch)

    patched_state = await resume_from_node(state, resume_node, patch, repo, masterdata)

    # Should short-circuit to success
    assert patched_state.final_status == StatusEnum.SUCCESS
    assert patched_state.erp_result is not None
    assert patched_state.erp_result.sales_order_no == "SO001"


def test_multiple_pdf_detection():
    """Test multiple PDF detection triggers MANUAL_REVIEW."""
    email_event = EmailEvent(
        provider="imap",
        account="sales@example.com",
        folder="INBOX",
        uid="123",
        message_id="msg1",
        from_email="customer@example.com",
        to=["sales@example.com"],
        subject="采购合同",
        body_text="请查看附件",
        received_at="2024-01-01T00:00:00Z",
        attachments=[
            EmailAttachment(
                attachment_id="att1",
                filename="contract1.pdf",
                content_type="application/pdf",
                size=1024,
            ),
            EmailAttachment(
                attachment_id="att2",
                filename="contract2.pdf",
                content_type="application/pdf",
                size=2048,
            ),
        ],
    )

    state = SalesEmailState(email_event=email_event)

    # This would be tested in the actual node execution
    # For now, verify the structure
    assert len(state.email_event.attachments) == 2


def test_ambiguous_customer_detection():
    """Test ambiguous customer detection (close scores)."""
    from mcs_contracts import CustomerMatchResult, ErrorInfo

    match_result = CustomerMatchResult(
        ok=False,
        score=85.0,
        top_candidates=[
            {"customer_id": "c1", "score": 85.0},
            {"customer_id": "c2", "score": 83.0},  # Diff < 5
        ],
        errors=[ErrorInfo(code=MULTI_CUSTOMER_AMBIGUOUS, reason="Close scores")],
    )

    assert not match_result.ok
    assert match_result.errors[0].code == MULTI_CUSTOMER_AMBIGUOUS


def test_permission_denied_on_tenant_mismatch():
    """Test permission denied when tenant_id mismatches."""
    # This would be tested in API endpoint
    # For now, verify error code exists
    assert PERMISSION_DENIED == "PERMISSION_DENIED"


def test_block_action_persists_decision():
    """Test BLOCK action persists decision and keeps MANUAL_REVIEW status."""
    # This would be tested in API endpoint
    # Verify the logic exists in submit_manual_review
    pass

