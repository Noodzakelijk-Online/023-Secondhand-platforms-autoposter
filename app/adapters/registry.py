from app.adapters.assisted import (
    EbayAdapter,
    KooppleinAdapter,
    MarktplaatsAdapter,
    NextdoorAdapter,
    TweedehandsAdapter,
)

ADAPTERS = {
    adapter.key: adapter
    for adapter in [
        MarktplaatsAdapter(),
        KooppleinAdapter(),
        NextdoorAdapter(),
        EbayAdapter(),
        TweedehandsAdapter(),
    ]
}


def get_adapter(platform: str):
    try:
        return ADAPTERS[platform]
    except KeyError as exc:
        raise ValueError(f"Unsupported platform: {platform}") from exc


def list_platforms() -> list[dict]:
    return [
        {
            "key": adapter.key,
            "name": adapter.name,
            "automation_mode": adapter.automation_mode,
            "posting_url": adapter.posting_url,
            "required_fields": adapter.get_required_fields(),
            "supported_categories": adapter.get_supported_categories(),
            "capabilities": adapter.get_capabilities(),
            "compliance_notes": adapter.extra_warnings,
        }
        for adapter in ADAPTERS.values()
    ]
