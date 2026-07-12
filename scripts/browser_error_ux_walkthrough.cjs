const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require("playwright");

const BASE_URL = process.env.BROWSER_BASE_URL || "http://127.0.0.1:8000";
const OUT_DIR = process.env.BROWSER_EVIDENCE_DIR || path.join("docs", "browser-evidence");

async function expectText(page, selector, text) {
  await page.locator(selector).waitFor({ state: "visible", timeout: 10_000 });
  await page.waitForFunction(
    ({ selector: targetSelector, text: targetText }) => {
      const node = document.querySelector(targetSelector);
      return Boolean(node && node.innerText.includes(targetText));
    },
    { selector, text },
    { timeout: 10_000 }
  );
}

async function run() {
  fs.mkdirSync(OUT_DIR, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1366, height: 900 } });
  try {
    await page.goto(BASE_URL, { waitUntil: "domcontentloaded" });

    await page.locator("#authEmail").fill("missing-user@example.com");
    await page.locator("#authPassword").fill("wrong-password");
    await page.locator("#authForm button[type='submit']").click();
    await expectText(page, "#authError", "Invalid email or password");

    const stamp = Date.now();
    await page.locator("#authEmail").fill(`browser-error-${stamp}@example.com`);
    await page.locator("#authPassword").fill("correct-password");
    await page.locator("#authName").fill("Browser Error UX");
    await page.locator("#registerButton").click();
    await page.locator("#shell").waitFor({ state: "visible", timeout: 10_000 });

    await page.locator("#newListingButton").click();
    await page.locator("#listingEditor").waitFor({ state: "visible", timeout: 10_000 });
    await page.locator('[data-platform="marktplaats"]').check();
    await page.locator("#validateButton").click();
    await expectText(page, "#prepublishReview", "Missing:");
    await expectText(page, "#prepublishReview", "Fix");
    const recoveryButtons = await page.locator("[data-focus-missing]").count();
    await page.locator("[data-focus-missing]").first().click();
    const focusedAfterRecovery = await page.evaluate(() => document.activeElement?.id || document.activeElement?.name || "");

    await page.locator("#publishButton").click();
    await page.locator("#jobList [data-job-id]").first().waitFor({ state: "visible", timeout: 10_000 });
    await page.locator("#jobList [data-job-id]").first().click();
    await expectText(page, "#jobDetails", "Retry after fixing the listing, platform account, or reported validation issue.");
    const retryGuidance = await page.locator(".retry-guidance").innerText();

    await page.getByRole("button", { name: "Settings" }).click();
    await page.locator("#importDataInput").setInputFiles({
      name: "broken.json",
      mimeType: "application/json",
      buffer: Buffer.from("{not-json"),
    });
    await expectText(page, "#dataPortabilityMessage", "Expected property name");
    const importError = await page.locator("#dataPortabilityMessage").innerText();

    const screenshotPath = path.join(OUT_DIR, "error-ux.png");
    await page.screenshot({ path: screenshotPath, fullPage: true });

    const report = {
      generatedAt: new Date().toISOString(),
      baseUrl: BASE_URL,
      browser: "chromium",
      assertions: [
        "invalid login shows inline auth error",
        "validation missing fields render recovery actions",
        "recovery action focuses a repair target",
        "failed job details show retry guidance",
        "invalid JSON import shows a visible import error",
      ],
      recoveryButtons,
      focusedAfterRecovery,
      retryGuidance,
      importError,
      screenshot: screenshotPath.replaceAll("\\", "/"),
    };
    fs.writeFileSync(path.join(OUT_DIR, "error-ux-walkthrough.json"), `${JSON.stringify(report, null, 2)}\n`);
    console.log(JSON.stringify(report, null, 2));
  } finally {
    await browser.close();
  }
}

run().catch((error) => {
  console.error(error);
  process.exit(1);
});
