import unittest

from fs.tests import FSTestCases, ThreadingTestCases


class TestPirannaFS(unittest.TestCase, FSTestCases, ThreadingTestCases):

    def setUp(self):
        self.fs = memoryfs.MemoryFS()
