const fs = require("node:fs");
const path = require("node:path");
const { chromium, firefox, webkit } = require("playwright");

const BASE_URL = process.env.BROWSER_BASE_URL || "http://127.0.0.1:8000";
const OUT_DIR = process.env.BROWSER_EVIDENCE_DIR || path.join("docs", "browser-evidence", "responsive");

const BROWSERS = { chromium, firefox, webkit };
const VIEWPORTS = [
  { name: "mobile", width: 390, height: 844 },
  { name: "tablet", width: 768, height: 1024 },
  { name: "laptop", width: 1366, height: 768 },
  { name: "desktop", width: 1920, height: 1080 },
];

async function api(method, route, options = {}) {
  const response = await fetch(`${BASE_URL}/api${route}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(options.token ? { Authorization: `Bearer ${options.token}` } : {}),
    },
    body: options.data ? JSON.stringify(options.data) : undefined,
  });
  if (!response.ok) {
    throw new Error(`${method} ${route} failed: ${response.status} ${await response.text()}`);
  }
  return response.status === 204 ? null : response.json();
}

async function setupScenario() {
  const stamp = Date.now();
  const user = await api("POST", "/auth/register", {
    data: {
      email: `responsive-${stamp}@example.com`,
      password: "correct-password",
      name: "Responsive Matrix",
    },
  });
  const token = user.token;
  await api("POST", "/listings", {
    token,
    data: {
      title: "Responsive matrix listing",
      description: "Listing used for responsive and browser compatibility evidence.",
      price_cents: 2500,
      condition: "good",
      category: "Home and furniture",
      location: "Utrecht",
      delivery_options: { pickup: true, shipping: false },
      pickup_allowed: true,
      tags: ["responsive", "browser"],
    },
  });
  return { token };
}

async function assertNoHorizontalOverflow(page) {
  const metrics = await page.evaluate(() => ({
    innerWidth: window.innerWidth,
    documentWidth: document.documentElement.scrollWidth,
    bodyWidth: document.body.scrollWidth,
  }));
  const maxWidth = Math.max(metrics.documentWidth, metrics.bodyWidth);
  if (maxWidth > metrics.innerWidth + 2) {
    throw new Error(`Horizontal overflow: ${maxWidth}px content in ${metrics.innerWidth}px viewport`);
  }
  return metrics;
}

async function assertView(page, viewName) {
  await page.getByRole("button", { name: new RegExp(`^${viewName}$`, "i") }).click();
  const viewId = `${viewName.toLowerCase()}View`;
  await page.locator(`#${viewId}.active`).waitFor({ state: "visible", timeout: 10_000 });
  return assertNoHorizontalOverflow(page);
}

async function runCase(browserName, browserType, viewport, token) {
  const browser = await browserType.launch();
  const context = await browser.newContext({ viewport });
  const page = await context.newPage();
  try {
    await page.goto(BASE_URL, { waitUntil: "domcontentloaded" });
    await page.evaluate((value) => localStorage.setItem("autoposterToken", value), token);
    await page.reload({ waitUntil: "networkidle" });
    await page.locator("#shell").waitFor({ state: "visible", timeout: 10_000 });

    const viewMetrics = {};
    for (const viewName of ["Dashboard", "Listings", "Queue", "Accounts", "Settings"]) {
      viewMetrics[viewName.toLowerCase()] = await assertView(page, viewName);
    }

    const screenshot = path.join(OUT_DIR, `${browserName}-${viewport.name}.png`);
    await page.screenshot({ path: screenshot, fullPage: true });
    return {
      browser: browserName,
      viewport: viewport.name,
      width: viewport.width,
      height: viewport.height,
      screenshot: screenshot.replaceAll("\\", "/"),
      viewMetrics,
    };
  } finally {
    await context.close();
    await browser.close();
  }
}

(async () => {
  fs.mkdirSync(OUT_DIR, { recursive: true });
  const scenario = await setupScenario();
  const results = [];
  for (const [browserName, browserType] of Object.entries(BROWSERS)) {
    for (const viewport of VIEWPORTS) {
      results.push(await runCase(browserName, browserType, viewport, scenario.token));
    }
  }
  const report = {
    generatedAt: new Date().toISOString(),
    baseUrl: BASE_URL,
    browsers: Object.keys(BROWSERS),
    viewports: VIEWPORTS.map(({ name, width, height }) => ({ name, width, height })),
    assertions: [
      "authenticated shell renders",
      "dashboard/listings/queue/accounts/settings views activate",
      "document and body width stay within viewport width",
      "screenshots captured for each browser and viewport",
    ],
    results,
  };
  const reportPath = path.join("docs", "browser-evidence", "responsive-matrix.json");
  fs.writeFileSync(reportPath, `${JSON.stringify(report, null, 2)}\n`);
  console.log(JSON.stringify(report, null, 2));
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
