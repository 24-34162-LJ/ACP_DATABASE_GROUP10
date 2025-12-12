/******************************************************
 * static/map/map.js
 *
 * Full, ready-to-drop JavaScript for the dynamic radial map
 * - supports up to 20 terminals
 * - radial layout + simple repel to reduce overlaps
 * - main terminal click handler (robust)
 * - traffic lights, jeep-dot animation, favorites, seat modal
 * - polling for live trips
 ******************************************************/

console.log("✅ map.js loaded");

const MAIN_TERMINAL_ID = window.MAIN_TERMINAL_ID || 1;
console.log("MAIN_TERMINAL_ID =", MAIN_TERMINAL_ID);

const activeTrips = new Map();   // trip_id -> timer id
const trafficLights = {};        // terminal_id -> "red"|"green"

/* NAV: open terminal seat page */
function goToTerminal(id) {
  if (!id) return;
  console.log("➡️ Navigating to terminal", id);
  window.location.href = "/seat/" + id;
}
window.goToTerminal = goToTerminal;

/* ---------- MAIN TERMINAL CLICK (robust attach) ---------- */
function setupMainTerminalClick() {
  function attachOnce() {
    const mainTerminal = document.getElementById("mainTerminal");
    if (!mainTerminal) {
      console.warn("⚠️ #mainTerminal not present yet.");
      return false;
    }

    // ensure it's clickable & on top
    mainTerminal.style.zIndex = 2000;
    mainTerminal.style.pointerEvents = "auto";

    // remove previous handlers by replacing the node with a clone
    const clone = mainTerminal.cloneNode(true);
    mainTerminal.parentNode.replaceChild(clone, mainTerminal);

    // attach handler to the new node
    clone.addEventListener("click", (ev) => {
      ev.stopPropagation();
      ev.preventDefault();
      console.log("🟡 Main terminal clicked → navigating to /mainterminal");
      // optional visual feedback
      clone.classList.toggle("expanded");
      // small delay so user sees the expand
      setTimeout(() => {
        window.location.href = "/mainterminal";
      }, 120);
    });

    return true;
  }

  if (!attachOnce()) {
    let tries = 0;
    const maxTries = 8;
    const t = setInterval(() => {
      tries++;
      if (attachOnce() || tries >= maxTries) {
        clearInterval(t);
        if (tries >= maxTries) console.warn("⚠️ setupMainTerminalClick: giving up after retries");
      }
    }, 150);
  }
}

/* ---------- SEAT MODAL ---------- */
function showSeatModal(trip) {
  const bg = document.getElementById("seatModalBg");
  const layout = document.getElementById("seatLayout");
  const seatId = document.getElementById("seatJeepId");

  if (!bg || !layout || !seatId) {
    console.warn("⚠️ Seat modal elements missing");
    return;
  }

  seatId.textContent = trip.jeepney_id !== undefined ? trip.jeepney_id : "—";

  const cap = Number(trip.capacity) || 22;
  const pass = Number(trip.passengers) || 0;

  let html = "";
  for (let i = 0; i < cap; i++) {
    const filled = i < pass ? "filled" : "empty";
    html += `<div class="seat-square ${filled}"></div>`;
  }
  layout.innerHTML = html;
  bg.style.display = "flex";
}

function closeSeatModal() {
  const bg = document.getElementById("seatModalBg");
  if (bg) bg.style.display = "none";
}
window.closeSeatModal = closeSeatModal;

/* ---------- FAVORITES (Save button) ---------- */
function setupFavoriteButtons() {
  const buttons = document.querySelectorAll(".fav-btn, .fav-btn"); // keep compatibility with different templates
  if (!buttons.length) return;

  buttons.forEach(btn => {
    // avoid attaching multiple times
    if (btn._favAttached) return;
    btn._favAttached = true;

    btn.addEventListener("click", async (event) => {
      event.stopPropagation(); // don't trigger goToTerminal

      const terminalId = btn.dataset.terminalId;
      const name = btn.dataset.terminalName || "this terminal";

      const label = window.prompt(`Add a label for ${name} (optional):`, "");
      if (label === null) return; // user cancelled

      const body = new URLSearchParams();
      if (terminalId) body.append("terminal_id", terminalId);
      if (label.trim()) body.append("label", label.trim());

      try {
        const resp = await fetch("/favorites/add", {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8" },
          body: body.toString()
        });
        const data = await resp.json().catch(() => ({}));
        if (!resp.ok) {
          console.error("Favorite save error:", data);
          alert("Error saving favorite.");
          return;
        }
        btn.classList.add("saved");
        const text = btn.querySelector(".fav-text");
        if (text) text.textContent = "Saved";
        else btn.textContent = "⭐ Saved";
        console.log("Favorite saved:", data);
      } catch (err) {
        console.error("Favorite network error:", err);
        alert("Network error while saving favorite.");
      }
    });
  });
}

/* ---------- TRAFFIC LIGHTS ---------- */
function initTrafficLights() {
  document.querySelectorAll(".dynamic-road, .road").forEach(road => {
    const terminalId = road.dataset.terminalId;
    const light = road.querySelector(".traffic-light");
    if (!light || !terminalId) return;

    const initial = Math.random() < 0.5 ? "red" : "green";
    trafficLights[terminalId] = initial;
    light.classList.toggle("green", initial === "green");

    // cycle periodically
    setInterval(() => {
      const current = trafficLights[terminalId];
      const next = current === "red" ? "green" : "red";
      trafficLights[terminalId] = next;
      light.classList.toggle("green", next === "green");
    }, 4500 + Math.random() * 4500);
  });
}

/* ---------- LAYOUT: radial + repel ---------- */
function layoutTerminals(maxSlots = 20) {
  const viewport = document.getElementById("mapViewport") || document.querySelector(".map-viewport") || document.querySelector(".map");
  const inner = document.getElementById("mapInner") || document.querySelector(".map-inner") || document.querySelector(".map");
  if (!viewport || !inner) {
    console.warn("⚠️ layoutTerminals: map elements not found");
    return;
  }

  const rect = viewport.getBoundingClientRect();
  const width = rect.width;
  const height = rect.height;
  const center = { x: width / 2, y: height / 2 };

  const radiusX = Math.min(800, width * 0.45);
  const radiusY = Math.min(450, height * 0.45);

  const termEls = Array.from(document.querySelectorAll(".dynamic-terminal"));
  const roadEls = Array.from(document.querySelectorAll(".dynamic-road, .road"));

  const count = Math.min(maxSlots, termEls.length);
  if (count === 0) return;

  // initial radial positions
  for (let i = 0; i < termEls.length; i++) {
    const el = termEls[i];
    if (i >= count) { el.style.display = "none"; continue; }
    el.style.display = "block";
    el.classList.remove("small");
    const angle = -Math.PI / 2 + (i / count) * (Math.PI * 2);
    const ex = center.x + Math.cos(angle) * radiusX;
    const ey = center.y + Math.sin(angle) * radiusY;
    el._x = ex;
    el._y = ey;
    if (count > 12) el.classList.add("small");
  }

  // place roads between center and endpoint
  for (let i = 0; i < roadEls.length; i++) {
    const road = roadEls[i];
    if (i >= count) { road.style.display = "none"; continue; }
    road.style.display = "block";
    const angle = -Math.PI / 2 + (i / count) * (Math.PI * 2);
    const endX = center.x + Math.cos(angle) * radiusX;
    const endY = center.y + Math.sin(angle) * radiusY;
    const midX = (center.x + endX) / 2;
    const midY = (center.y + endY) / 2;
    const dx = endX - center.x;
    const dy = endY - center.y;
    const len = Math.sqrt(dx * dx + dy * dy);

    road.style.width = `${len}px`;
    road.style.height = `28px`;
    road.style.left = `${midX - len / 2}px`;
    road.style.top = `${midY - 14}px`;

    const deg = (Math.atan2(dy, dx) * 180) / Math.PI;
    road.style.transform = `rotate(${deg}deg)`;

    const jeepDot = road.querySelector(".jeep-dot");
    if (jeepDot) {
      jeepDot.style.left = "0%";
      jeepDot.onclick = (e) => e.stopPropagation();
    }
  }

  // simple iterative repel to reduce overlap
  const nodes = termEls.slice(0, count).map(el => ({ el, x: el._x, y: el._y, w: el.offsetWidth, h: el.offsetHeight }));
  const iterations = 18;
  for (let k = 0; k < iterations; k++) {
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const a = nodes[i];
        const b = nodes[j];
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const overlapX = (a.w / 2 + b.w / 2) - Math.abs(dx);
        const overlapY = (a.h / 2 + b.h / 2) - Math.abs(dy);
        if (overlapX > 0 && overlapY > 0) {
          // push them apart
          const pushX = dx === 0 ? (Math.random() - 0.5) * 1 : dx;
          const pushY = dy === 0 ? (Math.random() - 0.5) * 1 : dy;
          const mag = Math.sqrt(pushX * pushX + pushY * pushY) || 1;
          const ux = pushX / mag, uy = pushY / mag;
          const shift = Math.min(8, Math.max(overlapX, overlapY)) * 0.5;
          b.x += ux * shift;
          b.y += uy * shift;
          a.x -= ux * shift;
          a.y -= uy * shift;

          // clamp inside viewport margin
          [a, b].forEach(n => {
            n.x = Math.max(40, Math.min(width - 40, n.x));
            n.y = Math.max(40, Math.min(height - 40, n.y));
          });
        }
      }
    }
  }

  // apply positions
  nodes.forEach(n => {
    n.el.style.left = `${n.x}px`;
    n.el.style.top = `${n.y}px`;
  });

  // center joint & main terminal exactly
  const joint = document.getElementById("joint");
  if (joint) {
    joint.style.left = `${center.x}px`;
    joint.style.top = `${center.y}px`;
    joint.style.transform = "translate(-50%,-50%)";
  }
  const main = document.getElementById("mainTerminal");
  if (main) {
    main.style.left = `${center.x}px`;
    main.style.top = `${center.y}px`;
    main.style.transform = "translate(-50%,-50%)";
  }
}

/* helper that initializes layout and resizes with debounce */
function initLayoutSupport() {
  layoutTerminals(20);
  window.addEventListener("resize", () => {
    if (window._layoutTimeout) clearTimeout(window._layoutTimeout);
    window._layoutTimeout = setTimeout(() => layoutTerminals(20), 120);
  });
}

/* ---------- HANDLE TRIPS (animation + arrival call) ---------- */
function handleTrips(trips) {
  const roads = document.querySelectorAll(".dynamic-road, .road");

  // reset existing road state
  roads.forEach(road => {
    road.classList.remove("trip-in", "trip-out");
    const jeepDot = road.querySelector(".jeep-dot");
    if (jeepDot) {
      jeepDot.style.opacity = 0;
      jeepDot.onclick = null;
    }
  });

  (trips || []).forEach(trip => {
    const isOutbound = trip.origin_terminal_id === MAIN_TERMINAL_ID;
    const otherId = isOutbound ? trip.destination_terminal_id : trip.origin_terminal_id;
    const direction = isOutbound ? "out" : "in";

    const road = document.querySelector(`.dynamic-road[data-terminal-id="${otherId}"], .road[data-terminal-id="${otherId}"]`);
    if (!road) return;

    const jeepDot = road.querySelector(".jeep-dot");
    if (!jeepDot) return;

    jeepDot.style.opacity = 1;
    road.classList.add(direction === "in" ? "trip-in" : "trip-out");

    jeepDot.onclick = (e) => {
      e.stopPropagation();
      showSeatModal(trip);
    };

    // create travel timer once per trip_id
    if (!activeTrips.has(trip.trip_id)) {
      const baseTime = 9000 + Math.random() * 4000;
      const tlState = trafficLights[String(otherId)];
      const multiplier = (tlState === "red") ? 1.5 : 1.0;
      const travelTime = baseTime * multiplier;

      road.style.setProperty("--travel-time", `${travelTime / 1000}s`);

      const timer = setTimeout(() => {
        fetch("/api/trips/arrive", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            jeepney_id: trip.jeepney_id,
            origin_terminal_id: trip.origin_terminal_id,
            destination_terminal_id: trip.destination_terminal_id
          })
        }).catch(err => console.error("arrive error:", err));

        activeTrips.delete(trip.trip_id);
      }, travelTime);

      activeTrips.set(trip.trip_id, timer);
    }
  });
}

/* ---------- POLLING FOR LIVE TRIPS ---------- */
function refreshTrips() {
  fetch("/api/map/live-trips")
    .then(r => r.json())
    .then(trips => {
      handleTrips(trips);
    })
    .catch(err => {
      console.error("live-trip error:", err);
    });
}

/* ---------- SOUNDS (optional) ---------- */
const engine = new Audio("/static/map/sounds/engine.mp3");
const horn = new Audio("/static/map/sounds/horn.mp3");
engine.loop = true;

function playEngine() {
  engine.volume = 0.36;
  engine.play().catch(() => {});
}
function stopEngine() {
  engine.pause();
}
function playHorn() {
  horn.volume = 1;
  horn.play().catch(() => {});
}

/* ---------- ZOOM control (if range exists) ---------- */
function initZoom() {
  const zoomRange = document.getElementById("zoomRange");
  const inner = document.getElementById("mapInner") || document.querySelector(".map-inner") || document.querySelector(".map");
  if (!zoomRange || !inner) return;
  function setZoom(v) { inner.style.transform = `scale(${v})`; }
  zoomRange.addEventListener("input", (e) => setZoom(e.target.value));
  setZoom(zoomRange.value || 1);
}

/* ---------- INIT ---------- */
document.addEventListener("DOMContentLoaded", () => {
  console.log("📌 DOMContentLoaded on map page");

  // attach main terminal click first to avoid race with cloned nodes
  setupMainTerminalClick();

  // layout + UI
  initLayoutSupport();
  initZoom();
  initTrafficLights();
  setupFavoriteButtons();

  // initial trips + poll
  refreshTrips();
  setInterval(refreshTrips, 3000);

  // start engine sound once on first interaction (user gesture)
  document.body.addEventListener("click", () => {
    try { playEngine(); } catch (e) { /* ignore */ }
  }, { once: true });
});
