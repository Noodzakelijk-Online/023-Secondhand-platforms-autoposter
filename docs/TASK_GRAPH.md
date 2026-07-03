# Task Graph

```mermaid
flowchart TD
  A["User account"] --> B["Master listing"]
  B --> C["Validated images"]
  C --> D["Platform selection"]
  D --> E["Readiness validation"]
  E --> F["Platform overrides/category mapping"]
  F --> G["Publishing job"]
  G --> H["Assisted package and logs"]
  H --> I["Human platform completion"]
  I --> J["Final URL confirmation"]
  J --> K["Publication history"]
```

## External Blockers

- Official API publishing requires provider credentials, OAuth/app approval, quota review, and platform-specific compliance work.
- Assisted workflows require the user to complete external login, CAPTCHA, payment, confirmation, and final submit steps.

