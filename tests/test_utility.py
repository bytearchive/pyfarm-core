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

import re
import math

try:
    _range = xrange
except NameError:
    _range = range

from nose.tools import raises
from utcore import TestCase
from pyfarm.utility import floatrange, convert, randstr, randint, rounded

RAND_TEST_COUNT = 75000


class Convert(TestCase):
    def test_convert_bytetomb(self):
        self.assertEqual(convert.bytetomb(10485760), 10.0)
        self.assertEqual(convert.bytetomb(11010048), 10.5)

    def test_convert_mbtogb(self):
        self.assertEqual(convert.mbtogb(2048), 2.0)
        self.assertEqual(convert.mbtogb(4608), 4.5)


class Random(TestCase):
    def test_randstr(self):
        generated = set()
        regex = re.compile("^[a-f0-9]{12}$")
        for i in xrange(RAND_TEST_COUNT):
            value = randstr()
            self.assertEqual(value not in generated, True)
            self.assertEqual(regex.match(value) is not None, True)

    def test_randint(self):
        generated = set()
        for i in xrange(RAND_TEST_COUNT):
            value = randint()
            self.assertEqual(value < 281474976710655 and value >= 0, True)
            self.assertEqual(value not in generated, True)
            generated.add(value)


class Rounding(TestCase):
    def test_rounded(self):
        self.assertEqual(rounded(math.pi), 3.1416)
        self.assertEqual(rounded(math.pi, 2), 3.14)
        self.assertEqual(rounded(math.pi, 6), 3.141593)

    @raises(TypeError)
    def test_rounded_places_type_error(self):
        rounded(1.5, None)


class Range(TestCase):
    @raises(ValueError)
    def test_range_end_error(self):
        floatrange(2, 1)

    @raises(ValueError)
    def test_range_by_error(self):
        with self.assertRaises(ValueErrr):
            floatrange(5, by=0)

    def test_intrange_start(self):
        self.assertEqual(list(floatrange(5)), list(_range(5)))

    def test_intrangestartby(self):
        self.assertEqual(list(floatrange(5, by=1)), [0, 1, 2, 3, 4])
        self.assertEqual(list(floatrange(5, by=2)), [0, 2, 4])

    def test_intrange_startendby(self):
        self.assertEqual(list(floatrange(1, 1, 1)), list(_range(1, 1, 1)))
        self.assertEqual(list(floatrange(1, 10, 1)), list(_range(1, 10, 1)))
        self.assertEqual(list(floatrange(1, 10, 2)), list(_range(1, 10, 2)))

    def test_floatrange_startby(self):
        self.assertEqual(
            list(floatrange(2.25, by=.25)),
            [0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25])
        self.assertEqual(list(floatrange(2, by=.25)),
            [0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0])
        self.assertEqual(list(floatrange(2, by=.75)), [0, 0.75, 1.5])
        self.assertEqual(list(floatrange(2, by=.75, add_endpoint=True)),
            [0, 0.75, 1.5, 2.0])
        self.assertEqual(list(floatrange(2.5, by=.15)),
            [0, 0.15, 0.3, 0.45, 0.6, 0.75, 0.9, 1.05, 1.2, 1.35, 1.5,
             1.65, 1.8, 1.95, 2.1, 2.25, 2.4])

    def test_floatrange_start(self):
        self.assertEqual(list(list(floatrange(2.25))), [0, 1, 2])
        self.assertEqual(list(list(floatrange(2.25, add_endpoint=True))),
                         [0, 1, 2, 2.25])

    def test_floatrange_startend(self):
        self.assertEqual(list(floatrange(2.25, 5)), [2.25, 3.25, 4.25])
        self.assertEqual(list(floatrange(2.25, 5, add_endpoint=True)),
                         [2.25, 3.25, 4.25, 5])

    def test_floatrange_startendby(self):
        self.assertEqual(list(floatrange(1.5, 2.5, .15)),
            [1.5, 1.65, 1.8, 1.95, 2.1, 2.25, 2.4])
        self.assertEqual(list(floatrange(1.5, 2.5, .15, add_endpoint=True)),
            [1.5, 1.65, 1.8, 1.95, 2.1, 2.25, 2.4, 2.5])