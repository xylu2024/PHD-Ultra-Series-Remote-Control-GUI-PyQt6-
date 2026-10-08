# -*- coding: utf-8 -*-
"""
Tests for serial commands json database.
"""

import json
import os
import unittest


class TestCommandsDatabase(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.commands_path = os.path.join(self.base_dir, "json", "commands.json")

    def test_commands_json_exists_and_valid(self):
        self.assertTrue(os.path.exists(self.commands_path))
        with open(self.commands_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn("Commands", data)
        commands = data["Commands"]

        # Ensure major sections exist
        self.assertIn("System commands", commands)
        self.assertIn("Run commands quickstart mode", commands)
        self.assertIn("Rate commands", commands)
        self.assertIn("Volume commands", commands)
        self.assertIn("Time commands", commands)

    def test_crucial_pump_commands_present(self):
        with open(self.commands_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        run_cmds = data["Commands"]["Run commands quickstart mode"]
        self.assertEqual(run_cmds.get("Run infuse direction"), "irun")
        self.assertEqual(run_cmds.get("Run withdraw direction"), "wrun")
        self.assertEqual(run_cmds.get("Stop"), "stop")


if __name__ == "__main__":
    unittest.main()
