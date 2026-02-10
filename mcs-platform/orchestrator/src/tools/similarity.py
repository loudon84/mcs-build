"""Similarity matching tools."""

from rapidfuzz import fuzz

from mcs_contracts import Customer, CustomerMatchResult, ErrorInfo
from errors import CUSTOMER_MATCH_LOW_SCORE


def normalize_filename(name: str) -> str:
    """Normalize filename for matching."""
    # Remove extension, lowercase, strip
    name = name.rsplit(".", 1)[0] if "." in name else name
    return name.lower().strip()


def match_customer_by_filename(
    filename: str,
    customers: list[Customer],
    threshold: float = 75.0,
) -> CustomerMatchResult:
    """Match customer by filename using fuzzy matching."""
    normalized_filename = normalize_filename(filename)
    top_candidates = []

    for customer in customers:
        # Try customer name
        score_name = fuzz.token_set_ratio(normalized_filename, customer.name.lower())
        # Try customer number
        score_num = fuzz.partial_ratio(normalized_filename, customer.customer_num.lower())
        # Take the higher score
        score = max(score_name, score_num)

        if score >= threshold:
            top_candidates.append(
                {
                    "customer_id": customer.customer_id,
                    "customer_num": customer.customer_num,
                    "name": customer.name,
                    "score": score,
                }
            )

    # Sort by score descending
    top_candidates.sort(key=lambda x: x["score"], reverse=True)
    top_candidates = top_candidates[:3]  # Top 3

    if not top_candidates:
        return CustomerMatchResult(
            ok=False,
            score=0.0,
            top_candidates=[],
            errors=[
                ErrorInfo(
                    code=CUSTOMER_MATCH_LOW_SCORE,
                    reason=f"No customer match found above threshold {threshold}",
                    details={"filename": filename, "threshold": threshold},
                )
            ],
        )

    best_match = top_candidates[0]
    return CustomerMatchResult(
        ok=True,
        customer_id=best_match["customer_id"],
        score=best_match["score"],
        top_candidates=top_candidates,
    )

