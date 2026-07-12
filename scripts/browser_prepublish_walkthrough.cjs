const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require("playwright");

const BASE_URL = process.env.BROWSER_BASE_URL || "http://127.0.0.1:8000";
const OUT_DIR = process.env.BROWSER_EVIDENCE_DIR || path.join("docs", "browser-evidence");

const PNG_BYTES = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII=",
  "base64"
);

async function api(request, token, method, route, options = {}) {
  const response = await request.fetch(`${BASE_URL}/api${route}`, {
    method,
    headers: token ? { Authorization: `Bearer ${token}`, ...(options.headers || {}) } : options.headers,
    data: options.data,
    multipart: options.multipart,
  });
  if (!response.ok()) {
    throw new Error(`${method} ${route} failed: ${response.status()} ${await response.text()}`);
  }
  return response.status() === 204 ? null : response.json();
}

async function setupScenario(request) {
  const stamp = Date.now();
  const user = await api(request, null, "POST", "/auth/register", {
    data: {
      email: `browser-prepublish-${stamp}@example.com`,
      password: "correct-password",
      name: "Browser Prepublish",
    },
  });
  const token = user.token;

  await api(request, token, "POST", "/category-mappings", {
    data: {
      source_category: "Home and furniture",
      platform: "marktplaats",
      platform_category: "Huis en Inrichting",
    },
  });

  const listing = await api(request, token, "POST", "/listings", {
    data: {
      title: "Browser-tested oak side table",
      description:
        "Solid oak side table in good used condition with light surface wear. Pickup available by appointment.",
      price_cents: 4500,
      condition: "good",
      category: "Home and furniture",
      location: "Utrecht",
      delivery_options: { pickup: true, shipping: false },
      pickup_allowed: true,
      shipping_allowed: false,
      material: "oak",
      tags: ["furniture", "oak", "side table"],
    },
  });

  await api(request, token, "POST", `/listings/${listing.id}/images`, {
    multipart: {
      file: {
        name: "table.png",
        mimeType: "image/png",
        buffer: PNG_BYTES,
      },
    },
  });

  return { token, listingId: listing.id };
}

async function runViewport(browser, scenario, viewportName, viewport, screenshotName) {
  const context = await browser.newContext({ viewport });
  const page = await context.newPage();
  await page.goto(BASE_URL, { waitUntil: "domcontentloaded" });
  await page.evaluate((token) => localStorage.setItem("autoposterToken", token), scenario.token);
  await page.reload({ waitUntil: "networkidle" });

  await page.getByRole("button", { name: "Listings" }).click();
  await page.locator(`#listingList [data-listing-id="${scenario.listingId}"]`).click();
  await page.locator('[data-platform="marktplaats"]').check();
  await expectVisibleText(page, "#prepublishReview", "Prepublish review");
  await expectVisibleText(page, "#prepublishReview", "Run validation to build the copy-ready posting package.");
  await page.locator("#validateButton").click();
  await expectVisibleText(page, "#prepublishReview", "Required fields are present.");
  await expectVisibleText(page, "#prepublishReview", "Huis en Inrichting");
  await expectVisibleText(page, "#prepublishReview", "Copy package");

  const screenshotPath = path.join(OUT_DIR, screenshotName);
  await page.screenshot({ path: screenshotPath, fullPage: true });
  const result = {
    viewport: viewportName,
    width: viewport.width,
    height: viewport.height,
    screenshot: screenshotPath.replaceAll("\\", "/"),
    prepublishVisible: await page.locator("#prepublishReview").isVisible(),
    copyButtons: await page.locator("[data-copy-field]").count(),
    packageButtons: await page.locator("[data-copy-package]").count(),
  };
  await context.close();
  return result;
}

async function expectVisibleText(page, selector, text) {
  const locator = page.locator(selector);
  await locator.waitFor({ state: "visible", timeout: 10_000 });
  await page.waitForFunction(
    ({ selector: targetSelector, text: targetText }) => {
      const node = document.querySelector(targetSelector);
      return Boolean(node && node.innerText.includes(targetText));
    },
    { selector, text },
    { timeout: 10_000 }
  );
}

(async () => {
  fs.mkdirSync(OUT_DIR, { recursive: true });
  const browser = await chromium.launch();
  try {
    const request = await browser.newContext().then((context) => context.request);
    const scenario = await setupScenario(request);
    const results = [];
    results.push(await runViewport(browser, scenario, "desktop", { width: 1440, height: 1000 }, "prepublish-desktop.png"));
    results.push(await runViewport(browser, scenario, "mobile", { width: 390, height: 844 }, "prepublish-mobile.png"));

    const report = {
      generatedAt: new Date().toISOString(),
      baseUrl: BASE_URL,
      browser: "chromium",
      listingId: scenario.listingId,
      assertions: [
        "auth token accepted by dashboard shell",
        "listing can be opened from the real Listings view",
        "Marktplaats platform selection opens prepublish review",
        "validation populates ready state and mapped category",
        "copy-ready package and field controls are present",
        "desktop and mobile screenshots were captured",
      ],
      results,
    };
    fs.writeFileSync(path.join(OUT_DIR, "prepublish-walkthrough.json"), `${JSON.stringify(report, null, 2)}\n`);
    console.log(JSON.stringify(report, null, 2));
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
