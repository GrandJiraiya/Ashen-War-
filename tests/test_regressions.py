import unittest

import app as app_module
from game.logic import create_new_run, resolve_battle, state_for_client


class FakeResponse:
    def __init__(self, data):
        self.data = data


class FakeQuery:
    def __init__(self, table_name, db):
        self.table_name = table_name
        self.db = db
        self.filters = {}
        self.payload = None

    def select(self, *_args):
        return self

    def eq(self, key, value):
        self.filters[key] = value
        return self

    def limit(self, *_args):
        return self

    def upsert(self, payload, on_conflict=None):
        self.payload = payload
        key = payload.get(on_conflict or "player_name")
        self.db[self.table_name][key] = payload
        return self

    def delete(self):
        return self

    def execute(self):
        if self.payload is not None:
            return FakeResponse([self.payload])

        key = self.filters.get("player_name")
        if key is None:
            return FakeResponse([])

        row = self.db[self.table_name].get(key)
        if row is None:
            return FakeResponse([])

        if self.table_name == "save_slots":
            if self.payload is None and "run_state" in row:
                return FakeResponse([{"run_state": row["run_state"]}])

        return FakeResponse([row])


class FakeSupabase:
    def __init__(self):
        self.db = {"leaderboard": {}, "save_slots": {}}

    def table(self, name):
        return FakeQuery(name, self.db)


class RegressionTests(unittest.TestCase):
    def test_reward_flow_exposes_reward_options(self):
        state = create_new_run("mage")
        state["enemy"]["hp"] = 1

        next_state = resolve_battle(state, "attack")
        client_state = state_for_client(next_state)

        self.assertTrue(client_state["reward_pending"])
        self.assertIsInstance(client_state["reward_options"], list)
        self.assertEqual(client_state["gear_offer"], None)

    def test_submit_to_leaderboard_keeps_best_score(self):
        fake = FakeSupabase()
        app_module.get_supabase = lambda: fake

        better_run = {"player": {"room": 8, "gold": 150, "hero_class": "mage"}}
        worse_run = {"player": {"room": 3, "gold": 5, "hero_class": "mage"}}

        self.assertTrue(app_module.submit_to_leaderboard("Crash", better_run))
        self.assertFalse(app_module.submit_to_leaderboard("Crash", worse_run))

    def test_reset_endpoint_clears_cookie_run(self):
        fake = FakeSupabase()
        app_module.get_supabase = lambda: fake
        fake.db["save_slots"]["run-123"] = {"player_name": "run-123", "run_state": {"player": {"room": 2}}}

        client = app_module.app.test_client()
        with client.session_transaction() as sess:
            sess["run_id"] = "run-123"

        response = client.post("/api/game/reset", json={})
        self.assertEqual(response.status_code, 200)

        with client.session_transaction() as sess:
            self.assertIsNone(sess.get("run_id"))


if __name__ == "__main__":
    unittest.main()
