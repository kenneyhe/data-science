import unittest

class TestDummy(unittest.TestCase):
    def test_import(self):
        pass
    def test_failure(self):
        self.assert(False)
