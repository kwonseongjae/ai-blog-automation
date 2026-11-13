import unittest

from labs.learning_basics import LABS, run_lab


class LearningLabTests(unittest.TestCase):
    def test_each_published_example_checks_normal_and_failure_cases(self):
        self.assertEqual(len(LABS), 7)
        for name in LABS:
            with self.subTest(name=name):
                result = run_lab(name)
                self.assertGreaterEqual(len(result), 2)
                self.assertTrue(all(isinstance(x, str) and x for x in result))

    def test_unknown_example_is_rejected(self):
        with self.assertRaises(ValueError):
            run_lab('../shell')


if __name__ == '__main__':
    unittest.main()
