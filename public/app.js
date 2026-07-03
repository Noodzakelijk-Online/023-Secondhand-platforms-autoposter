const state = {
  token: localStorage.getItem("autoposterToken"),
  user: null,
  platforms: [],
  listings: [],
  jobs: [],
  accounts: [],
  templates: [],
  selectedListingId: null,
  selectedPlatforms: new Set(),
};

const $ = (selector) => document.querySelector(selector);
const money = (cents) => (cents / 100).toLocaleString(undefined, { style: "currency", currency: "EUR" });

async function api(path, options = {}) {
  const headers = options.headers || {};
  if (!(options.body instanceof FormData)) headers["Content-Type"] = "application/json";
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  const response = await fetch(`/api${path}`, { ...options, headers });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.error?.message || error.detail || "Request failed");
  }
  if (response.status === 204) return null;
  return response.json();
}

function show(view) {
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

async function loadAll() {
  const [platforms, listings, jobs, accounts, templates] = await Promise.all([
    api("/platforms"),
    api("/listings"),
    api("/jobs"),
    api("/accounts"),
    api("/templates"),
  ]);
  state.platforms = platforms;
  state.listings = listings;
  state.jobs = jobs;
  state.accounts = accounts;
  state.templates = templates;
  if (!state.selectedListingId && listings.length) state.selectedListingId = listings[0].id;
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
  form.tags.value = (listing.tags || []).join(", ");
  form.description.value = listing.description || "";
  form.delivery_options.value = JSON.stringify(listing.delivery_options || {}, null, 2);
  renderImages(listing);
  renderPlatforms(listing);
}

function renderImages(listing) {
  $("#imageList").innerHTML = (listing.images || []).map((image) => `
    <article class="image-tile">
      <img src="/uploads/${listing.id}/${image.storage_path.split(/[\\\\/]/).pop()}" alt="${escapeHtml(image.filename)}" />
      <strong>${escapeHtml(image.filename)}</strong>
      <button class="ghost" data-delete-image="${image.id}">Delete</button>
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
}

function renderJobs() {
  $("#jobList").innerHTML = state.jobs.map(jobItemHtml).join("") || `<p class="muted">No publishing jobs.</p>`;
}

function renderAccounts() {
  const platformOptions = state.platforms.map((platform) => `<option value="${platform.key}">${escapeHtml(platform.name)}</option>`).join("");
  $("#accountPlatform").innerHTML = platformOptions;
  $("#templatePlatform").innerHTML = `<option value="">All platforms</option>${platformOptions}`;
  $("#accountList").innerHTML = state.accounts.map((account) => `
    <article class="list-item">
      <strong>${escapeHtml(account.display_name)}</strong>
      <span class="muted">${escapeHtml(account.platform)} · ${escapeHtml(account.mode)}</span>
      <span class="${statusClass(account.status)}">${escapeHtml(account.status)}</span>
    </article>
  `).join("") || `<p class="muted">No platform accounts.</p>`;
}

function renderSettings() {
  $("#templateList").innerHTML = state.templates.map((template) => `
    <article class="list-item">
      <strong>${escapeHtml(template.name)}</strong>
      <span class="muted">${escapeHtml(template.platform || "All platforms")}</span>
      <p>${escapeHtml(template.body.slice(0, 160))}</p>
    </article>
  `).join("") || `<p class="muted">No templates saved.</p>`;
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
    await loadAll();
  } catch {
    localStorage.removeItem("autoposterToken");
    state.token = null;
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
  show("listings");
  await loadAll();
});

$("#refreshButton").addEventListener("click", loadAll);

$("#listingList").addEventListener("click", (event) => {
  const item = event.target.closest("[data-listing-id]");
  if (!item) return;
  state.selectedListingId = Number(item.dataset.listingId);
  renderListings();
});

$("#recentListings").addEventListener("click", (event) => {
  const item = event.target.closest("[data-listing-id]");
  if (!item) return;
  state.selectedListingId = Number(item.dataset.listingId);
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
      tags: form.tags.value.split(",").map((tag) => tag.trim()).filter(Boolean),
      description: form.description.value,
      delivery_options: parseDeliveryOptions(form.delivery_options.value),
      status: "draft",
    }),
  });
  await savePlatformOverrides();
  $("#editorMessage").textContent = "Saved";
  await loadAll();
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
  const button = event.target.closest("[data-delete-image]");
  const listing = selectedListing();
  if (!button || !listing) return;
  await api(`/listings/${listing.id}/images/${button.dataset.deleteImage}`, { method: "DELETE" });
  await loadAll();
});

$("#validateButton").addEventListener("click", async () => {
  const listing = selectedListing();
  if (!listing) return;
  await savePlatformOverrides();
  const results = await api(`/listings/${listing.id}/validate`);
  $("#editorMessage").textContent = `${results.filter((item) => item.ready).length}/${results.length} ready`;
  await loadAll();
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

$("#templateForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  await api("/templates", {
    method: "POST",
    body: JSON.stringify({
      name: $("#templateName").value,
      platform: $("#templatePlatform").value || null,
      body: $("#templateBody").value,
    }),
  });
  $("#templateName").value = "";
  $("#templateBody").value = "";
  await loadAll();
});

boot();
