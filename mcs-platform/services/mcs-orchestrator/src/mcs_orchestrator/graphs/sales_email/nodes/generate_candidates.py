"""Generate manual review candidates."""

from mcs_contracts import (
    ManualReviewCandidateContact,
    ManualReviewCandidateCustomer,
    ManualReviewCandidatePdf,
    ManualReviewCandidates,
)
from mcs_orchestrator.graphs.sales_email.state import SalesEmailState
from mcs_orchestrator.tools.similarity import normalize_filename


def generate_manual_review_candidates(state: SalesEmailState) -> ManualReviewCandidates:
    """Generate candidates for manual review."""
    candidates = ManualReviewCandidates()

    # Generate PDF candidates
    if state.email_event.attachments:
        pdf_attachments = [
            att for att in state.email_event.attachments
            if att.content_type == "application/pdf" or att.filename.lower().endswith(".pdf")
        ]

        # Mark the first/largest as suggested if only one, or none if multiple
        suggested_pdf_id = None
        if len(pdf_attachments) == 1:
            suggested_pdf_id = pdf_attachments[0].attachment_id
        elif state.pdf_attachment:
            suggested_pdf_id = state.pdf_attachment.attachment_id

        for pdf in pdf_attachments:
            candidates.pdfs.append(
                ManualReviewCandidatePdf(
                    attachment_id=pdf.attachment_id,
                    filename=pdf.filename,
                    sha256=pdf.sha256,
                    size=pdf.size,
                    suggested=(pdf.attachment_id == suggested_pdf_id),
                )
            )

    # Generate customer candidates
    if state.matched_customer and state.matched_customer.top_candidates:
        # Mark the first one as suggested if score is high enough
        suggested_customer_id = None
        if state.matched_customer.ok and state.matched_customer.score >= 75.0:
            suggested_customer_id = state.matched_customer.customer_id

        for candidate in state.matched_customer.top_candidates[:3]:  # Top 3
            customer_id = candidate["customer_id"]
            customer = state.masterdata.get_customer_by_id(customer_id) if state.masterdata else None

            if customer:
                normalized_filename = (
                    normalize_filename(state.pdf_attachment.filename)
                    if state.pdf_attachment
                    else ""
                )
                candidates.customers.append(
                    ManualReviewCandidateCustomer(
                        customer_id=customer.customer_id,
                        customer_num=customer.customer_num,
                        customer_name=customer.name,
                        score=candidate.get("score", 0.0),
                        evidence={
                            "matched_tokens": [normalized_filename],
                            "filename_normalized": normalized_filename,
                        },
                        suggested=(customer_id == suggested_customer_id),
                    )
                )

    # Generate contact candidates
    if state.masterdata:
        # If contact matched, include it
        if state.matched_contact and state.matched_contact.ok and state.matched_contact.contact_id:
            contact = state.masterdata.get_contact_by_email(state.email_event.from_email)
            if contact:
                candidates.contacts.append(
                    ManualReviewCandidateContact(
                        contact_id=contact.contact_id,
                        name=contact.name,
                        email=contact.email,
                        telephone=contact.telephone,
                        customer_id=contact.customer_id,
                        suggested=True,  # Only one contact candidate
                    )
                )
        # If contact not found, try to find contacts by customer_id
        elif state.matched_customer and state.matched_customer.ok:
            customer_id = state.matched_customer.customer_id
            for contact in state.masterdata.contacts:
                if contact.customer_id == customer_id:
                    candidates.contacts.append(
                        ManualReviewCandidateContact(
                            contact_id=contact.contact_id,
                            name=contact.name,
                            email=contact.email,
                            telephone=contact.telephone,
                            customer_id=contact.customer_id,
                            suggested=(contact.email.lower() == state.email_event.from_email.lower()),
                        )
                    )

    # Ensure only one suggested per category
    _ensure_single_suggested(candidates)

    return candidates


def _ensure_single_suggested(candidates: ManualReviewCandidates) -> None:
    """Ensure only one suggested candidate per category."""
    # PDFs
    suggested_pdfs = [p for p in candidates.pdfs if p.suggested]
    if len(suggested_pdfs) > 1:
        # Keep only the first one
        for pdf in candidates.pdfs:
            pdf.suggested = (pdf == suggested_pdfs[0])

    # Customers
    suggested_customers = [c for c in candidates.customers if c.suggested]
    if len(suggested_customers) > 1:
        # Keep only the highest score
        best = max(suggested_customers, key=lambda c: c.score)
        for customer in candidates.customers:
            customer.suggested = (customer == best)

    # Contacts
    suggested_contacts = [c for c in candidates.contacts if c.suggested]
    if len(suggested_contacts) > 1:
        # Keep only the first one
        for contact in candidates.contacts:
            contact.suggested = (contact == suggested_contacts[0])

