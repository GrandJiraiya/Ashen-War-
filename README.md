# Ashen-War-
2.0 Ashen War rpg

# 🗡️ Ashen War

**Browser-based Idle Loot Dungeon Crawler RPG**

Swear your oath. Crawl the ashen ruins. Loot legendary gear. Fight bosses every 5th floor. Submit your best run to the global leaderboard.

**Live Game:** https://ashen-war-lite-6k9g7rhim-crash-out-crypto.vercel.app/game?player=YourName

---

## ✨ Features
- 3 classes (Mage, Warrior, Rogue)
- Auto-combat + manual decisions on loot, gear, and merchant
- Full cloud saves via Supabase
- Global leaderboard
- Responsive (works great on mobile)

---

## 🚀 Quick Start (Local)

```bash
pip install -r requirements.txt
python app.py

## Troubleshooting

If tapping a class gives an error like `The string did not match the expected pattern`, check these first:

- `SUPABASE_URL` must be the project API URL: `https://<project-ref>.supabase.co`
- Do **not** use the dashboard URL: `https://supabase.com/dashboard/project/<project-ref>`
- Set one of: `SUPABASE_KEY`, `SUPABASE_ANON_KEY`, or `SUPABASE_PUBLISHABLE_KEY`
- Make sure `save_slots.player_name` is unique if you are using `upsert(..., on_conflict="player_name")`


## Environment

Copy `.env.example` to `.env` and provide your Supabase credentials before running locally.
