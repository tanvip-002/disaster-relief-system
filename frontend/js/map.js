// ─────────────────────────────────────────────────────────
// RELIEFOPS — MAP & NOTIFICATION FRONTEND LOGIC
// Backend: FastAPI at http://127.0.0.1:8000
// ─────────────────────────────────────────────────────────

const API = "http://127.0.0.1:8000";

// ── AUTH ──
function getToken() { return localStorage.getItem("token") || ""; }

function authHeaders() {
  return {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${getToken()}`
  };
}

// ── THEME TOGGLE ──
function toggleTheme() {
  const html = document.documentElement;
  const isDark = html.getAttribute("data-theme") === "dark";
  const next = isDark ? "light" : "dark";
  html.setAttribute("data-theme", next);
  document.getElementById("themeLbl").textContent = next.toUpperCase();
  localStorage.setItem("theme", next);

  // Re-apply tile filter when theme changes
  if (window._map) {
    const tiles = document.querySelectorAll(".leaflet-tile");
    tiles.forEach(t => {
      t.style.filter = next === "dark"
        ? "brightness(0.72) saturate(0.6) hue-rotate(180deg) invert(1)"
        : "none";
    });
  }
}

// ── EMAIL CONSENT ──
let emailConsent = localStorage.getItem("emailConsent") === "true";
let userEmail    = localStorage.getItem("userEmail") || "";

function checkConsent() {
  if (localStorage.getItem("emailConsent") === null) {
    document.getElementById("consentModal").classList.add("open");
  }
}

function giveConsent(agreed) {
  emailConsent = agreed;
  localStorage.setItem("emailConsent", String(agreed));
  document.getElementById("consentModal").classList.remove("open");

  if (agreed) {
    const email = prompt("Enter your email address for critical alerts:");
    if (email && email.includes("@")) {
      userEmail = email;
      localStorage.setItem("userEmail", email);
      toast("✅ Email alerts enabled!", "success");
    } else if (email) {
      toast("⚠️ Invalid email — alerts disabled", "error");
      emailConsent = false;
      localStorage.setItem("emailConsent", "false");
    }
  } else {
    toast("In-app notifications only — got it!", "info");
  }
}

// ── MAP INIT ──
const map = L.map("map", {
  center: [20.5937, 78.9629],
  zoom: 5,
  zoomControl: true
});

window._map = map;

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "© OpenStreetMap contributors",
  maxZoom: 19
}).addTo(map);

// Show coordinates on hover
map.on("mousemove", e => {
  document.getElementById("coordBar").textContent =
    `${e.latlng.lat.toFixed(5)},  ${e.latlng.lng.toFixed(5)}`;
});

// Clicking map fills lat/lon inputs
map.on("click", e => {
  document.getElementById("iLat").value = e.latlng.lat.toFixed(6);
  document.getElementById("iLon").value = e.latlng.lng.toFixed(6);
  toast("📍 Coordinates captured from map!", "info");
});

let markers  = [];
let userMark = null;

function clearMarkers() {
  markers.forEach(m => map.removeLayer(m));
  markers = [];
}

// ── MARKER HELPERS ──
const TYPE_COLORS = {
  shelter:   "#3b82f6",
  hospital:  "#ef4444",
  food_bank: "#22c55e",
  other:     "#f97316"
};

const TYPE_EMOJI = {
  shelter:   "🏠",
  hospital:  "🏥",
  food_bank: "🍎",
  other:     "📍"
};

function makeMarker(lat, lon, type) {
  const color = TYPE_COLORS[type] || "#f97316";
  const emoji = TYPE_EMOJI[type]  || "📍";

  const icon = L.divIcon({
    className: "",
    html: `
      <div style="
        background:${color};
        width:30px;height:30px;
        border-radius:50% 50% 50% 0;
        transform:rotate(-45deg);
        border:2.5px solid white;
        box-shadow:0 3px 10px rgba(0,0,0,0.35);
        display:flex;align-items:center;justify-content:center;
      ">
        <span style="transform:rotate(45deg);font-size:13px">${emoji}</span>
      </div>`,
    iconSize:    [30, 30],
    iconAnchor:  [15, 30],
    popupAnchor: [0, -34]
  });

  return L.marker([lat, lon], { icon });
}

// ── LOAD ALL LOCATIONS ──
async function loadAll() {
  try {
    toast("Loading all centers...", "info");
    const res = await fetch(`${API}/maps/locations`, { headers: authHeaders() });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const locs = await res.json();
    clearMarkers();
    renderList(locs, false);
    plotOnMap(locs);
    updateStats(locs, null);
    toast(`✅ ${locs.length} centers loaded`, "success");
  } catch (e) {
    toast(`❌ Failed: ${e.message}`, "error");
  }
}

// ── SEARCH NEARBY ──
async function searchNearby() {
  const lat    = parseFloat(document.getElementById("iLat").value);
  const lon    = parseFloat(document.getElementById("iLon").value);
  const radius = parseFloat(document.getElementById("iRadius").value) || 10;

  if (isNaN(lat) || isNaN(lon)) {
    toast("⚠️ Enter valid coordinates first", "error");
    return;
  }

  try {
    toast(`Searching within ${radius} km...`, "info");
    const res = await fetch(`${API}/maps/locations/nearby`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ latitude: lat, longitude: lon, radius_km: radius })
    });

    if (res.status === 404) { toast(`No centers within ${radius} km`, "error"); return; }
    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const nearby = await res.json();
    clearMarkers();
    renderList(nearby, true);
    plotOnMap(nearby);
    map.setView([lat, lon], 12);

    // User position circle
    if (userMark) map.removeLayer(userMark);
    userMark = L.circleMarker([lat, lon], {
      radius: 9, fillColor: "#f97316",
      color: "white", weight: 2.5, fillOpacity: 0.95
    }).addTo(map).bindPopup("📍 Your Location");
    markers.push(userMark);

    updateStats(nearby, nearby.length);
    toast(`✅ ${nearby.length} centers found nearby`, "success");
  } catch (e) {
    toast(`❌ Search failed: ${e.message}`, "error");
  }
}

// ── GPS LOCATION ──
function useGPS() {
  if (!navigator.geolocation) { toast("❌ Geolocation not supported", "error"); return; }
  toast("📍 Locating you...", "info");
  navigator.geolocation.getCurrentPosition(
    pos => {
      document.getElementById("iLat").value = pos.coords.latitude.toFixed(6);
      document.getElementById("iLon").value = pos.coords.longitude.toFixed(6);
      map.setView([pos.coords.latitude, pos.coords.longitude], 13);
      toast(`📍 Found: ${pos.coords.latitude.toFixed(4)}, ${pos.coords.longitude.toFixed(4)}`, "success");
    },
    err => toast(`❌ ${err.message}`, "error")
  );
}

// ── PLOT ON MAP ──
function plotOnMap(locs) {
  const bounds = [];

  locs.forEach(loc => {
    const m = makeMarker(loc.latitude, loc.longitude, loc.type);
    const dist = loc.distance_km !== undefined
      ? `<br><span style="color:#22c55e;font-size:11px;font-weight:700">📏 ${loc.distance_km} km away</span>`
      : "";

    m.bindPopup(`
      <div style="min-width:150px">
        <strong style="font-size:13px">${TYPE_EMOJI[loc.type]||"📍"} ${loc.name}</strong><br/>
        <span style="font-size:11px;opacity:0.6;text-transform:uppercase">${loc.type.replace("_"," ")}</span>
        ${dist}<br/>
        <span style="font-size:10px;opacity:0.45">${loc.latitude.toFixed(5)}, ${loc.longitude.toFixed(5)}</span>
      </div>
    `);

    m.addTo(map);
    markers.push(m);
    bounds.push([loc.latitude, loc.longitude]);
  });

  if (bounds.length && !userMark) {
    map.fitBounds(bounds, { padding: [40, 40] });
  }
}

// ── RENDER SIDEBAR LIST ──
function renderList(locs, isNearby) {
  const el = document.getElementById("locList");
  if (!locs.length) {
    el.innerHTML = `<div class="empty-msg">No centers found.</div>`;
    return;
  }

  el.innerHTML = locs.map(l => `
    <div class="loc-item ${isNearby ? "nearby" : ""}"
         onclick="focusLoc(${l.latitude},${l.longitude},'${l.name.replace(/'/g,"\\'")}')">
      <div class="pip pip-${l.type}"></div>
      <div class="loc-body">
        <div class="loc-name">${l.name}</div>
        <div class="loc-sub">${l.type.replace("_"," ").toUpperCase()}</div>
      </div>
      ${l.distance_km !== undefined
        ? `<div class="loc-km">${l.distance_km}km</div>`
        : ""}
    </div>
  `).join("");
}

function focusLoc(lat, lon, name) {
  map.setView([lat, lon], 14);
  toast(`📍 ${name}`, "info");
}

// ── STATS ──
function updateStats(locs, nearbyCount) {
  document.getElementById("sTotal").textContent    = locs.length;
  document.getElementById("sNearby").textContent   = nearbyCount !== null ? nearbyCount : "—";
  document.getElementById("sShelters").textContent = locs.filter(l => l.type === "shelter").length;
  document.getElementById("sHospitals").textContent= locs.filter(l => l.type === "hospital").length;
}

// ── ADD LOCATION ──
function openAddModal()  { document.getElementById("addModal").classList.add("open"); }
function closeAddModal() { document.getElementById("addModal").classList.remove("open"); }

async function submitAdd() {
  const name = document.getElementById("aName").value.trim();
  const type = document.getElementById("aType").value;
  const lat  = parseFloat(document.getElementById("aLat").value);
  const lon  = parseFloat(document.getElementById("aLon").value);

  if (!name || isNaN(lat) || isNaN(lon)) {
    toast("⚠️ Fill in all fields", "error"); return;
  }

  try {
    const res = await fetch(`${API}/maps/locations`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ name, type, latitude: lat, longitude: lon })
    });

    if (res.status === 403) { toast("❌ Admin access required", "error"); return; }
    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const created = await res.json();
    closeAddModal();
    toast(`✅ "${created.name}" added!`, "success");

    const m = makeMarker(created.latitude, created.longitude, created.type);
    m.addTo(map).openPopup();
    markers.push(m);
    map.setView([created.latitude, created.longitude], 13);
  } catch (e) {
    toast(`❌ ${e.message}`, "error");
  }
}

// ── NOTIFICATIONS ──
function openDrawer() {
  document.getElementById("drawer").classList.add("open");
  loadNotifications();
}

function closeDrawer() {
  document.getElementById("drawer").classList.remove("open");
}

async function loadNotifications() {
  const list = document.getElementById("notifList");
  try {
    const res = await fetch(`${API}/maps/notifications`, { headers: authHeaders() });
    if (res.status === 404) {
      list.innerHTML = `<div class="empty-msg">No notifications yet.</div>`;
      updateBadge(0); return;
    }
    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const notifs = await res.json();
    const unread = notifs.filter(n => !n.is_read).length;
    updateBadge(unread);

    list.innerHTML = notifs.map(n => `
      <div class="notif-card ${!n.is_read ? "unread" : ""}"
           onclick="markRead(${n.id}, this)">
        <div class="notif-title">${n.title}</div>
        <div class="notif-body">${n.message}</div>
        <div class="notif-time">
          ${new Date(n.created_at).toLocaleString()}
          ${n.email_sent ? " · 📧 emailed" : ""}
        </div>
      </div>
    `).join("");
  } catch {
    list.innerHTML = `<div class="empty-msg">Could not load notifications.</div>`;
  }
}

async function markRead(id, el) {
  try {
    await fetch(`${API}/maps/notifications/${id}/read`, {
      method: "PATCH", headers: authHeaders()
    });
    el.classList.remove("unread");
    loadNotifications();
  } catch { /* silent */ }
}

function updateBadge(n) {
  const b = document.getElementById("badge");
  if (n > 0) { b.style.display = "flex"; b.textContent = n; }
  else { b.style.display = "none"; }
}

// ── TOAST ──
function toast(msg, type = "info") {
  const stack = document.getElementById("toasts");
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = msg;
  stack.appendChild(el);
  setTimeout(() => { el.style.opacity = "0"; setTimeout(() => el.remove(), 300); }, 3000);
}

// ── INIT ──
document.addEventListener("DOMContentLoaded", () => {
  // Restore saved theme
  const saved = localStorage.getItem("theme") || "dark";
  document.documentElement.setAttribute("data-theme", saved);
  document.getElementById("themeLbl").textContent = saved.toUpperCase();

  // Check email consent
  checkConsent();

  // Poll notifications every 30s
  setInterval(() => { if (getToken()) loadNotifications(); }, 30000);

  toast("🚨 ReliefOps Dashboard ready", "info");
});