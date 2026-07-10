from pathlib import Path


def test_frontend_exposes_controlled_job_polling():
    html = Path("public/index.html").read_text(encoding="utf-8")
    script = Path("public/app.js").read_text(encoding="utf-8")

    required_html = [
        'id="jobPollingStatus"',
        'id="jobPollingToggle"',
        "Pause live refresh",
        "Resume live refresh",
    ]
    for fragment in required_html:
        assert fragment in html or fragment in script

    required_script = [
        "jobPolling",
        "refreshJobsOnly",
        "scheduleJobPolling",
        "renderJobPollingStatus",
        "setTimeout(refreshJobsOnly",
        "clearTimeout(state.jobPolling.timerId)",
        "$(\"#jobPollingToggle\").addEventListener",
    ]
    for fragment in required_script:
        assert fragment in script
