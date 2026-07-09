const state = {
  token: localStorage.getItem("autoposterToken"),
  user: null,
  platforms: [],
  listings: [],
  jobs: [],
  accounts: [],
  templates: [],
  categoryMappings: [],
  validationResults: {},
  selectedListingId: null,
  selectedPlatforms: new Set(),
  listingQuery: {
    search: "",
    status: "",
    sort: "-updated_at",
    limit: 10,
    offset: 0,
    total: 0,
  },
  jobQuery: {
    platform: "",
    status: "",
    sort: "-created_at",
    limit: 10,
    offset: 0,
    total: 0,
  },
  pendingRequests: 0,
};

const $ = (selector) => document.querySelector(selector);
const money = (cents) => (cents / 100).toLocaleString(undefined, { style: "currency", currency: "EUR" });
let listingSearchTimer = null;

function setBusy(delta) {
  state.pendingRequests = Math.max(0, state.pendingRequests + delta);
  document.body.classList.toggle("busy", state.pendingRequests > 0);
}

function showAppMessage(message, tone = "error") {
  const node = $("#appMessage");
  if (!node) return;
  node.textContent = message || "Something went wrong";
  node.className = `app-message ${tone}`;
}

function clearAppMessage() {
  const node = $("#appMessage");
  if (!node) return;
  node.textContent = "";
  node.className = "app-message hidden";
}

async function api(path, options = {}) {
  const { data } = await apiWithMeta(path, options);
  return data;
}

async function apiWithMeta(path, options = {}) {
  const headers = options.headers || {};
  if (!(options.body instanceof FormData)) headers["Content-Type"] = "application/json";
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  setBusy(1);
  try {
    const response = await fetch(`/api${path}`, { ...options, headers });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.error?.message || error.detail || "Request failed");
    }
    const data = response.status === 204 ? null : await response.json();
    return { data, headers: response.headers };
  } catch (error) {
    if (error instanceof Error) throw error;
    throw new Error("Network request failed");
  } finally {
    setBusy(-1);
  }
}

function listingQueryPath() {
  const params = new URLSearchParams({
    limit: String(state.listingQuery.limit),
    offset: String(state.listingQuery.offset),
    sort: state.listingQuery.sort,
  });
  if (state.listingQuery.search.trim()) params.set("search", state.listingQuery.search.trim());
  if (state.listingQuery.status) params.set("status", state.listingQuery.status);
  return `/listings?${params.toString()}`;
}

function jobQueryPath() {
  const params = new URLSearchParams({
    limit: String(state.jobQuery.limit),
    offset: String(state.jobQuery.offset),
    sort: state.jobQuery.sort,
  });
  if (state.jobQuery.platform) params.set("platform", state.jobQuery.platform);
  if (state.jobQuery.status) params.set("status", state.jobQuery.status);
  return `/jobs?${params.toString()}`;
}

function show(view) {
  clearAppMessage();
  document.querySelectorAll(".view").forEach((node) => node.classList.remove("active"));
  document.querySelectorAll(".nav").forEach((node) => node.classList.toggle("active", node.dataset.view === view));
  $(`#${view}View`).classList.add("active");
  $("#viewTitle").textContent = view[0].toUpperCase() + view.slice(1);
}

function statusClass(status) {
  return `status ${status || ""}`;
}

function selectedListing() {
  return state.listings.find((listing) => listing.id === state.selectedListingId) || null;
}

function platformByKey(key) {
  return state.platforms.find((platform) => platform.key === key) || { key, name: key, compliance_notes: [] };
}

async function loadAll() {
  const [platforms, listingResult, jobResult, accounts, templates, categoryMappings] = await Promise.all([
    api("/platforms"),
    apiWithMeta(listingQueryPath()),
    apiWithMeta(jobQueryPath()),
    api("/accounts"),
    api("/templates"),
    api("/category-mappings"),
  ]);
  state.platforms = platforms;
  state.listings = listingResult.data;
  state.listingQuery.total = Number(listingResult.headers.get("X-Total-Count") || state.listings.length);
  state.jobs = jobResult.data;
  state.jobQuery.total = Number(jobResult.headers.get("X-Total-Count") || state.jobs.length);
  state.accounts = accounts;
  state.templates = templates;
  state.categoryMappings = categoryMappings;
  if (state.selectedListingId && !state.listings.some((listing) => listing.id === state.selectedListingId)) {
    state.selectedListingId = null;
    state.validationResults = {};
  }
  if (!state.selectedListingId && state.listings.length) state.selectedListingId = state.listings[0].id;
  render();
}

function render() {
  renderDashboard();
  renderListings();
  renderJobs();
  renderAccounts();
  renderSettings();
}

function renderDashboard() {
  $("#metricListings").textContent = state.listings.length;
  $("#metricReady").textContent = state.listings.filter((l) => l.platform_mappings.some((m) => m.status === "draft")).length;
  $("#metricAction").textContent = state.jobs.filter((j) => j.status === "needs_user_action").length;
  $("#metricFailed").textContent = state.jobs.filter((j) => j.status === "failed").length;
  $("#recentListings").innerHTML = state.listings.slice(0, 5).map(listingItemHtml).join("") || `<p class="muted">No listings yet.</p>`;
  $("#latestJobs").innerHTML = state.jobs.slice(0, 5).map(jobItemHtml).join("") || `<p class="muted">No jobs yet.</p>`;
}

function listingItemHtml(listing) {
  return `
    <article class="list-item ${listing.id === state.selectedListingId ? "selected" : ""}" data-listing-id="${listing.id}">
      <strong>${escapeHtml(listing.title || "Untitled listing")}</strong>
      <span class="muted">${escapeHtml(listing.category || "No category")} · ${money(listing.price_cents || 0)}</span>
      <span class="${statusClass(listing.status)}">${escapeHtml(listing.status)}</span>
    </article>
  `;
}

function jobItemHtml(job) {
  return `
    <article class="list-item" data-job-id="${job.id}">
      <div class="pane-head">
        <strong>${escapeHtml(job.platform)}</strong>
        <span class="${statusClass(job.status)}">${escapeHtml(job.status)}</span>
      </div>
      <span class="muted">Listing #${job.listing_id} · Attempt ${job.attempts}/${job.max_attempts}</span>
    </article>
  `;
}

function renderListings() {
  $("#listingSearch").value = state.listingQuery.search;
  $("#listingStatusFilter").value = state.listingQuery.status;
  $("#listingSort").value = state.listingQuery.sort;
  const start = state.listingQuery.total ? state.listingQuery.offset + 1 : 0;
  const end = Math.min(state.listingQuery.offset + state.listingQuery.limit, state.listingQuery.total);
  $("#listingPageInfo").textContent = `${start}-${end} of ${state.listingQuery.total}`;
  $("#listingPrevPage").disabled = state.listingQuery.offset === 0;
  $("#listingNextPage").disabled = state.listingQuery.offset + state.listingQuery.limit >= state.listingQuery.total;
  $("#listingList").innerHTML = state.listings.map(listingItemHtml).join("") || `<p class="muted">No listings yet.</p>`;
  const listing = selectedListing();
  $("#listingEditor").classList.toggle("hidden", !listing);
  if (!listing) return;
  const form = $("#listingForm");
  form.title.value = listing.title || "";
  form.price.value = ((listing.price_cents || 0) / 100).toFixed(2);
  form.condition.value = listing.condition || "used";
  form.category.value = listing.category || "";
  form.location.value = listing.location || "";
  form.brand.value = listing.brand || "";
  form.model.value = listing.model || "";
  form.color.value = listing.color || "";
  form.material.value = listing.material || "";
  form.weight_grams.value = listing.weight_grams || 0;
  form.shipping_cost.value = ((listing.shipping_cost_cents || 0) / 100).toFixed(2);
  form.pickup_allowed.checked = Boolean(listing.pickup_allowed);
  form.shipping_allowed.checked = Boolean(listing.shipping_allowed);
  form.tags.value = (listing.tags || []).join(", ");
  form.description.value = listing.description || "";
  form.delivery_options.value = JSON.stringify(listing.delivery_options || {}, null, 2);
  form.dimensions.value = JSON.stringify(listing.dimensions || {}, null, 2);
  form.notes.value = listing.notes || "";
  form.internal_notes.value = listing.internal_notes || "";
  $("#listingRevision").textContent = `Revision ${listing.revision || 1}`;
  renderListingTemplateOptions();
  renderImages(listing);
  renderPlatforms(listing);
}

function renderListingTemplateOptions() {
  const options = state.templates.map((template) => {
    const platform = template.platform ? ` (${template.platform})` : "";
    return `<option value="${template.id}">${escapeHtml(template.name)}${escapeHtml(platform)}</option>`;
  }).join("");
  $("#listingTemplateSelect").innerHTML = `<option value="">Choose template</option>${options}`;
}

function renderImages(listing) {
  const images = listing.images || [];
  $("#imageList").innerHTML = images.map((image, index) => `
    <article class="image-tile">
      <img src="/uploads/${listing.id}/${image.storage_path.split(/[\\\\/]/).pop()}" alt="${escapeHtml(image.filename)}" />
      <strong>${escapeHtml(image.filename)}</strong>
      <div class="image-actions">
        <button class="ghost" data-move-image="${image.id}" data-direction="-1" ${index === 0 ? "disabled" : ""}>Up</button>
        <button class="ghost" data-move-image="${image.id}" data-direction="1" ${index === images.length - 1 ? "disabled" : ""}>Down</button>
        <button class="ghost" data-delete-image="${image.id}">Delete</button>
      </div>
    </article>
  `).join("") || `<p class="muted">No images uploaded.</p>`;
}

function renderPlatforms(listing) {
  const mappings = new Map((listing.platform_mappings || []).map((mapping) => [mapping.platform, mapping]));
  state.selectedPlatforms = new Set([...mappings.values()].filter((m) => m.status !== "skipped").map((m) => m.platform));
  $("#platformList").innerHTML = state.platforms.map((platform) => {
    const mapping = mappings.get(platform.key);
    const checked = state.selectedPlatforms.has(platform.key) ? "checked" : "";
    const override = mapping?.overrides?.description || "";
    const errors = mapping?.validation_errors?.length ? `Missing: ${mapping.validation_errors.join(", ")}` : "Ready for validation";
    return `
      <article class="platform-card">
        <label><input type="checkbox" data-platform="${platform.key}" ${checked} /> ${escapeHtml(platform.name)}</label>
        <span class="${statusClass(mapping?.status || "draft")}">${escapeHtml(mapping?.status || platform.automation_mode)}</span>
        <textarea data-platform-description="${platform.key}" placeholder="Platform description variant">${escapeHtml(override)}</textarea>
        <small class="muted">${escapeHtml(errors)}</small>
      </article>
    `;
  }).join("");
  renderPrepublishReview(listing);
}

function renderPrepublishReview(listing) {
  const selectedKeys = state.platforms
    .map((platform) => platform.key)
    .filter((platformKey) => state.selectedPlatforms.has(platformKey));
  const review = $("#prepublishReview");
  if (!selectedKeys.length) {
    review.classList.add("hidden");
    review.innerHTML = "";
    return;
  }

  review.classList.remove("hidden");
  review.innerHTML = `
    <div class="pane-head">
      <h3>Prepublish review</h3>
      <span class="muted">Listing #${listing.id} - revision ${listing.revision || 1}</span>
    </div>
    <div class="review-grid">
      ${selectedKeys.map((platformKey) => reviewCardHtml(platformKey)).join("")}
    </div>
  `;
}

function reviewCardHtml(platformKey) {
  const platform = platformByKey(platformKey);
  const validation = state.validationResults[platformKey];
  const notes = platform.compliance_notes || [];
  if (!validation) {
    return `
      <article class="review-card">
        <div class="pane-head">
          <strong>${escapeHtml(platform.name)}</strong>
          <span class="status">not checked</span>
        </div>
        <p class="muted">Run validation to build the copy-ready posting package.</p>
        ${platform.posting_url ? `<a href="${escapeHtml(platform.posting_url)}" target="_blank" rel="noreferrer">Open platform</a>` : ""}
        ${notes.length ? `<ul class="review-notes">${notes.map((note) => `<li>${escapeHtml(note)}</li>`).join("")}</ul>` : ""}
      </article>
    `;
  }

  const fields = Object.entries(validation.mapped_fields || {});
  const missing = validation.missing_fields || [];
  const warnings = validation.warnings || [];
  return `
    <article class="review-card">
      <div class="pane-head">
        <strong>${escapeHtml(platform.name)}</strong>
        <span class="${statusClass(validation.ready ? "ready" : "needs_user_action")}">${validation.ready ? "ready" : "needs action"}</span>
      </div>
      ${platform.posting_url ? `<a href="${escapeHtml(platform.posting_url)}" target="_blank" rel="noreferrer">Open platform</a>` : ""}
      ${missing.length ? `
        <p class="review-alert">Missing: ${escapeHtml(missing.join(", "))}</p>
        <div class="recovery-list">
          ${missing.map((field) => missingFieldRecoveryHtml(field)).join("")}
        </div>
      ` : `<p class="muted">Required fields are present.</p>`}
      ${warnings.length ? `<ul class="review-notes">${warnings.map((warning) => `<li>${escapeHtml(warning)}</li>`).join("")}</ul>` : ""}
      ${notes.length ? `<ul class="review-notes">${notes.map((note) => `<li>${escapeHtml(note)}</li>`).join("")}</ul>` : ""}
      <div class="review-actions">
        <button type="button" class="ghost" data-copy-package="${platformKey}">Copy package</button>
      </div>
      <div class="field-list">
        ${fields.map(([field, value]) => `
          <div class="field-row">
            <div>
              <strong>${escapeHtml(formatFieldLabel(field))}</strong>
              <span>${escapeHtml(formatFieldValue(value))}</span>
            </div>
            <button type="button" class="ghost" data-copy-field="${platformKey}" data-copy-name="${escapeHtml(field)}">Copy</button>
          </div>
        `).join("") || `<p class="muted">No mapped fields returned.</p>`}
      </div>
    </article>
  `;
}

function formatFieldLabel(value) {
  return String(value).replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function formatFieldValue(value) {
  if (value === null || value === undefined || value === "") return "";
  if (Array.isArray(value)) return value.join(", ");
  if (typeof value === "object") return JSON.stringify(value, null, 2);
  return String(value);
}

function missingFieldRecoveryHtml(field) {
  return `
    <div class="recovery-row">
      <span>${escapeHtml(missingFieldHint(field))}</span>
      <button type="button" class="ghost" data-focus-missing="${escapeHtml(field)}">Fix</button>
    </div>
  `;
}

function missingFieldHint(field) {
  const hints = {
    title: "Add a title that identifies the item clearly.",
    description: "Add the buyer-facing description.",
    price_cents: "Set a price above zero.",
    condition: "Choose the item condition.",
    category: "Choose the source category or add a platform mapping.",
    location: "Add the pickup or shipping location.",
    delivery_options: "Fill delivery options or pickup/shipping flags.",
    images: "Upload at least one item image.",
  };
  return hints[field] || `Review ${formatFieldLabel(field)}.`;
}

function focusRecoveryTarget(field) {
  const fieldMap = {
    price_cents: "price",
    images: "imageInput",
  };
  if (field === "images") {
    $("#imageInput")?.focus();
    return;
  }
  const targetName = fieldMap[field] || field;
  const target = document.querySelector(`#listingForm [name="${targetName}"]`);
  if (!target) return;
  target.focus();
  target.scrollIntoView({ block: "center", behavior: "smooth" });
}

function packageText(platformKey) {
  const platform = platformByKey(platformKey);
  const validation = state.validationResults[platformKey];
  if (!validation) return "";
  const lines = [
    platform.name,
    platform.posting_url ? `Posting URL: ${platform.posting_url}` : "",
    `Ready: ${validation.ready ? "yes" : "no"}`,
    (validation.missing_fields || []).length ? `Missing: ${validation.missing_fields.join(", ")}` : "",
    "",
    ...Object.entries(validation.mapped_fields || {}).map(
      ([field, value]) => `${formatFieldLabel(field)}: ${formatFieldValue(value)}`
    ),
  ];
  return lines.filter((line, index) => line || index > 3).join("\n").trim();
}

async function copyText(text) {
  if (!text) return;
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return;
  }
  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "");
  textarea.style.position = "fixed";
  textarea.style.opacity = "0";
  document.body.appendChild(textarea);
  textarea.select();
  document.execCommand("copy");
  textarea.remove();
}

function renderJobs() {
  const platformOptions = state.platforms.map((platform) => `<option value="${platform.key}">${escapeHtml(platform.name)}</option>`).join("");
  $("#jobPlatformFilter").innerHTML = `<option value="">All platforms</option>${platformOptions}`;
  $("#jobPlatformFilter").value = state.jobQuery.platform;
  $("#jobStatusFilter").value = state.jobQuery.status;
  $("#jobSort").value = state.jobQuery.sort;
  const start = state.jobQuery.total ? state.jobQuery.offset + 1 : 0;
  const end = Math.min(state.jobQuery.offset + state.jobQuery.limit, state.jobQuery.total);
  $("#jobPageInfo").textContent = `${start}-${end} of ${state.jobQuery.total}`;
  $("#jobPrevPage").disabled = state.jobQuery.offset === 0;
  $("#jobNextPage").disabled = state.jobQuery.offset + state.jobQuery.limit >= state.jobQuery.total;
  $("#jobList").innerHTML = state.jobs.map(jobItemHtml).join("") || `<p class="muted">No publishing jobs.</p>`;
}

function renderAccounts() {
  const platformOptions = state.platforms.map((platform) => `<option value="${platform.key}">${escapeHtml(platform.name)}</option>`).join("");
  $("#accountPlatform").innerHTML = platformOptions;
  $("#templatePlatform").innerHTML = `<option value="">All platforms</option>${platformOptions}`;
  $("#mappingPlatform").innerHTML = platformOptions;
  $("#accountList").innerHTML = state.accounts.map((account) => `
    <article class="list-item">
      <div class="pane-head">
        <strong>${escapeHtml(account.display_name)}</strong>
        <button class="ghost" data-delete-account="${account.id}">Delete</button>
      </div>
      <span class="muted">${escapeHtml(account.platform)} · ${escapeHtml(account.mode)}</span>
      <span class="${statusClass(account.status)}">${escapeHtml(account.status)}</span>
    </article>
  `).join("") || `<p class="muted">No platform accounts.</p>`;
}

function renderSettings() {
  $("#templateList").innerHTML = state.templates.map((template) => `
    <article class="list-item">
      <div class="pane-head">
        <strong>${escapeHtml(template.name)}</strong>
        <div class="row compact-actions">
          <button class="ghost" data-edit-template="${template.id}">Edit</button>
          <button class="ghost" data-delete-template="${template.id}">Delete</button>
        </div>
      </div>
      <span class="muted">${escapeHtml(template.platform || "All platforms")}</span>
      <p>${escapeHtml(template.body.slice(0, 160))}</p>
    </article>
  `).join("") || `<p class="muted">No templates saved.</p>`;
  $("#categoryMappingList").innerHTML = state.categoryMappings.map((mapping) => `
    <article class="list-item">
      <div class="pane-head">
        <strong>${escapeHtml(mapping.source_category)}</strong>
        <div class="row compact-actions">
          <button class="ghost" data-edit-category-mapping="${mapping.id}">Edit</button>
          <button class="ghost" data-delete-category-mapping="${mapping.id}">Delete</button>
        </div>
      </div>
      <span class="muted">${escapeHtml(mapping.platform)} -> ${escapeHtml(mapping.platform_category)}</span>
    </article>
  `).join("") || `<p class="muted">No category mappings saved.</p>`;
}

function renderDiagnostics(result) {
  const checks = result.doctor?.checks || [];
  $("#diagnosticsOutput").classList.remove("muted");
  $("#diagnosticsOutput").innerHTML = `
    <div class="pane-head">
      <strong>Status: ${escapeHtml(result.status)}</strong>
      <span class="${statusClass(result.status)}">${escapeHtml(result.doctor?.status || result.status)}</span>
    </div>
    <p class="muted">${Number(result.listings || 0)} listings · ${Number(result.jobs || 0)} jobs · ${(result.platforms || []).length} platforms</p>
    <div class="diagnostic-checks">
      ${checks.map((check) => `
        <article class="diagnostic-check">
          <div class="pane-head">
            <strong>${escapeHtml(check.name)}</strong>
            <span class="${statusClass(check.status)}">${escapeHtml(check.status)}</span>
          </div>
          <p>${escapeHtml(check.message)}</p>
        </article>
      `).join("")}
    </div>
  `;
}

function parseDeliveryOptions(value) {
  if (!value.trim()) return {};
  try {
    return JSON.parse(value);
  } catch {
    return { note: value };
  }
}

async function savePlatformOverrides() {
  const listing = selectedListing();
  if (!listing) return;
  const cards = document.querySelectorAll("[data-platform]");
  for (const checkbox of cards) {
    const platform = checkbox.dataset.platform;
    const description = document.querySelector(`[data-platform-description="${platform}"]`)?.value || "";
    await api(`/listings/${listing.id}/platforms`, {
      method: "POST",
      body: JSON.stringify({
        platform,
        selected: checkbox.checked,
        overrides: description ? { description } : {},
      }),
    });
  }
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  })[char]);
}

window.addEventListener("unhandledrejection", (event) => {
  event.preventDefault();
  showAppMessage(event.reason?.message || "Something went wrong");
});

async function boot() {
  try {
    const health = await api("/health", { headers: {} });
    $("#healthBadge").textContent = health.status;
  } catch {
    $("#healthBadge").textContent = "Offline";
  }

  if (!state.token) return;
  try {
    state.user = await api("/auth/me");
    $("#userEmail").textContent = state.user.email;
    $("#authView").classList.add("hidden");
    $("#shell").classList.remove("hidden");
  } catch {
    localStorage.removeItem("autoposterToken");
    state.token = null;
    return;
  }

  try {
    await loadAll();
  } catch (error) {
    showAppMessage(error.message);
  }
}

$("#authForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  $("#authError").textContent = "";
  try {
    const payload = {
      email: $("#authEmail").value,
      password: $("#authPassword").value,
      name: $("#authName").value,
    };
    const data = await api("/auth/login", { method: "POST", body: JSON.stringify(payload) });
    state.token = data.token;
    localStorage.setItem("autoposterToken", data.token);
    await boot();
  } catch (error) {
    $("#authError").textContent = error.message;
  }
});

$("#registerButton").addEventListener("click", async () => {
  $("#authError").textContent = "";
  try {
    const data = await api("/auth/register", {
      method: "POST",
      body: JSON.stringify({
        email: $("#authEmail").value,
        password: $("#authPassword").value,
        name: $("#authName").value,
      }),
    });
    state.token = data.token;
    localStorage.setItem("autoposterToken", data.token);
    await boot();
  } catch (error) {
    $("#authError").textContent = error.message;
  }
});

$("#logoutButton").addEventListener("click", () => {
  api("/auth/logout", { method: "POST" }).finally(() => {
    localStorage.removeItem("autoposterToken");
    window.location.reload();
  });
});

document.querySelectorAll(".nav").forEach((node) => node.addEventListener("click", () => show(node.dataset.view)));

$("#newListingButton").addEventListener("click", async () => {
  const listing = await api("/listings", {
    method: "POST",
    body: JSON.stringify({ title: "Untitled listing", status: "draft" }),
  });
  state.selectedListingId = listing.id;
  state.listingQuery.search = "";
  state.listingQuery.status = "";
  state.listingQuery.sort = "-updated_at";
  state.listingQuery.offset = 0;
  show("listings");
  await loadAll();
});

$("#refreshButton").addEventListener("click", loadAll);

$("#refreshJobsButton").addEventListener("click", loadAll);

$("#listingSearch").addEventListener("input", (event) => {
  clearTimeout(listingSearchTimer);
  listingSearchTimer = setTimeout(async () => {
    state.listingQuery.search = event.target.value;
    state.listingQuery.offset = 0;
    await loadAll();
  }, 250);
});

$("#listingStatusFilter").addEventListener("change", async (event) => {
  state.listingQuery.status = event.target.value;
  state.listingQuery.offset = 0;
  await loadAll();
});

$("#listingSort").addEventListener("change", async (event) => {
  state.listingQuery.sort = event.target.value;
  state.listingQuery.offset = 0;
  await loadAll();
});

$("#listingPrevPage").addEventListener("click", async () => {
  state.listingQuery.offset = Math.max(0, state.listingQuery.offset - state.listingQuery.limit);
  await loadAll();
});

$("#listingNextPage").addEventListener("click", async () => {
  const nextOffset = state.listingQuery.offset + state.listingQuery.limit;
  if (nextOffset >= state.listingQuery.total) return;
  state.listingQuery.offset = nextOffset;
  await loadAll();
});

$("#jobPlatformFilter").addEventListener("change", async (event) => {
  state.jobQuery.platform = event.target.value;
  state.jobQuery.offset = 0;
  await loadAll();
});

$("#jobStatusFilter").addEventListener("change", async (event) => {
  state.jobQuery.status = event.target.value;
  state.jobQuery.offset = 0;
  await loadAll();
});

$("#jobSort").addEventListener("change", async (event) => {
  state.jobQuery.sort = event.target.value;
  state.jobQuery.offset = 0;
  await loadAll();
});

$("#jobPrevPage").addEventListener("click", async () => {
  state.jobQuery.offset = Math.max(0, state.jobQuery.offset - state.jobQuery.limit);
  await loadAll();
});

$("#jobNextPage").addEventListener("click", async () => {
  const nextOffset = state.jobQuery.offset + state.jobQuery.limit;
  if (nextOffset >= state.jobQuery.total) return;
  state.jobQuery.offset = nextOffset;
  await loadAll();
});

$("#listingList").addEventListener("click", (event) => {
  const item = event.target.closest("[data-listing-id]");
  if (!item) return;
  state.selectedListingId = Number(item.dataset.listingId);
  state.validationResults = {};
  renderListings();
});

$("#recentListings").addEventListener("click", (event) => {
  const item = event.target.closest("[data-listing-id]");
  if (!item) return;
  state.selectedListingId = Number(item.dataset.listingId);
  state.validationResults = {};
  show("listings");
  renderListings();
});

$("#listingForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const listing = selectedListing();
  if (!listing) return;
  const form = event.currentTarget;
  await api(`/listings/${listing.id}`, {
    method: "PATCH",
    body: JSON.stringify({
      title: form.title.value,
      price_cents: Math.round(Number(form.price.value || 0) * 100),
      condition: form.condition.value,
      category: form.category.value,
      location: form.location.value,
      brand: form.brand.value,
      model: form.model.value,
      color: form.color.value,
      material: form.material.value,
      weight_grams: Math.round(Number(form.weight_grams.value || 0)),
      shipping_cost_cents: Math.round(Number(form.shipping_cost.value || 0) * 100),
      pickup_allowed: form.pickup_allowed.checked,
      shipping_allowed: form.shipping_allowed.checked,
      tags: form.tags.value.split(",").map((tag) => tag.trim()).filter(Boolean),
      description: form.description.value,
      delivery_options: parseDeliveryOptions(form.delivery_options.value),
      dimensions: parseDeliveryOptions(form.dimensions.value),
      notes: form.notes.value,
      internal_notes: form.internal_notes.value,
      status: "draft",
    }),
  });
  await savePlatformOverrides();
  $("#editorMessage").textContent = "Saved";
  await loadAll();
});

$("#applyTemplateButton").addEventListener("click", () => {
  const templateId = Number($("#listingTemplateSelect").value);
  const template = state.templates.find((candidate) => candidate.id === templateId);
  if (!template) return;
  const description = $("#listingForm").description;
  description.value = [description.value.trim(), template.body.trim()].filter(Boolean).join("\n\n");
  $("#editorMessage").textContent = "Template applied";
});

$("#duplicateButton").addEventListener("click", async () => {
  const listing = selectedListing();
  if (!listing) return;
  const clone = await api(`/listings/${listing.id}/duplicate`, { method: "POST" });
  state.selectedListingId = clone.id;
  await loadAll();
});

$("#deleteListingButton").addEventListener("click", async () => {
  const listing = selectedListing();
  if (!listing) return;
  await api(`/listings/${listing.id}`, { method: "DELETE" });
  state.selectedListingId = null;
  await loadAll();
});

$("#imageInput").addEventListener("change", async (event) => {
  const listing = selectedListing();
  if (!listing || !event.target.files.length) return;
  for (const file of event.target.files) {
    const data = new FormData();
    data.append("file", file);
    await api(`/listings/${listing.id}/images`, { method: "POST", body: data, headers: {} });
  }
  event.target.value = "";
  await loadAll();
});

$("#imageList").addEventListener("click", async (event) => {
  const listing = selectedListing();
  if (!listing) return;
  const moveButton = event.target.closest("[data-move-image]");
  if (moveButton) {
    const imageId = Number(moveButton.dataset.moveImage);
    const direction = Number(moveButton.dataset.direction);
    const imageIds = (listing.images || []).map((image) => image.id);
    const index = imageIds.indexOf(imageId);
    const target = index + direction;
    if (index < 0 || target < 0 || target >= imageIds.length) return;
    [imageIds[index], imageIds[target]] = [imageIds[target], imageIds[index]];
    await api(`/listings/${listing.id}/images/order`, {
      method: "PATCH",
      body: JSON.stringify({ image_ids: imageIds }),
    });
    await loadAll();
    return;
  }
  const deleteButton = event.target.closest("[data-delete-image]");
  if (!deleteButton) return;
  await api(`/listings/${listing.id}/images/${deleteButton.dataset.deleteImage}`, { method: "DELETE" });
  await loadAll();
});

$("#validateButton").addEventListener("click", async () => {
  const listing = selectedListing();
  if (!listing) return;
  await savePlatformOverrides();
  const results = await api(`/listings/${listing.id}/validate`);
  state.validationResults = Object.fromEntries(results.map((result) => [result.platform, result]));
  $("#editorMessage").textContent = `${results.filter((item) => item.ready).length}/${results.length} ready`;
  await loadAll();
});

$("#prepublishReview").addEventListener("click", async (event) => {
  const packageButton = event.target.closest("[data-copy-package]");
  if (packageButton) {
    await copyText(packageText(packageButton.dataset.copyPackage));
    $("#editorMessage").textContent = "Package copied";
    return;
  }
  const fieldButton = event.target.closest("[data-copy-field]");
  if (fieldButton) {
    const validation = state.validationResults[fieldButton.dataset.copyField];
    const value = validation?.mapped_fields?.[fieldButton.dataset.copyName];
    await copyText(formatFieldValue(value));
    $("#editorMessage").textContent = "Field copied";
    return;
  }
  const fixButton = event.target.closest("[data-focus-missing]");
  if (!fixButton) return;
  focusRecoveryTarget(fixButton.dataset.focusMissing);
  $("#editorMessage").textContent = `Review ${formatFieldLabel(fixButton.dataset.focusMissing)}`;
});

$("#publishButton").addEventListener("click", async () => {
  const listing = selectedListing();
  if (!listing) return;
  await savePlatformOverrides();
  const platforms = [...document.querySelectorAll("[data-platform]")]
    .filter((checkbox) => checkbox.checked)
    .map((checkbox) => checkbox.dataset.platform);
  if (!platforms.length) {
    $("#editorMessage").textContent = "Select at least one platform";
    return;
  }
  await api(`/listings/${listing.id}/publish`, {
    method: "POST",
    body: JSON.stringify({ platforms, process_now: true }),
  });
  state.validationResults = {};
  state.jobQuery.offset = 0;
  $("#editorMessage").textContent = "Queued";
  show("queue");
  await loadAll();
});

$("#jobList").addEventListener("click", (event) => {
  const item = event.target.closest("[data-job-id]");
  if (!item) return;
  const job = state.jobs.find((candidate) => candidate.id === Number(item.dataset.jobId));
  if (!job) return;
  $("#jobDetails").classList.remove("hidden");
  $("#jobDetails").innerHTML = `
    <div class="pane-head">
      <h3>${escapeHtml(job.platform)} job #${job.id}</h3>
      <button class="ghost" id="retryJobButton">Retry</button>
    </div>
    <p><span class="${statusClass(job.status)}">${escapeHtml(job.status)}</span></p>
    <p class="muted">${escapeHtml(job.error_message || job.result?.posting_url || "")}</p>
    <h3>Logs</h3>
    ${(job.logs || []).map((log) => `<p class="job-log">${escapeHtml(log.message)}</p>`).join("")}
  `;
  $("#retryJobButton").addEventListener("click", async () => {
    await api(`/jobs/${job.id}/retry`, { method: "POST" });
    await loadAll();
  });
});

$("#accountForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  await api("/accounts", {
    method: "POST",
    body: JSON.stringify({
      platform: $("#accountPlatform").value,
      display_name: $("#accountName").value,
      status: $("#accountStatus").value,
      mode: "assisted",
      connection_data: {},
    }),
  });
  $("#accountName").value = "";
  await loadAll();
});

$("#accountList").addEventListener("click", async (event) => {
  const button = event.target.closest("[data-delete-account]");
  if (!button) return;
  await api(`/accounts/${button.dataset.deleteAccount}`, { method: "DELETE" });
  await loadAll();
});

$("#templateForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const templateId = event.currentTarget.dataset.templateId;
  await api(templateId ? `/templates/${templateId}` : "/templates", {
    method: templateId ? "PATCH" : "POST",
    body: JSON.stringify({
      name: $("#templateName").value,
      platform: $("#templatePlatform").value || null,
      body: $("#templateBody").value,
    }),
  });
  $("#templateName").value = "";
  $("#templateBody").value = "";
  $("#templatePlatform").value = "";
  delete event.currentTarget.dataset.templateId;
  $("#templateForm button[type='submit']").textContent = "Save template";
  $("#cancelTemplateEditButton").classList.add("hidden");
  await loadAll();
});

$("#cancelTemplateEditButton").addEventListener("click", () => {
  $("#templateName").value = "";
  $("#templateBody").value = "";
  $("#templatePlatform").value = "";
  delete $("#templateForm").dataset.templateId;
  $("#templateForm button[type='submit']").textContent = "Save template";
  $("#cancelTemplateEditButton").classList.add("hidden");
});

$("#templateList").addEventListener("click", async (event) => {
  const editButton = event.target.closest("[data-edit-template]");
  if (editButton) {
    const template = state.templates.find((candidate) => candidate.id === Number(editButton.dataset.editTemplate));
    if (!template) return;
    $("#templateName").value = template.name;
    $("#templatePlatform").value = template.platform || "";
    $("#templateBody").value = template.body;
    $("#templateForm").dataset.templateId = template.id;
    $("#templateForm button[type='submit']").textContent = "Update template";
    $("#cancelTemplateEditButton").classList.remove("hidden");
    return;
  }
  const deleteButton = event.target.closest("[data-delete-template]");
  if (!deleteButton) return;
  await api(`/templates/${deleteButton.dataset.deleteTemplate}`, { method: "DELETE" });
  await loadAll();
});

$("#categoryMappingForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const mappingId = event.currentTarget.dataset.mappingId;
  const payload = {
    source_category: $("#mappingSourceCategory").value,
    platform: $("#mappingPlatform").value,
    platform_category: $("#mappingPlatformCategory").value,
  };
  await api(mappingId ? `/category-mappings/${mappingId}` : "/category-mappings", {
    method: mappingId ? "PATCH" : "POST",
    body: JSON.stringify(payload),
  });
  $("#mappingSourceCategory").value = "";
  $("#mappingPlatformCategory").value = "";
  delete event.currentTarget.dataset.mappingId;
  $("#categoryMappingForm button[type='submit']").textContent = "Save mapping";
  await loadAll();
});

$("#categoryMappingList").addEventListener("click", async (event) => {
  const editButton = event.target.closest("[data-edit-category-mapping]");
  if (editButton) {
    const mapping = state.categoryMappings.find((candidate) => candidate.id === Number(editButton.dataset.editCategoryMapping));
    if (!mapping) return;
    $("#mappingSourceCategory").value = mapping.source_category;
    $("#mappingPlatform").value = mapping.platform;
    $("#mappingPlatformCategory").value = mapping.platform_category;
    $("#categoryMappingForm").dataset.mappingId = mapping.id;
    $("#categoryMappingForm button[type='submit']").textContent = "Update mapping";
    return;
  }
  const deleteButton = event.target.closest("[data-delete-category-mapping]");
  if (!deleteButton) return;
  await api(`/category-mappings/${deleteButton.dataset.deleteCategoryMapping}`, { method: "DELETE" });
  await loadAll();
});

$("#exportDataButton").addEventListener("click", async () => {
  const bundle = await api("/export");
  const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: "application/json" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `autoposter-export-${new Date().toISOString().slice(0, 10)}.json`;
  link.click();
  URL.revokeObjectURL(link.href);
  $("#dataPortabilityMessage").textContent = "Export ready";
});

$("#importDataInput").addEventListener("change", async (event) => {
  const file = event.target.files[0];
  if (!file) return;
  try {
    const bundle = JSON.parse(await file.text());
    const result = await api("/import", { method: "POST", body: JSON.stringify(bundle) });
    $("#dataPortabilityMessage").textContent =
      `Imported ${result.listings_created} listings, ${result.templates_created + result.templates_updated} templates, ` +
      `${result.category_mappings_created + result.category_mappings_updated} mappings`;
    await loadAll();
  } catch (error) {
    $("#dataPortabilityMessage").textContent = error.message;
  } finally {
    event.target.value = "";
  }
});

$("#runDiagnosticsButton").addEventListener("click", async () => {
  const diagnostics = await api("/diagnostics");
  renderDiagnostics(diagnostics);
});

$("#deleteMyDataButton").addEventListener("click", async () => {
  const confirmation = window.prompt("Type DELETE to permanently remove your account data.");
  if (confirmation !== "DELETE") return;
  await api("/auth/me", { method: "DELETE" });
  localStorage.removeItem("autoposterToken");
  window.location.reload();
});

boot();
