/******************************************************
 * GLOBAL CONFIG
 ******************************************************/
console.log("✅ map.js loaded");

const MAIN_TERMINAL_ID = window.MAIN_TERMINAL_ID || 1;
console.log("MAIN_TERMINAL_ID =", MAIN_TERMINAL_ID);

const activeTrips = new Map();   // trip_id → timer
const trafficLights = {};        // terminal_id → "red"/"green"


/******************************************************
 * NAVIGATION
 ******************************************************/
function goToTerminal(id) {
  console.log("➡️ goToTerminal called with id =", id);
  if (!id) return;
  window.location.href = "/seat/" + id;
}

// expose for inline onclick in HTML
window.goToTerminal = goToTerminal;


/******************************************************
 * MAIN TERMINAL CLICK
 ******************************************************/
function setupMainTerminalClick() {
  const mainTerminal = document.getElementById("mainTerminal");
  if (!mainTerminal) {
    console.warn("⚠️ #mainTerminal not found");
    return;
  }

  mainTerminal.addEventListener("click", () => {
    console.log("🟡 Main terminal clicked → /mainterminal");
    mainTerminal.classList.toggle("expanded");
    window.location.href = "/mainterminal";
  });
}


/******************************************************
 * SEAT MODAL SUPPORT
 ******************************************************/
function showSeatModal(trip) {
  const bg = document.getElementById("seatModalBg");
  const layout = document.getElementById("seatLayout");
  const seatId = document.getElementById("seatJeepId");

  if (!bg || !layout || !seatId) {
    console.warn("⚠️ Seat modal elements missing");
    return;
  }

  seatId.textContent = trip.jeepney_id;

  const cap = trip.capacity || 22;
  const pass = trip.passengers || 0;

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

// make close function globally accessible (for inline onclick)
window.closeSeatModal = closeSeatModal;


/******************************************************
 * TRAFFIC LIGHT INITIALIZATION
 ******************************************************/
function initTrafficLights() {
  document.querySelectorAll(".road").forEach(road => {
    const terminalId = road.dataset.terminalId;
    const light = road.querySelector(".traffic-light");
    if (!light || !terminalId) return;

    const initial = Math.random() < 0.5 ? "red" : "green";
    trafficLights[terminalId] = initial;
    light.classList.toggle("green", initial === "green");

    setInterval(() => {
      const current = trafficLights[terminalId];
      const next = current === "red" ? "green" : "red";
      trafficLights[terminalId] = next;
      light.classList.toggle("green", next === "green");
    }, 5000 + Math.random() * 5000);
  });
}


/******************************************************
 * HANDLE TRIPS (ANIMATION + ARRIVAL CALL)
 ******************************************************/
function handleTrips(trips) {
  const roads = document.querySelectorAll(".road");

  // reset states
  roads.forEach(road => {
    road.classList.remove("trip-in", "trip-out");
    const jeepDot = road.querySelector(".jeep-dot");
    if (jeepDot) {
      jeepDot.style.opacity = 0;
      jeepDot.onclick = null;
    }
  });

  trips.forEach(trip => {
    const isOutbound = trip.origin_terminal_id === MAIN_TERMINAL_ID;
    const otherId = isOutbound
      ? trip.destination_terminal_id
      : trip.origin_terminal_id;

    const direction = isOutbound ? "out" : "in";

    const road = document.querySelector(
      `.road[data-terminal-id="${otherId}"]`
    );
    if (!road) return;

    const jeepDot = road.querySelector(".jeep-dot");
    if (!jeepDot) return;

    // show jeep + animation
    jeepDot.style.opacity = 1;
    road.classList.add(direction === "in" ? "trip-in" : "trip-out");

    // click the moving jeep → seat layout
    jeepDot.onclick = () => showSeatModal(trip);

    // create travel timer once per trip
    if (!activeTrips.has(trip.trip_id)) {
      const baseTime = 10000 + Math.random() * 3000;
      const tlState = trafficLights[String(otherId)];
      const multiplier = (tlState === "red") ? 1.5 : 1.0;
      const travelTime = baseTime * multiplier;

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


/******************************************************
 * BACKEND LIVE TRIPS POLLING
 ******************************************************/
function refreshTrips() {
  fetch("/api/map/live-trips")
    .then(r => r.json())
    .then(trips => {
      // console.log("LIVE TRIPS:", trips);
      handleTrips(trips);
    })
    .catch(err => console.error("live-trip error:", err));
}


/******************************************************
 * OPTIONAL: SOUNDS
 ******************************************************/
const engine = new Audio("/static/map/sounds/engine.mp3");
const horn   = new Audio("/static/map/sounds/horn.mp3");
engine.loop = true;

function playEngine() {
  engine.volume = 0.4;
  engine.play().catch(() => {});
}

function stopEngine() {
  engine.pause();
}

function playHorn() {
  horn.volume = 1;
  horn.play().catch(() => {});
}


/******************************************************
 * INIT
 ******************************************************/
document.addEventListener("DOMContentLoaded", () => {
  console.log("📌 DOMContentLoaded on map.html");
  setupMainTerminalClick();
  initTrafficLights();
  refreshTrips();
  setInterval(refreshTrips, 3000);

  document.body.addEventListener("click", () => {
    playEngine();
  }, { once: true });
});
