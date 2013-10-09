#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2012 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function

import mox
import os
import sys
import unittest


# pylint: disable=W0212
if __name__ == '__main__':
  sys.path.insert(0, os.path.join(os.path.dirname(sys.argv[0]), '..', '..'))

pre_upload = __import__('pre-upload')


class TryUTF8DecodeTest(unittest.TestCase):
  def runTest(self):
    self.assertEquals(u'', pre_upload._try_utf8_decode(''))
    self.assertEquals(u'abc', pre_upload._try_utf8_decode('abc'))
    self.assertEquals(u'你好布萊恩', pre_upload._try_utf8_decode('你好布萊恩'))
    # Invalid UTF-8
    self.assertEquals('\x80', pre_upload._try_utf8_decode('\x80'))


class CheckNoLongLinesTest(unittest.TestCase):
  def setUp(self):
    self.mocker = mox.Mox()
    self.mocker.StubOutWithMock(pre_upload, '_filter_files')
    self.mocker.StubOutWithMock(pre_upload, '_get_affected_files')
    self.mocker.StubOutWithMock(pre_upload, '_get_file_diff')
    pre_upload._get_affected_files(mox.IgnoreArg()).AndReturn(['x.py'])
    pre_upload._filter_files(
        ['x.py'], mox.IgnoreArg(), mox.IgnoreArg()).AndReturn(['x.py'])

  def tearDown(self):
    self.mocker.UnsetStubs()
    self.mocker.VerifyAll()

  def runTest(self):
    pre_upload._get_file_diff(mox.IgnoreArg(), mox.IgnoreArg()).AndReturn(
        [(1, u"x" * 80),                      # OK
         (2, "\x80" * 80),                    # OK
         (3, u"x" * 81),                      # Too long
         (4, "\x80" * 81),                    # Too long
         (5, u"See http://" + (u"x" * 80)),   # OK (URL)
         (6, u"See https://" + (u"x" * 80)),  # OK (URL)
         (7, u"#  define " + (u"x" * 80)),    # OK (compiler directive)
         (8, u"#define" + (u"x" * 74)),       # Too long
         ])
    self.mocker.ReplayAll()
    failure = pre_upload._check_no_long_lines('PROJECT', 'COMMIT')
    self.assertTrue(failure)
    self.assertEquals('Found lines longer than 80 characters (first 5 shown):',
                      failure.msg)
    self.assertEquals(['x.py, line %d, 81 chars' % line
                       for line in [3, 4, 8]],
                      failure.items)

class CheckKernelConfig(unittest.TestCase):
  def tearDown(self):
    self.mocker.UnsetStubs()

  def runTest(self):
    self.mocker = mox.Mox();

    # Mixed changes, should fail
    self.mocker.StubOutWithMock(pre_upload, '_get_affected_files')
    pre_upload._get_affected_files(mox.IgnoreArg()).AndReturn(
        ['/kernel/files/chromeos/config/base.config',
         '/kernel/files/arch/arm/mach-exynos/mach-exynos5-dt.c'
        ])
    self.mocker.ReplayAll()
    failure = pre_upload._kernel_configcheck('PROJECT', 'COMMIT')
    self.assertTrue(failure)

    # Code-only changes, should pass
    self.mocker.UnsetStubs()
    self.mocker.StubOutWithMock(pre_upload, '_get_affected_files')
    pre_upload._get_affected_files(mox.IgnoreArg()).AndReturn(
        ['/kernel/files/Makefile',
         '/kernel/files/arch/arm/mach-exynos/mach-exynos5-dt.c'
        ])
    self.mocker.ReplayAll()
    failure = pre_upload._kernel_configcheck('PROJECT', 'COMMIT')
    self.assertFalse(failure)

    # Config-only changes, should pass
    self.mocker.UnsetStubs()
    self.mocker.StubOutWithMock(pre_upload, '_get_affected_files')
    pre_upload._get_affected_files(mox.IgnoreArg()).AndReturn(
        ['/kernel/files/chromeos/config/base.config',
        ])
    self.mocker.ReplayAll()
    failure = pre_upload._kernel_configcheck('PROJECT', 'COMMIT')
    self.assertFalse(failure)


if __name__ == '__main__':
  unittest.main()
