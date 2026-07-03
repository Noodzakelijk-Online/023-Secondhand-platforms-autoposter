# Legacy Script Quarantine

The repository still contains pre-existing Selenium/browser automation scripts. They are not imported by the FastAPI app, not run at startup, and not required by `requirements.txt`.

Optional dependencies for these scripts live in `requirements-legacy.txt`.

## Rules

- Do not run legacy scripts in production app startup.
- Do not commit real credentials, LastPass secrets, cookies, browser profiles, scraped data, or downloaded images.
- Do not bypass CAPTCHAs, anti-bot controls, login protections, SMS prompts, payment prompts, or platform security systems.
- Run only in a user-controlled local browser session when platform terms and account permissions allow it.
- Prefer official APIs for future production automation.

## Root Legacy Files

| File | Purpose | Risk | Current Status |
| --- | --- | --- | --- |
| `main.py` | Old orchestrator for scraping Tweedehands and posting elsewhere through Selenium/LastPass. | High: credentials, browser automation, platform controls. | Legacy reference only. Not used by web app. |
| `scrape_second_hand.py` | Old Tweedehands scraping flow. | High: authenticated scraping and local CSV/images. | Legacy reference only. |
| `markplaats.py` | Old Marktplaats Selenium login/posting helper. | High: login, cookies, 2FA, paid/free placement choices. | Legacy reference only. Current app uses assisted adapter. |
| `post_koopplein.py` | Old Koopplein Selenium posting helper. | Medium/high: account login and posting. | Legacy reference only. Current app uses assisted adapter. |
| `post_nextdoor.py` | Old Nextdoor Selenium posting helper. | High: neighborhood/account controls and anti-abuse flows. | Legacy reference only. Current app uses assisted adapter. |
| `post_ebay.py` | Old eBay Selenium posting helper. | High: CAPTCHA, SMS, marketplace policy, paid/shipping setup. | Legacy reference only. Current app uses assisted adapter. |
| `nlp_hanlder.py` | Old spaCy category matching helper. | Low runtime risk, but has a typo in filename and requires heavy model dependency. | Legacy reference only. |
| `test.py` | Old standalone spaCy test script. | Low, but not part of app tests. | Legacy reference only. |
| `setup.sh`, `start.desktop`, `stop.desktop`, `stop.sh`, `main.spec` | Old packaging/startup helpers. | Medium: unclear relation to new app. | Needs future cleanup or replacement. |

## Duplicate Nested Folder

The folder `023-Secondhand-platforms-autoposter-main/` appears to be a duplicate copy of the old repository source. It is not used by the FastAPI app. Future cleanup should either move it under `legacy/archive/` or remove it after confirming no unique code remains.

## Future Quarantine Work

1. Move legacy runtime scripts into `legacy/selenium/`.
2. Add a root-level compatibility note for users who still expect the old scripts.
3. Remove the duplicate nested source folder after comparison.
4. Add tests proving `app.main` does not import Selenium, LastPass, spaCy, or legacy modules.
