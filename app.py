from flask import Flask, request, jsonify, render_template
import os
from dotenv import load_dotenv

# Game logic imports
from game.logic import (
    create_new_run,
    resolve_battle,
    choose_reward,
    handle_gear_choice,
    shop_action,
    state_for_client,
)

# Supabase (lazy-loaded)
from supabase_client import get_supabase

load_dotenv()
app = Flask(__name__)
app.secret_key = os.urandom(24)

# ====================== SUPABASE HELPERS ======================
def save_player_run(player_name: str, run_state: dict):
    supabase = get_supabase()
    supabase.table("save_slots").upsert({
        "player_name": player_name,
        "run_state": run_state,
        "updated_at": "now()"
    }).execute()

def load_player_run(player_name: str):
    supabase = get_supabase()
    response = supabase.table("save_slots").select("run_state").eq("player_name", player_name).execute()
    data = response.data
    return data[0]["run_state"] if data else None

def submit_to_leaderboard(player_name: str, run_state: dict):
    supabase = get_supabase()
    score = run_state.get("room", 0) + run_state.get("gold", 0)
    supabase.table("leaderboard").upsert({
        "player_name": player_name,
        "class": run_state.get("class"),
        "score": score,
        "run_data": run_state,
        "submitted_at": "now()"
    }).execute()

# ====================== ROUTES ======================
@app.get("/")
def index():
    return render_template("game.html")

@app.get("/game")
def game_page():
    return render_template("game.html")

# API - Get current state
@app.get("/api/game/state")
def get_state():
    player_name = request.args.get("player_name")
    run_state = load_player_run(player_name)
    if not run_state:
        return jsonify({"has_run": False})
    return jsonify(state_for_client(run_state))

# API - Start new run
@app.post("/api/game/new-run")
def new_run():
    data = request.get_json()
    player_name = data.get("player_name")
    hero_class = data.get("heroClass")
    if not player_name or hero_class not in {"mage", "warrior", "rogue"}:
        return jsonify({"error": "Invalid player or class"}), 400
    run_state = create_new_run(hero_class)
    save_player_run(player_name, run_state)
    return jsonify(state_for_client(run_state))

# API - Fight
@app.post("/api/game/fight")
def fight():
    data = request.get_json()
    player_name = data.get("player_name")
    action = data.get("action", "attack")
    run_state = load_player_run(player_name)
    if not run_state:
        return jsonify({"error": "No active run"}), 400
    run_state = resolve_battle(run_state, action)
    save_player_run(player_name, run_state)
    return jsonify(state_for_client(run_state))

# API - Reward choice
@app.post("/api/game/reward")
def reward():
    data = request.get_json()
    player_name = data.get("player_name")
    choice = data.get("choice")
    run_state = load_player_run(player_name)
    if not run_state:
        return jsonify({"error": "No active run"}), 400
    run_state = choose_reward(run_state, choice)
    save_player_run(player_name, run_state)
    return jsonify(state_for_client(run_state))

# API - Gear choice
@app.post("/api/game/gear")
def gear():
    data = request.get_json()
    player_name = data.get("player_name")
    choice = data.get("choice")
    run_state = load_player_run(player_name)
    if not run_state:
        return jsonify({"error": "No active run"}), 400
    run_state = handle_gear_choice(run_state, choice)
    save_player_run(player_name, run_state)
    return jsonify(state_for_client(run_state))

# API - Shop
@app.post("/api/game/shop")
def shop():
    data = request.get_json()
    player_name = data.get("player_name")
    action = data.get("action")
    run_state = load_player_run(player_name)
    if not run_state:
        return jsonify({"error": "No active run"}), 400
    run_state = shop_action(run_state, action)
    save_player_run(player_name, run_state)
    return jsonify(state_for_client(run_state))

# API - Submit to leaderboard
@app.post("/api/run/submit")
def submit_run():
    data = request.get_json()
    player_name = data.get("player_name")
    run_state = load_player_run(player_name)
    if run_state:
        submit_to_leaderboard(player_name, run_state)
        return jsonify({"success": True, "message": "Run submitted to leaderboard!"})
    return jsonify({"error": "No run to submit"}), 400

# API - Reset run
@app.post("/api/game/reset")
def reset_run():
    data = request.get_json()
    player_name = data.get("player_name")
    if player_name:
        supabase = get_supabase()
        supabase.table("save_slots").update({"run_state": None}).eq("player_name", player_name).execute()
        return jsonify({"success": True})
    return jsonify({"error": "player_name required"}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)