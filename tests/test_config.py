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

import os
import tempfile
import uuid
from textwrap import dedent
from os.path import join, dirname, expandvars, expanduser

from pkg_resources import get_distribution

from pyfarm.core.enums import PY26, LINUX, MAC, WINDOWS
from pyfarm.core.testutil import TestCase as BaseTestCase, requires_ci

if PY26:
    from unittest2 import TestCase, skipIf
else:
    from unittest import TestCase, skipIf

from pyfarm.core.config import (
    read_env, read_env_number, read_env_bool, read_env_strict_number,
    BOOLEAN_FALSE, BOOLEAN_TRUE, Configuration)


class TestConfigEnvironment(TestCase):
    def test_readenv_missing(self):
        key = uuid.uuid4().hex
        with self.assertRaises(EnvironmentError):
            read_env(key)
        self.assertEqual(read_env(key, 42), 42)

    def test_readenv_exists(self):
        key = uuid.uuid4().hex
        value = uuid.uuid4().hex
        os.environ[key] = value
        self.assertEqual(read_env(key), value)
        del os.environ[key]

    def test_readenv_eval(self):
        key = uuid.uuid4().hex

        for value in (True, False, 42, 3.141, None, [1, 2, 3]):
            os.environ[key] = str(value)
            self.assertEqual(read_env(key, eval_literal=True), value)

        os.environ[key] = "f"
        with self.assertRaises(ValueError):
            read_env(key, eval_literal=True)

        self.assertEqual(
            read_env(key, 42, eval_literal=True, raise_eval_exception=False),
            42)

        del os.environ[key]

    def test_read_env_bool(self):
        for true in BOOLEAN_TRUE:
            key = uuid.uuid4().hex
            os.environ[key] = true
            self.assertTrue(read_env_bool(key, False))

        for false in BOOLEAN_FALSE:
            key = uuid.uuid4().hex
            os.environ[key] = false
            self.assertFalse(read_env_bool(key, True))

        with self.assertRaises(AssertionError):
            read_env_bool("")

        with self.assertRaises(TypeError):
            key = uuid.uuid4().hex
            os.environ[key] = "42"
            read_env_bool(key, 1)

        with self.assertRaises(TypeError):
            key = uuid.uuid4().hex
            self.assertTrue(read_env_bool(key, 1))

        key = uuid.uuid4().hex
        self.assertTrue(read_env_bool(key, True))

    def test_read_env_number(self):
        key = uuid.uuid4().hex
        os.environ[key] = "42"
        self.assertEqual(read_env_number(key), 42)
        key = uuid.uuid4().hex
        os.environ[key] = "3.14159"
        self.assertEqual(read_env_number(key), 3.14159)

        key = uuid.uuid4().hex
        os.environ[key] = "foo"
        with self.assertRaises(ValueError):
            self.assertEqual(read_env_number(key))

        key = uuid.uuid4().hex
        os.environ[key] = "None"
        with self.assertRaises(TypeError):
            self.assertEqual(read_env_number(key))

    def test_read_env_strict_number(self):
        with self.assertRaises(AssertionError):
            read_env_strict_number("")

        key = uuid.uuid4().hex
        os.environ[key] = "3.14159"
        self.assertEqual(read_env_strict_number(key, number_type=float),
                         3.14159)

        key = uuid.uuid4().hex
        os.environ[key] = "42"
        with self.assertRaises(TypeError):
            read_env_strict_number(key, number_type=float)


class TestConfiguration(BaseTestCase):
    def test_parent_class(self):
        self.assertIn(dict, Configuration.__bases__)

    def test_extension(self):
        self.assertEqual(Configuration.DEFAULT_FILE_EXTENSION, ".yml")

    def test_local_directory_name(self):
        self.assertEqual(Configuration.DEFAULT_LOCAL_DIRECTORY_NAME, "etc")

    def test_parent_application_name(self):
        self.assertEqual(
            Configuration.DEFAULT_PARENT_APPLICATION_NAME, "pyfarm")

    def test_environment_variable(self):
        self.assertEqual(
            Configuration.DEFAULT_ENVIRONMENT_PATH_VARIABLE,
            "PYFARM_CONFIG_ROOT")

    @skipIf(not LINUX, "not linux")
    def test_linux_system_root(self):
        self.assertEqual(
            Configuration.DEFAULT_SYSTEM_ROOT, join(os.sep, "etc"))

    @skipIf(not MAC, "not mac")
    def test_mac_system_root(self):
        self.assertEqual(
            Configuration.DEFAULT_SYSTEM_ROOT, join(os.sep, "Library"))

    @skipIf(not WINDOWS, "not windows")
    def test_windows_system_root(self):
        self.assertEqual(
            Configuration.DEFAULT_SYSTEM_ROOT, expandvars("$ProgramData"))

    @skipIf(not LINUX, "not linux")
    def test_linux_user_root(self):
        self.assertEqual(
            Configuration.DEFAULT_USER_ROOT, expanduser("~"))

    @skipIf(not MAC, "not mac")
    def test_mac_user_root(self):
        self.assertEqual(
            Configuration.DEFAULT_USER_ROOT, expanduser("~"))

    @skipIf(not WINDOWS, "not windows")
    def test_windows_user_root(self):
        self.assertEqual(
            Configuration.DEFAULT_USER_ROOT, expandvars("$APPDATA"))

    def test_instance_attributes(self):
        config = Configuration("agent", "1.2.3")
        self.assertIsNotNone(config.DEFAULT_SYSTEM_ROOT)
        self.assertEqual(config.name, "agent")
        self.assertEqual(config.version, "1.2.3")
        self.assertEqual(config.system_root, Configuration.DEFAULT_SYSTEM_ROOT)
        self.assertEqual(
            config.child_dir,
            join(config.DEFAULT_PARENT_APPLICATION_NAME, config.name))
        self.assertEqual(config.DEFAULT_FILE_EXTENSION, config.file_extension)
        if config.DEFAULT_ENVIRONMENT_PATH_VARIABLE not in os.environ:
            self.assertIsNone(config.environment_root)
        else:
            self.assertEqual(
                config.environment_root,
                join(config.cwd,
                     os.environ[config.DEFAULT_ENVIRONMENT_PATH_VARIABLE]))
        self.assertEqual(
            config.local_dir,
            join(config.cwd, config.DEFAULT_LOCAL_DIRECTORY_NAME))

    def test_split_version(self):
        config = Configuration("agent", "1.2.3")
        self.assertEqual(config.split_version(), ["1.2.3", "1.2", "1"])

    def test_split_empty_version(self):
        config = Configuration("agent", "")
        self.assertEqual(config.split_version(), [])

    def test_files_system_root(self):
        os.environ[Configuration.DEFAULT_ENVIRONMENT_PATH_VARIABLE] \
            = tempfile.mkdtemp()
        config = Configuration("agent", "1.2.3")
        os.environ.pop(Configuration.DEFAULT_ENVIRONMENT_PATH_VARIABLE)
        split = config.split_version()
        filename = config.name + config.file_extension
        all_paths = [
            join(config.system_root, config.child_dir, split[0], filename),
            join(config.system_root, config.child_dir, split[1], filename),
            join(config.system_root, config.child_dir, split[2], filename),
            join(config.system_root, config.child_dir + os.sep, filename),
            join(config.user_root, "." + config.child_dir, split[0], filename),
            join(config.user_root, "." + config.child_dir, split[1], filename),
            join(config.user_root, "." + config.child_dir, split[2], filename),
            join(config.user_root, "." + config.child_dir + os.sep, filename),
            join(config.local_dir, config.child_dir, split[0], filename),
            join(config.local_dir, config.child_dir, split[1], filename),
            join(config.local_dir, config.child_dir, split[2], filename),
            join(config.local_dir, config.child_dir + os.sep, filename),
            join(config.environment_root, config.child_dir, split[0], filename),
            join(config.environment_root, config.child_dir, split[1], filename),
            join(config.environment_root, config.child_dir, split[2], filename),
            join(config.environment_root, config.child_dir + os.sep, filename),
        ]
        self.assertEqual(config.files(validate=False), all_paths)

    def test_files_filtered_with_files(self):
        local_root = tempfile.mkdtemp()
        config = Configuration("agent", "1.2.3")
        config.system_root = local_root
        self.add_cleanup_path(local_root)
        split = config.split_version()
        filename = config.name + config.file_extension
        paths = [
            join(config.system_root, config.child_dir, split[2], filename),
            join(config.system_root, config.child_dir + os.sep, filename)
        ]

        for path in paths:
            try:
                os.makedirs(dirname(path))
            except OSError:
                pass

            with open(path, "w") as stream:
                self.add_cleanup_path(stream.name)

        self.assertEqual(config.files(), paths)

    def test_files_filtered_without_files(self):
        config = Configuration("agent", "1.2.3")
        self.assertEqual(config.files(), [])

    def test_load_basic(self):
        local_root = tempfile.mkdtemp()
        config = Configuration("agent", "1.2.3")
        config.system_root = local_root
        self.add_cleanup_path(local_root)
        split = config.split_version()
        filename = config.name + config.file_extension
        paths = [
            join(config.system_root, config.child_dir, split[2], filename),
            join(config.system_root, config.child_dir + os.sep, filename)
        ]

        for i, path in enumerate(paths):
            try:
                os.makedirs(dirname(path))
            except OSError:
                pass

            with open(path, "w") as stream:
                stream.write("value: %d" % i)
                self.add_cleanup_path(stream.name)

        config.load()
        self.assertEqual(config["value"], i)

    def test_load_empty_file(self):
        local_root = tempfile.mkdtemp()
        config = Configuration("agent", "1.2.3")
        config.system_root = local_root
        self.add_cleanup_path(local_root)
        split = config.split_version()
        filename = config.name + config.file_extension
        paths = [
            join(config.system_root, config.child_dir + os.sep, filename),
            join(config.system_root, config.child_dir, split[2], filename)]

        for i, path in enumerate(paths):
            try:
                os.makedirs(dirname(path))
            except OSError:
                pass

            with open(path, "w") as stream:
                stream.write("")
                self.add_cleanup_path(stream.name)

        config.load()

    def test_load_environment(self):
        local_root = tempfile.mkdtemp()
        config = Configuration("agent", "1.2.3")
        config.system_root = local_root
        self.add_cleanup_path(local_root)
        split = config.split_version()
        filename = config.name + config.file_extension
        paths = [
            join(config.system_root, config.child_dir, split[2], filename),
            join(config.system_root, config.child_dir + os.sep, filename)]

        for i, path in enumerate(paths):
            try:
                os.makedirs(dirname(path))
            except OSError:
                pass

            data = dedent("""
            env:
                key%s: %s
                key: %s
            """ % (i, i, i))

            with open(path, "w") as stream:
                stream.write(data)
                self.add_cleanup_path(stream.name)

        environment = {}
        config.load(environment=environment)
        self.assertEqual(environment, {"key0": 0, "key1": 1, "key": 1})

    def test_auto_version(self):
        distro = get_distribution("pyfarm.core")
        config = Configuration("pyfarm.core")
        self.assertEqual(config.distribution, distro)
        self.assertEqual(config.version, distro.version)
        self.assertEqual(config.name, "core")

    def test_auto_version_fail(self):
        with self.assertRaises(ValueError):
            Configuration("foobar")

    def test_tempdir(self):
        config = Configuration("pyfarm.core")
        self.assertEqual(
            config.tempdir,
            join(config.DEFAULT_TEMP_DIRECTORY_ROOT, config.name))

    def test_get_default_behavior(self):
        key = uuid.uuid4().hex
        config = Configuration("pyfarm.core")
        self.assertIsNone(config.get(key))

    def test_getitem_default_behavior(self):
        key = uuid.uuid4().hex
        config = Configuration("pyfarm.core")
        with self.assertRaises(KeyError):
            config[key]


class TestConfigurationExpansion(BaseTestCase):
    def test_temp_getitem(self):
        key = uuid.uuid4().hex
        config = Configuration("pyfarm.core")
        config[key] = "$temp/bar"
        self.assertEqual(config[key], config.tempdir + "/bar")

    def test_temp_get(self):
        key = uuid.uuid4().hex
        config = Configuration("pyfarm.core")
        config[key] = "$temp/bar"
        self.assertEqual(config.get(key), config.tempdir + "/bar")

    def test_recursive_expansion(self):
        envvar1 = "a" + uuid.uuid4().hex
        envvalue1 = "a" + uuid.uuid4().hex
        envvar2 = "b" + uuid.uuid4().hex
        envvalue2 = "b" + uuid.uuid4().hex
        os.environ[envvar1] = envvalue1
        os.environ[envvar2] = envvalue2
        config = Configuration("pyfarm.core")
        config.update(
            foo="foo", bar="bar", foobar="$foo/$bar",
            home="~/foo", path="$foobar/$%s" % envvar1,
            envvar2_expand="$%s" % envvar2)
        config.update({envvar2: "envvar2"})
        self.assertEqual(config["foobar"], "foo/bar")
        self.assertEqual(config["path"], "foo/bar/%s" % envvalue1)
        self.assertEqual(config["home"], expanduser("~/foo"))
        self.assertEqual(config["envvar2_expand"], "envvar2")
