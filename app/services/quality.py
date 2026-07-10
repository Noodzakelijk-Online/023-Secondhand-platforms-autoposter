from dataclasses import dataclass
from typing import Any

from app.models import Listing


@dataclass(frozen=True)
class QualityIssue:
    field: str
    severity: str
    message: str
    action: str


def analyze_listing_quality(listing: Listing) -> dict[str, Any]:
    issues: list[QualityIssue] = []
    suggestions: list[dict[str, Any]] = []

    title = (listing.title or "").strip()
    description = (listing.description or "").strip()
    category = (listing.category or "").strip()
    location = (listing.location or "").strip()

    if not title:
        issues.append(issue("title", "critical", "Title is missing.", "Add a clear item title."))
    elif len(title) < 12:
        issues.append(
            issue("title", "warning", "Title is very short.", "Include brand, item type, or distinguishing detail.")
        )
    elif title.isupper() and len(title) > 8:
        issues.append(
            issue("title", "tip", "Title is all caps.", "Use normal capitalization for a calmer marketplace listing.")
        )

    if not description:
        issues.append(
            issue("description", "critical", "Description is missing.", "Add buyer-facing details and condition notes.")
        )
    elif len(description) < 80:
        issues.append(
            issue(
                "description",
                "warning",
                "Description is short.",
                "Mention condition, included parts, pickup/shipping, and any visible wear.",
            )
        )
    elif len(description) > 3000:
        issues.append(issue("description", "tip", "Description is long.", "Trim repeated details before posting."))

    if listing.price_cents <= 0:
        issues.append(issue("price_cents", "critical", "Price is missing.", "Set a realistic asking price above zero."))
    if not category:
        issues.append(
            issue("category", "critical", "Category is missing.", "Choose a category or add category mappings.")
        )
    if not location:
        issues.append(
            issue("location", "critical", "Location is missing.", "Add the pickup or shipping origin location.")
        )
    if not listing.images:
        issues.append(issue("images", "critical", "No images are attached.", "Upload at least one clear item photo."))
    elif len(listing.images) == 1:
        issues.append(
            issue("images", "tip", "Only one image is attached.", "Add extra angles, labels, defects, or scale photos.")
        )

    if not listing.pickup_allowed and not listing.shipping_allowed:
        issues.append(
            issue(
                "delivery_options",
                "warning",
                "No delivery method is selected.",
                "Enable pickup, shipping, or describe the delivery arrangement.",
            )
        )
    if listing.shipping_allowed and listing.shipping_cost_cents <= 0:
        issues.append(
            issue(
                "shipping_cost_cents",
                "tip",
                "Shipping is enabled without a shipping cost.",
                "Add the shipping cost or mention that it is calculated separately.",
            )
        )
    if listing.shipping_allowed and not listing.weight_grams and not listing.dimensions:
        issues.append(
            issue(
                "dimensions",
                "tip",
                "Shipping details are thin.",
                "Add weight or dimensions so buyers can judge shipping fit.",
            )
        )

    if listing.condition in {"used", "fair", "damaged", "for_parts"} and not mentions_wear(description):
        issues.append(
            issue(
                "description",
                "warning",
                "Condition notes are not explicit.",
                "Mention visible wear, defects, repairs, or say there are no known issues.",
            )
        )

    suggested_title = build_title(listing)
    if suggested_title and suggested_title.casefold() != title.casefold():
        suggestions.append(
            {
                "field": "title",
                "value": suggested_title,
                "rationale": "Built from brand, model, color/material, and category fields.",
            }
        )

    suggested_description = build_description(listing)
    if suggested_description and len(description) < 160:
        suggestions.append(
            {
                "field": "description",
                "value": suggested_description,
                "rationale": "Structured buyer-facing draft from the current listing fields.",
            }
        )

    suggested_tags = build_tags(listing)
    if suggested_tags and set(tag.casefold() for tag in suggested_tags) != set(tag.casefold() for tag in listing.tags):
        suggestions.append(
            {
                "field": "tags",
                "value": suggested_tags,
                "rationale": "Search tags derived from item, brand, color, material, and category.",
            }
        )

    score = quality_score(issues)
    return {
        "score": score,
        "grade": grade_for_score(score),
        "summary": summary_for_score(score, issues),
        "issues": [item.__dict__ for item in issues],
        "suggestions": suggestions,
        "checklist": {
            "has_title": bool(title),
            "has_description": bool(description),
            "has_price": listing.price_cents > 0,
            "has_category": bool(category),
            "has_location": bool(location),
            "has_images": bool(listing.images),
            "has_delivery_method": bool(listing.pickup_allowed or listing.shipping_allowed),
        },
    }


def issue(field: str, severity: str, message: str, action: str) -> QualityIssue:
    return QualityIssue(field=field, severity=severity, message=message, action=action)


def quality_score(issues: list[QualityIssue]) -> int:
    penalties = {"critical": 15, "warning": 8, "tip": 3}
    return max(0, 100 - sum(penalties.get(item.severity, 3) for item in issues))


def grade_for_score(score: int) -> str:
    if score >= 85:
        return "ready"
    if score >= 70:
        return "good"
    if score >= 50:
        return "needs_work"
    return "blocked"


def summary_for_score(score: int, issues: list[QualityIssue]) -> str:
    critical = sum(1 for item in issues if item.severity == "critical")
    warnings = sum(1 for item in issues if item.severity == "warning")
    if critical:
        return f"Fix {critical} required item before publishing."
    if warnings:
        return f"Listing is usable, with {warnings} quality improvement to consider."
    if score < 100:
        return "Listing is ready; optional polish remains."
    return "Listing has the core details buyers expect."


def mentions_wear(description: str) -> bool:
    text = description.casefold()
    markers = [
        "wear",
        "scratch",
        "scratches",
        "dent",
        "defect",
        "damage",
        "used",
        "condition",
        "working",
        "tested",
        "no known issues",
        "as pictured",
    ]
    return any(marker in text for marker in markers)


def build_title(listing: Listing) -> str:
    parts = [listing.brand, listing.model, listing.color, listing.material, listing.category or listing.title]
    cleaned = []
    seen = set()
    for part in parts:
        value = (part or "").strip()
        if not value:
            continue
        key = value.casefold()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(value)
    return " ".join(cleaned)[:160]


def build_description(listing: Listing) -> str:
    lines = []
    title = (listing.title or build_title(listing) or "Item").strip()
    lines.append(f"{title} in {format_condition(listing.condition)} condition.")
    detail_parts = [listing.brand, listing.model, listing.color, listing.material]
    details = ", ".join(part.strip() for part in detail_parts if part and part.strip())
    if details:
        lines.append(f"Details: {details}.")
    if listing.notes:
        lines.append(str(listing.notes).strip())
    if listing.pickup_allowed and listing.shipping_allowed:
        lines.append("Available for pickup or shipping.")
    elif listing.pickup_allowed:
        lines.append("Available for pickup.")
    elif listing.shipping_allowed:
        lines.append("Shipping is available.")
    if listing.location:
        lines.append(f"Location: {listing.location}.")
    return "\n".join(lines)


def format_condition(condition: str) -> str:
    return (condition or "used").replace("_", " ")


def build_tags(listing: Listing) -> list[str]:
    raw_values = [
        *(listing.tags or []),
        listing.category,
        listing.brand,
        listing.model,
        listing.color,
        listing.material,
    ]
    tags = []
    seen = set()
    for raw_value in raw_values:
        value = str(raw_value or "").strip()
        if not value:
            continue
        for candidate in split_tag_value(value):
            key = candidate.casefold()
            if key not in seen and len(candidate) <= 40:
                seen.add(key)
                tags.append(candidate)
            if len(tags) >= 10:
                return tags
    return tags


def split_tag_value(value: str) -> list[str]:
    if "," in value:
        return [part.strip() for part in value.split(",") if part.strip()]
    return [value]
