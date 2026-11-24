import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from automation.learning_blog import record_publication

ENTRY = {'id': 'a', 'title': '제목', 'url': 'https://jacks-aiblog.tistory.com/14', 'date': '2026-11-25'}


def git(cwd, *args):
    return subprocess.check_output(['git', *args], cwd=cwd, text=True).strip()


class PublicationLogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.remote, self.work = base / 'remote.git', base / 'work'
        git(base, 'init', '--bare', '-b', 'main', str(self.remote))
        git(base, 'clone', str(self.remote), str(self.work))
        git(self.work, 'checkout', '-b', 'main')
        (self.work / 'docs/posts').mkdir(parents=True)
        (self.work / 'docs/posts/x.md').write_text('x')
        git(self.work, 'add', '.')
        git(self.work, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-m', 'init')
        git(self.work, 'push', 'origin', 'HEAD:main')

    def tearDown(self):
        self.tmp.cleanup()

    def test_records_commits_and_pushes(self):
        record_publication(self.work, ENTRY)
        log = json.loads((self.work / 'docs/posts/publication-log.json').read_text())
        self.assertEqual(log, [ENTRY])
        self.assertEqual(git(self.work, 'rev-parse', 'HEAD'), git(self.work, 'ls-remote', 'origin', 'refs/heads/main').split()[0])
        self.assertEqual(git(self.work, 'status', '--porcelain'), '')

    def test_same_url_is_not_recorded_twice(self):
        record_publication(self.work, ENTRY)
        head = git(self.work, 'rev-parse', 'HEAD')
        record_publication(self.work, ENTRY)
        self.assertEqual(git(self.work, 'rev-parse', 'HEAD'), head)


if __name__ == '__main__':
    unittest.main()
