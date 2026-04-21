from datetime import datetime, timezone
import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

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
app.secret_key = os.getenv("FLASK_SECRET_KEY", "420b420bud6689bir547sd75368bbghhf64327")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def player_blob(run_state: dict) -> dict:
    return run_state.get("player", {}) if isinstance(run_state, dict) else {}


def save_player_run(player_name: str, run_state: dict):
    supabase = get_supabase()
    supabase.table("save_slots").upsert(
        {
            "player_name": player_name,
            "run_state": run_state,
            "updated_at": utc_now_iso(),
        },
        on_conflict="player_name",
    ).execute()


def load_player_run(player_name: str):
    if not player_name:
        return None
    supabase = get_supabase()
    response = (
        supabase.table("save_slots")
        .select("run_state")
        .eq("player_name", player_name)
        .limit(1)
        .execute()
    )
    data = response.data or []
    return data[0].get("run_state") if data else None


def submit_to_leaderboard(player_name: str, run_state: dict):
    supabase = get_supabase()
    player = player_blob(run_state)
    room = int(player.get("room", 1))
    gold = int(player.get("gold", 0))
    score = max(0, (room - 1) * 100 + gold)
    class_key = player.get("hero_class") or player.get("class") or "unknown"
    supabase.table("leaderboard").upsert(
        {
            "player_name": player_name,
            "class": class_key,
            "score": score,
            "run_data": run_state,
            "submitted_at": utc_now_iso(),
        },
        on_conflict="player_name",
    ).execute()


@app.errorhandler(Exception)
def handle_unexpected_error(err):
    app.logger.exception("Unhandled server error")
    return jsonify({"error": str(err)}), 500


@app.get("/")
def index():
    return render_template("game.html")


@app.get("/game")
def game_page():
    return render_template("game.html")


@app.get("/api/game/state")
def get_state():
    player_name = request.args.get("player_name", "").strip()
    if not player_name:
        return jsonify({"has_run": False})
    run_state = load_player_run(player_name)
    if not run_state:
        return jsonify({"has_run": False})
    return jsonify(state_for_client(run_state))


@app.post("/api/game/new-run")
def new_run():
    data = request.get_json(silent=True) or {}
    player_name = str(data.get("player_name", "")).strip()
    hero_class = data.get("heroClass")
    if not player_name or hero_class not in {"mage", "warrior", "rogue"}:
        return jsonify({"error": "Invalid player or class"}), 400
    run_state = create_new_run(hero_class)
    save_player_run(player_name, run_state)
    return jsonify(state_for_client(run_state))


@app.post("/api/game/fight")
def fight():
    data = request.get_json(silent=True) or {}
    player_name = str(data.get("player_name", "")).strip()
    action = data.get("action", "attack")
    run_state = load_player_run(player_name)
    if not run_state:
        return jsonify({"error": "No active run"}), 400
    run_state = resolve_battle(run_state, action)
    save_player_run(player_name, run_state)
    return jsonify(state_for_client(run_state))


@app.post("/api/game/reward")
def reward():
    data = request.get_json(silent=True) or {}
    player_name = str(data.get("player_name", "")).strip()
    choice = data.get("choice")
    run_state = load_player_run(player_name)
    if not run_state:
        return jsonify({"error": "No active run"}), 400
    run_state = choose_reward(run_state, choice)
    save_player_run(player_name, run_state)
    return jsonify(state_for_client(run_state))


@app.post("/api/game/gear")
def gear():
    data = request.get_json(silent=True) or {}
    player_name = str(data.get("player_name", "")).strip()
    choice = data.get("choice")
    run_state = load_player_run(player_name)
    if not run_state:
        return jsonify({"error": "No active run"}), 400
    run_state = handle_gear_choice(run_state, choice)
    save_player_run(player_name, run_state)
    return jsonify(state_for_client(run_state))


@app.post("/api/game/shop")
def shop():
    data = request.get_json(silent=True) or {}
    player_name = str(data.get("player_name", "")).strip()
    action = data.get("action")
    run_state = load_player_run(player_name)
    if not run_state:
        return jsonify({"error": "No active run"}), 400
    run_state = shop_action(run_state, action)
    save_player_run(player_name, run_state)
    return jsonify(state_for_client(run_state))


@app.post("/api/run/submit")
def submit_run():
    data = request.get_json(silent=True) or {}
    player_name = str(data.get("player_name", "")).strip()
    run_state = load_player_run(player_name)
    if not run_state:
        return jsonify({"error": "No run to submit"}), 400
    submit_to_leaderboard(player_name, run_state)
    return jsonify({"success": True, "message": "Run submitted to leaderboard!"})


@app.post("/api/game/reset")
def reset_run():
    data = request.get_json(silent=True) or {}
    player_name = str(data.get("player_name", "")).strip()
    if not player_name:
        return jsonify({"error": "player_name required"}), 400
    supabase = get_supabase()
    supabase.table("save_slots").delete().eq("player_name", player_name).execute()
    return jsonify({"success": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
