let currentPlayerName = null;

function getPlayerName() {
  if (currentPlayerName) return currentPlayerName;
  const urlParams = new URLSearchParams(window.location.search);
  let player = urlParams.get("player") || localStorage.getItem("player_name");
  if (!player) player = prompt("Enter your player name:", "CrashOutCrypto");
  currentPlayerName = (player || "Adventurer").trim().replace(/[^a-zA-Z0-9_]/g, "_");
  localStorage.setItem("player_name", currentPlayerName);
  return currentPlayerName;
}

async function api(endpoint, method = "GET", body = null) {
  const options = { method, headers: {} };
  if (body) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }
  const res = await fetch(endpoint, options);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Server error");
  return data;
}

function renderState(state) {
  const hasRun = !!state.has_run;
  document.getElementById("class-selection").style.display = hasRun ? "none" : "block";
  document.getElementById("game-ui").classList.toggle("hidden", !hasRun);
  if (!hasRun) return;

  const p = state.player || {};
  const e = state.enemy || null;

  document.getElementById("player-name").textContent = getPlayerName();
  document.getElementById("player-class").textContent =
    p.display_class || p.class_label || (p.class || "").toUpperCase();
  document.getElementById("player-hp").textContent = `${p.hp ?? 0}/${p.max_hp ?? 0}`;
  document.getElementById("player-gold").textContent = p.gold ?? 0;
  document.getElementById("player-room").textContent = p.room ?? state.room ?? 0;

  const hpPercent = Math.max(0, Math.min(100, ((p.hp ?? 0) / Math.max(1, p.max_hp ?? 1)) * 100));
  document.getElementById("hp-bar").style.width = `${hpPercent}%`;

  const enemySec = document.getElementById("enemy-section");
  if (e) {
    enemySec.classList.remove("hidden");
    document.getElementById("enemy-name").textContent = e.name;
    document.getElementById("enemy-hp").textContent = `${e.hp}/${e.max_hp}`;
  } else {
    enemySec.classList.add("hidden");
  }

  document.getElementById("battle-log").innerHTML =
    (state.battle_log || []).map((line) => `<div>${line}</div>`).join("");

  const rewardSec = document.getElementById("reward-section");
  if (Array.isArray(state.reward_options) && state.reward_options.length) {
    rewardSec.classList.remove("hidden");
    document.getElementById("reward-options").innerHTML =
      state.reward_options.map((opt) => `
        <button onclick="chooseReward('${opt.id}')" class="w-full bg-emerald-700 py-4 rounded-2xl text-left px-6 text-sm">
          ${opt.label}
        </button>
      `).join("");
  } else if (state.gear_offer) {
    rewardSec.classList.remove("hidden");
    document.getElementById("reward-options").innerHTML = `
      <div class="mb-4">${state.gear_offer.rarity} ${state.gear_offer.name} (${state.gear_offer.slot})</div>
      <button onclick="chooseGear('equip')" class="w-full bg-blue-700 py-4 rounded-2xl mb-3">Equip</button>
      <button onclick="chooseGear('sell')" class="w-full bg-zinc-700 py-4 rounded-2xl">Sell</button>
    `;
  } else {
    rewardSec.classList.add("hidden");
  }

  document.getElementById("run-over-section").classList.toggle("hidden", !state.run_over);
}

async function startNewRun(heroClass) {
  const playerName = getPlayerName();
  const data = await api("/api/game/new-run", "POST", { heroClass, player_name: playerName });
  renderState(data);
}

async function fight(action = "attack") {
  const data = await api("/api/game/fight", "POST", { action });
  renderState(data);
}

async function chooseReward(choice) {
  const data = await api("/api/game/reward", "POST", { choice });
  renderState(data);
}

async function chooseGear(choice) {
  const data = await api("/api/game/gear", "POST", { choice });
  renderState(data);
}

async function shopAction(action) {
  const data = await api("/api/game/shop", "POST", { action });
  renderState(data);
}

async function resetRun() {
  if (!confirm("Start a new run?")) return;
  await api("/api/game/reset", "POST", {});
  renderState({ has_run: false });
}

async function submitToLeaderboard() {
  const data = await api("/api/run/submit", "POST", {});
  alert(data.updated ? "Run submitted to leaderboard!" : "Run submitted, but your best score remains unchanged.");
}

async function initGame() {
  getPlayerName();
  const state = await api("/api/game/state");
  renderState(state);
}

document.addEventListener("DOMContentLoaded", initGame);
