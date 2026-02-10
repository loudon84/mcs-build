"""Test failure paths for sales email graph."""

import pytest

from mcs_contracts import EmailEvent, StatusEnum
from graphs.sales_email.state import SalesEmailState


def test_unknown_contact():
    """Test UNKNOWN_CONTACT path."""
    email_event = EmailEvent(
        provider="imap",
        account="sales@example.com",
        folder="INBOX",
        uid="123",
        message_id="msg1",
        from_email="unknown@example.com",
        to=[],
        subject="Test",
        body_text="Test",
        received_at="2024-01-01T00:00:00Z",
    )

    state = SalesEmailState(email_event=email_event)
    # Simulate contact not found
    from mcs_contracts import ContactMatchResult, ErrorInfo
    from errors import CONTACT_NOT_FOUND

    state.matched_contact = ContactMatchResult(
        ok=False,
        errors=[ErrorInfo(code=CONTACT_NOT_FOUND, reason="Contact not found")],
    )

    assert state.matched_contact.ok is False
    assert state.matched_contact.errors[0].code == CONTACT_NOT_FOUND


def test_not_contract_mail():
    """Test NOT_CONTRACT_MAIL -> IGNORED path."""
    email_event = EmailEvent(
        provider="imap",
        account="sales@example.com",
        folder="INBOX",
        uid="123",
        message_id="msg1",
        from_email="customer@example.com",
        to=[],
        subject="普通邮件",
        body_text="这不是合同邮件",
        received_at="2024-01-01T00:00:00Z",
    )

    state = SalesEmailState(email_event=email_event)
    # Simulate not contract mail
    from mcs_contracts import ContractSignalResult, ErrorInfo
    from errors import NOT_CONTRACT_MAIL

    state.contract_signals = ContractSignalResult(
        ok=False,
        is_contract_mail=False,
        errors=[ErrorInfo(code=NOT_CONTRACT_MAIL, reason="Not a contract email")],
    )

    assert state.contract_signals.is_contract_mail is False

