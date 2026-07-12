const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require("playwright");

const BASE_URL = process.env.BROWSER_BASE_URL || "http://127.0.0.1:8000";
const OUT_DIR = process.env.BROWSER_EVIDENCE_DIR || path.join("docs", "browser-evidence");

const PNG_BYTES = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII=",
  "base64"
);

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

async function fillListing(page) {
  const form = page.locator("#listingForm");
  await form.locator('[name="title"]').fill("Browser E2E oak lamp");
  await form.locator('[name="price"]').fill("42.50");
  await form.locator('[name="condition"]').selectOption("good");
  await form.locator('[name="category"]').fill("Home and furniture");
  await form.locator('[name="location"]').fill("Utrecht");
  await form.locator('[name="tags"]').fill("lamp, oak, browser");
  await form.locator('[name="material"]').fill("oak");
  await form.locator('[name="description"]').fill(
    "Solid oak lamp tested through a full browser workflow. Pickup available by appointment."
  );
  await form.locator('[name="delivery_options"]').fill('{"pickup":true,"shipping":false}');
  await form.locator('[name="pickup_allowed"]').check();
  await form.locator('button[type="submit"]').click();
  await expectText(page, "#editorMessage", "Saved");
}

async function run() {
  fs.mkdirSync(OUT_DIR, { recursive: true });
  const browser = await chromium.launch();
  const context = await browser.newContext({ acceptDownloads: true, viewport: { width: 1366, height: 900 } });
  const page = await context.newPage();

  try {
    await page.goto(BASE_URL, { waitUntil: "domcontentloaded" });
    const stamp = Date.now();
    await page.locator("#authEmail").fill(`browser-e2e-${stamp}@example.com`);
    await page.locator("#authPassword").fill("correct-password");
    await page.locator("#authName").fill("Browser E2E");
    await page.locator("#registerButton").click();
    await page.locator("#shell").waitFor({ state: "visible", timeout: 10_000 });

    await page.locator("#newListingButton").click();
    await page.locator("#listingEditor").waitFor({ state: "visible", timeout: 10_000 });
    await fillListing(page);

    await page.locator("#imageInput").setInputFiles({
      name: "lamp.png",
      mimeType: "image/png",
      buffer: PNG_BYTES,
    });
    await expectText(page, "#imageList", "lamp.png");

    await page.locator('[data-platform="marktplaats"]').check();
    await page.locator("#validateButton").click();
    await expectText(page, "#prepublishReview", "Required fields are present.");
    await expectText(page, "#prepublishReview", "Copy package");

    await page.locator("#publishButton").click();
    await expectText(page, "#jobList", "needs_user_action");
    await page.locator("#jobList [data-job-id]").first().click();
    await page.locator("#manualPlatformUrl").fill("https://www.marktplaats.nl/v/huis-en-inrichting/lampen/browser-e2e");
    await page.locator("#manualPlatformListingId").fill("browser-e2e");
    await page.locator("#manualCompletionForm button[type='submit']").click();
    await expectText(page, "#jobList", "published");

    await page.getByRole("button", { name: "Settings" }).click();
    const downloadPromise = page.waitForEvent("download");
    await page.locator("#exportDataButton").click();
    const download = await downloadPromise;
    const downloadPath = path.join(OUT_DIR, "e2e-export.json");
    await download.saveAs(downloadPath);
    const exported = JSON.parse(fs.readFileSync(downloadPath, "utf-8"));

    await page.on("dialog", (dialog) => dialog.accept("DELETE"));
    await page.locator("#deleteMyDataButton").click();
    await page.locator("#authView").waitFor({ state: "visible", timeout: 10_000 });

    const screenshotPath = path.join(OUT_DIR, "e2e-final-auth.png");
    await page.screenshot({ path: screenshotPath, fullPage: true });

    const report = {
      generatedAt: new Date().toISOString(),
      baseUrl: BASE_URL,
      browser: "chromium",
      assertions: [
        "fresh user registration opens dashboard shell",
        "listing is created and saved through the real editor",
        "image upload appears in the editor",
        "selected platform validation shows prepublish copy controls",
        "assisted job is queued and manually completed",
        "JSON export downloads user data",
        "account deletion returns to the auth view",
      ],
      exportedListings: exported.listings?.length || 0,
      exportedTitle: exported.listings?.[0]?.title || "",
      screenshot: screenshotPath.replaceAll("\\", "/"),
      download: downloadPath.replaceAll("\\", "/"),
    };
    fs.writeFileSync(path.join(OUT_DIR, "e2e-workflow.json"), `${JSON.stringify(report, null, 2)}\n`);
    console.log(JSON.stringify(report, null, 2));
  } finally {
    await browser.close();
  }
}

run().catch((error) => {
  console.error(error);
  process.exit(1);
});
