from datetime import datetime, timezone
import os
import secrets
from uuid import uuid4

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, session

from game.logic import (
    choose_reward,
    create_new_run,
    handle_gear_choice,
    resolve_battle,
    shop_action,
    state_for_client,
)
from supabase_client import get_supabase

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", secrets.token_hex(32))


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def player_blob(run_state: dict) -> dict:
    return run_state.get("player", {}) if isinstance(run_state, dict) else {}


def current_run_id() -> str | None:
    run_id = session.get("run_id")
    if isinstance(run_id, str) and run_id.strip():
        return run_id
    return None


def save_run(run_id: str, run_state: dict):
    supabase = get_supabase()
    supabase.table("save_slots").upsert(
        {
            "player_name": run_id,
            "run_state": run_state,
            "updated_at": utc_now_iso(),
        },
        on_conflict="player_name",
    ).execute()


def load_run(run_id: str | None):
    if not run_id:
        return None
    supabase = get_supabase()
    response = (
        supabase.table("save_slots")
        .select("run_state")
        .eq("player_name", run_id)
        .limit(1)
        .execute()
    )
    data = response.data or []
    return data[0].get("run_state") if data else None


def delete_run(run_id: str | None):
    if not run_id:
        return
    supabase = get_supabase()
    supabase.table("save_slots").delete().eq("player_name", run_id).execute()


def submit_to_leaderboard(player_name: str, run_state: dict) -> bool:
    supabase = get_supabase()
    player = player_blob(run_state)
    score = max(0, (int(player.get("room", 1)) - 1) * 100 + int(player.get("gold", 0)))

    existing = (
        supabase.table("leaderboard")
        .select("score")
        .eq("player_name", player_name)
        .limit(1)
        .execute()
    ).data or []

    if existing and int(existing[0]["score"]) >= score:
        return False

    supabase.table("leaderboard").upsert(
        {
            "player_name": player_name,
            "class": player.get("hero_class") or "unknown",
            "score": score,
            "run_data": run_state,
            "submitted_at": utc_now_iso(),
        },
        on_conflict="player_name",
    ).execute()
    return True


@app.errorhandler(Exception)
def handle_unexpected_error(err):
    app.logger.exception("Unhandled server error")
    return jsonify({"error": "Internal server error"}), 500


@app.get("/")
def index():
    return render_template("game.html")


@app.get("/game")
def game_page():
    return render_template("game.html")


@app.get("/api/game/state")
def get_state():
    run_state = load_run(current_run_id())
    return jsonify(state_for_client(run_state))


@app.post("/api/game/new-run")
def new_run():
    data = request.get_json(silent=True) or {}
    hero_class = data.get("heroClass")
    display_name = str(data.get("player_name", "")).strip()

    if hero_class not in {"mage", "warrior", "rogue"}:
        return jsonify({"error": "Invalid class"}), 400

    run_state = create_new_run(hero_class)
    run_state["display_name"] = display_name or "Adventurer"

    run_id = str(uuid4())
    session["run_id"] = run_id
    save_run(run_id, run_state)
    return jsonify(state_for_client(run_state))


@app.post("/api/game/fight")
def fight():
    data = request.get_json(silent=True) or {}
    action = data.get("action", "attack")
    run_id = current_run_id()
    run_state = load_run(run_id)
    if not run_state:
        return jsonify({"error": "No active run"}), 400

    run_state = resolve_battle(run_state, action)
    save_run(run_id, run_state)
    return jsonify(state_for_client(run_state))


@app.post("/api/game/reward")
def reward():
    data = request.get_json(silent=True) or {}
    choice = data.get("choice")
    run_id = current_run_id()
    run_state = load_run(run_id)
    if not run_state:
        return jsonify({"error": "No active run"}), 400

    run_state = choose_reward(run_state, choice)
    save_run(run_id, run_state)
    return jsonify(state_for_client(run_state))


@app.post("/api/game/gear")
def gear():
    data = request.get_json(silent=True) or {}
    choice = data.get("choice")
    run_id = current_run_id()
    run_state = load_run(run_id)
    if not run_state:
        return jsonify({"error": "No active run"}), 400

    run_state = handle_gear_choice(run_state, choice)
    save_run(run_id, run_state)
    return jsonify(state_for_client(run_state))


@app.post("/api/game/shop")
def shop():
    data = request.get_json(silent=True) or {}
    action = data.get("action")
    run_id = current_run_id()
    run_state = load_run(run_id)
    if not run_state:
        return jsonify({"error": "No active run"}), 400

    run_state = shop_action(run_state, action)
    save_run(run_id, run_state)
    return jsonify(state_for_client(run_state))


@app.post("/api/run/submit")
def submit_run():
    run_state = load_run(current_run_id())
    if not run_state:
        return jsonify({"error": "No run to submit"}), 400

    player_name = run_state.get("display_name") or "Adventurer"
    updated = submit_to_leaderboard(player_name, run_state)
    return jsonify({"success": True, "updated": updated})


@app.post("/api/game/reset")
def reset_run():
    delete_run(current_run_id())
    session.pop("run_id", None)
    return jsonify({"success": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
