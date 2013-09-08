# No shebang line, this module is meant to be imported
#
# Copyright 2013 Oliver Palmer
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import with_statement

import sys

if sys.version_info[0:2] < (2, 7):
    from unittest2 import TestCase
else:
    from unittest import TestCase

from pyfarm.core.config import Config, cfg as _cfg


class TestConfig(TestCase):
    def test_type(self):
        self.assertIsInstance(_cfg, Config)

    def test_items(self):
        cfg = Config()
        cfg.update({"true": True, "false": False})

        items = {}
        for key, value in cfg.items():
            items[key] = value

        self.assertEqual(items, {"true": True, "false": False})

    def test_get(self):
        cfg = Config()
        cfg.set("foo", True)
        self.assertEqual(cfg.get("foo"), True)
        self.assertEqual(cfg.get("bar", False), False)

    def test_get_error(self):
        with self.assertRaises(KeyError):
            Config().get("foo")

    def test_contains(self):
        self.assertIn("foo", Config({"foo": True}))

    def test_set(self):
        cfg = Config()
        cfg.set("foo", True)
        self.assertEqual(cfg.get("foo"), True)
        cfg.set("foo", False)
        self.assertEqual(cfg.get("foo"), False)

    def test_setdefault(self):
        cfg = Config()
        self.assertEqual(cfg.setdefault("foo", True), True)
        self.assertEqual(cfg.setdefault("foo", False), True)

    def test_update_error(self):
        cfg = Config()
        with self.assertRaises(AssertionError):
            cfg.update(None)

    def test_iter(self):
        data = {"true": True, "false": False}
        cfg = Config(data)
        self.assertEqual(
            set(key for key in cfg), set(data.keys()))