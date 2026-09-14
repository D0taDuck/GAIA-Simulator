import json
import threading
import time
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from gaia.engine import Simulation
from gaia.server import GaiaServer


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.server = GaiaServer(("127.0.0.1", 0), Simulation())
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def command(self, action, token=None, **extra):
        data = json.dumps(dict(action=action, **extra)).encode()
        req = Request(self.url + "/api/control", data=data, headers={"Content-Type": "application/json",
                       "X-Gaia-Token": self.server.token if token is None else token})
        with urlopen(req, timeout=5) as response:
            return json.load(response)

    def test_pause_step_save_restore_and_reset(self):
        result = self.command("step", ticks=17)
        self.assertEqual(result["current"]["tick"], 17)
        with urlopen(self.url + "/api/export/checkpoint") as response:
            saved = json.load(response)
        self.command("step", ticks=12)
        result = self.command("restore", checkpoint=saved)
        self.assertEqual(result["current"]["tick"], 17)
        result = self.command("reset", config={"seed": 12, "mode": "off"})
        self.assertEqual(result["current"]["tick"], 0)
        self.assertEqual(result["config"]["seed"], 12)

    def test_scheduled_event_and_end_unlock_csv_export(self):
        result = self.command("schedule_event", event={"kind": "rainfall", "magnitude": 100, "at_tick": 2})
        self.assertEqual(result["scheduled_events"][0]["kind"], "rainfall")
        result = self.command("step", ticks=2)
        self.assertGreater(result["current"]["reservoir"], 3000)
        with self.assertRaises(HTTPError) as exc:
            urlopen(self.url + "/api/export/csv")
        self.assertEqual(exc.exception.code, 409)
        result = self.command("end")
        self.assertTrue(result["ended"])
        with urlopen(self.url + "/api/export/csv") as response:
            self.assertEqual(response.status, 200)
        with self.assertRaises(HTTPError) as exc:
            self.command("step")
        self.assertEqual(exc.exception.code, 400)

    def test_running_clock_can_pause_and_shut_down(self):
        self.command("start")
        deadline = time.monotonic() + 2
        while self.server.controller.sim.world.tick == 0 and time.monotonic() < deadline:
            time.sleep(0.02)
        paused = self.command("pause")
        self.assertGreater(paused["current"]["tick"], 0)
        time.sleep(0.15)
        self.assertEqual(paused["current"]["tick"], self.server.controller.sim.world.tick)
        self.server.controller.close()
        self.assertFalse(self.server.controller.thread.is_alive())

    def test_invalid_commands_do_not_replace_world(self):
        with self.assertRaises(HTTPError) as exc:
            self.command("reset", config={"initial_population": -2})
        self.assertEqual(exc.exception.code, 400)
        self.assertEqual(len(self.server.controller.sim.population), 36)
        with self.assertRaises(HTTPError) as exc:
            self.command("start", token="wrong")
        self.assertEqual(exc.exception.code, 403)

    def test_html_state_and_exports(self):
        for route in ("/", "/api/state", "/api/export/report"):
            with self.subTest(route=route), urlopen(self.url + route) as response:
                self.assertEqual(response.status, 200)
                self.assertGreater(len(response.read()), 50)


if __name__ == "__main__":
    unittest.main()
