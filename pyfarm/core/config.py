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

"""
Configuration Object
====================

Basic module used for reading configuration data into PyFarm
in various forms.

:const BOOLEAN_TRUE:
    set of values which will return a True boolean value from
    :func:`.read_env_bool`

:const BOOLEAN_FALSE:
    set of values which will return a False boolean value from
    :func:`.read_env_bool`

:const NOTSET:
    instanced :class:`object` which is returned when no data was found and
    no default was provided
"""

import os
from ast import literal_eval
from functools import partial
from itertools import product
from pprint import pformat
from os.path import isfile, join, isdir

try:
    from StringIO import StringIO
except ImportError:  # pragma: no cover
    from io import StringIO

import yaml
try:
    from yaml.loader import CLoader as Loader
except ImportError:  # pragma: no cover
    from yaml.loader import Loader

from pyfarm.core.logger import getLogger
from pyfarm.core.enums import (
    STRING_TYPES, NUMERIC_TYPES, NOTSET, LINUX, MAC, WINDOWS)

logger = getLogger("core.config")

# Boolean values as strings that can match a value we
# pulled from the environment after calling .lower().
BOOLEAN_TRUE = set(["1", "t", "y", "true", "yes"])
BOOLEAN_FALSE = set(["0", "f", "n", "false", "no"])


def read_env(envvar, default=NOTSET, warn_if_unset=False, eval_literal=False,
             raise_eval_exception=True, log_result=True, desc=None):
    """
    Lookup and evaluate an environment variable.

    :param string envvar:
        The environment variable to lookup in :class:`os.environ`

    :keyword object default:
        Alternate value to return if ``envvar`` is not present.  If this
        is instead set to ``NOTSET`` then an exception will be raised if
        ``envvar`` is not found.

    :keyword bool warn_if_unset:
        If True, log a warning if the value being returned is the same
        as ``default``

    :keyword eval_literal:
        if True, run :func:`.literal_eval` on the value retrieved
        from the environment

    :keyword bool raise_eval_exception:
        If True and we failed to parse ``envvar`` with :func:`.literal_eval`
        then raise a :class:`EnvironmentKeyError`

    :keyword bool log_result:
        If True, log the query and result to INFO.  If False, only log the
        query itself to DEBUG.  This keyword mainly exists so environment
        variables such as :envvar:`PYFARM_SECRET` or
        :envvar:`PYFARM_DATABASE_URI` stay out of log files.

    :keyword string desc:
        Describes the purpose of the value being returned.  This may also
        be read in at the time the documentation is built.
    """
    if not log_result:  # pragma: no cover
        logger.debug("read_env(%s)" % repr(envvar))

    if envvar not in os.environ:
        # default not provided, raise an exception
        if default is NOTSET:
            raise EnvironmentError("$%s is not in the environment" % envvar)

        if warn_if_unset:  # pragma: no cover
            logger.warning("$%s is using a default value" % envvar)

        if log_result:  # pragma: no cover
            logger.info("read_env(%s): %s" % (repr(envvar), repr(default)))

        return default
    else:
        value = os.environ[envvar]

        if not eval_literal:
            return value

        try:
            return literal_eval(value)

        except (ValueError, SyntaxError) as e:
            if raise_eval_exception:
                raise

            args = (envvar, e)
            logger.error(
                "$%s contains a value which could not be parsed: %s" % args)
            logger.warning("returning default value for $%s" % envvar)
            return default


def read_env_bool(*args, **kwargs):
    """
    Wrapper around :func:`.read_env` which converts environment variables
    to boolean values.  Please see the documentation for
    :func:`.read_env` for additional information on exceptions and input
    arguments.

    :exception AssertionError:
        raised if a default value is not provided

    :exception TypeError:
        raised if the environment variable found was a string and could
        not be converted to a boolean.
    """
    notset = object()

    if len(args) == 1:
        kwargs.setdefault("default", notset)

    kwargs["eval_literal"] = False  # we'll handle this ourselves here
    value = read_env(*args, **kwargs)
    assert value is not notset, "default value required for `read_env_bool`"

    if isinstance(value, STRING_TYPES):
        value = value.lower()

        if value in BOOLEAN_TRUE:
            return True

        elif value in BOOLEAN_FALSE:
            return False

        else:
            raise TypeError(
                "could not convert %s to a boolean from $%s" % (
                    repr(value), args[0]))

    if not isinstance(value, bool):
        raise TypeError("expected a boolean default value for `read_env_bool`")

    return value


def read_env_number(*args, **kwargs):
    """
    Wrapper around :func:`.read_env` which will read a numerical value
    from an environment variable.  Please see the documentation for
    :func:`.read_env` for additional information on exceptions and input
    arguments.

    :exception TypeError:
        raised if we either failed to convert the value from the environment
        variable or the value was not a float, integer, or long
    """

    if len(args) == 1:
        kwargs.setdefault("default", NOTSET)

    kwargs["eval_literal"] = True
    try:
        value = read_env(*args, **kwargs)
    except ValueError:
        raise ValueError("failed to evaluate the data in $%s" % args[0])

    assert value is not NOTSET, "default value required for `read_env_number`"

    if not isinstance(value, NUMERIC_TYPES):
        raise TypeError("`read_env_number` did not return a number type object")

    return value


def read_env_strict_number(*args, **kwargs):
    """
    Strict version of :func:`.read_env_number` which will only return an integer

    :keyword number_type:
        the type of number(s) this function must return

    :exception AsssertionError:
        raised if the number_type keyword is not provided (required to check
        the type on output)

    :exception TypeError:
        raised if the type of the result is not an instance of `number_type`
    """
    number_type = kwargs.pop("number_type", None)
    assert number_type is not None, "`number_type` keyword is required for"
    value = read_env_number(*args, **kwargs)

    if not isinstance(value, number_type):
        raise TypeError("%s is not an %s object" % (repr(value), number_type))

    return value


read_env_int = partial(read_env_strict_number, number_type=int)
read_env_float = partial(read_env_strict_number, number_type=float)


class Configuration(dict):
    """
    Main object responsible for finding, loading, and
    merging configuration data.

    :param string version:
        The version the version of the program running.

    """
    if LINUX:
        DEFAULT_CONFIG_ROOT = join(os.sep, "etc")
    elif MAC:
        DEFAULT_CONFIG_ROOT = join(os.sep, "Library")
    elif WINDOWS:
        DEFAULT_CONFIG_ROOT = os.environ["APPDATA"]
    else:
        logger.warning("Failed to determine default configuration root")
        DEFAULT_CONFIG_ROOT = None

    FILE_EXTENSION = ".yml"
    LOCAL_DIRECTORY_NAME = "etc"
    PARENT_APPLICATION_NAME = "pyfarm"
    ENVIRONMENT_PATH_VARIABLE = "PYFARM_CONFIG_ROOT"

    def __init__(self, service_name, version):
        super(Configuration, self).__init__()
        self.service_name = service_name
        self.version = version
        self.system_root = self.DEFAULT_CONFIG_ROOT
        self.child_dir = join(self.PARENT_APPLICATION_NAME, self.service_name)
        self.environment_root = read_env(self.ENVIRONMENT_PATH_VARIABLE, None)

        if isdir(self.LOCAL_DIRECTORY_NAME):
            self.local_dir = self.LOCAL_DIRECTORY_NAME
        else:
            self.local_dir = None

    def split_version(self, sep="."):
        """
        Splits ``self.version`` into a tuple of individual versions.  For
        example ``1.2.3`` would be split into ``['1', '1.2', '1.2.3']``
        """
        if self.version is None:
            return []

        split = self.version.split(sep)
        return [
            sep.join(split[:index]) for index, _ in enumerate(split, start=1)]

    def directories(self, filter_missing=True):
        """
        Returns a list of platform dependent directories which may contain
        configuration files.

        :param bool filter_missing:
            If True then only return directories which exist
        """
        results = []
        roots = []
        versions = self.split_version(self.version)
        versions.insert(0, "")  # the 'version free' directory

        # If provided, insert the default root
        if self.system_root is not None:
            roots.append(join(self.system_root, self.child_dir))

        # If provided, append the root discovered in the environment
        if self.environment_root is not None:
            roots.append(join(self.environment_root, self.child_dir))

        # If provided append a local directory
        if self.local_dir is not None:
            roots.append(join(self.local_dir, self.child_dir))

        paths = [join(root, tail) for root, tail in product(roots, versions)]
        for path in paths:
            if filter_missing and isdir(path) or not filter_missing:
                results.append(path)

        if results:
            logger.debug(
                "Found %s configuration directories: %s",
                len(results), pformat(results))

        return results

    def files(self, filter_missing=True):
        """
        Returns a list of configuration files.

        :param bool filter_missing:
            If True only return files which exist.
        """
        directories = self.directories(filter_missing=filter_missing)
        if not directories:
            logger.error("No configuration directories found.")
            return []

        filename = self.service_name + self.FILE_EXTENSION
        filepaths = [join(directory, filename) for directory in directories]
        filterer = lambda _: True if not filter_missing else isfile
        filtered_paths = list(filter(filterer, filepaths))

        if not filtered_paths:
            logger.error("No configuration files found.")

        return filtered_paths

    def load(self, environment=os.environ):
        """Loads data from the configuration files"""
        for filepath in self.files():
            logger.debug("Reading %s", filepath)

            with open(filepath, "rb") as stream:
                data = yaml.load(stream, Loader=Loader)

            if environment is not None and "env" in data:
                config_environment = data.pop("env")
                assert isinstance(config_environment, dict)
                environment.update(config_environment)

            self.update(data)
