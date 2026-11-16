import json
import unittest
from pathlib import Path

from automation.learning_blog import validate_catalogue
from scripts.prepare_learning_posts import merge_catalogue

ROOT = Path(__file__).resolve().parents[1]
ARCHIVED = {'python-json-boundary', 'python-atomic-state', 'python-request-id',
            'python-subprocess-timeout', 'python-url-target'}


def load(name):
    return json.loads((ROOT / 'docs/posts' / name).read_text(encoding='utf-8'))


class CatalogueTests(unittest.TestCase):
    def test_merge_skips_archived(self):
        existing = [{'id': 'a'}]
        generated = {'a': {'title': 'A'}, 'b': {'id': 'b'}, 'old': {'id': 'old'}}
        result = merge_catalogue(existing, generated, {'old'})
        self.assertEqual([e['id'] for e in result], ['a', 'b'])
        self.assertEqual(result[0]['title'], 'A')

    def test_catalogue_order_and_validity(self):
        catalogue = load('catalogue.json')
        ids = [e['id'] for e in catalogue]
        self.assertEqual(ids[:3], ['python-kst-date', 'python-path-base', 'ai-agent-first-task'])
        self.assertEqual(ids[-1], 'dark-mode-contrast-guide')
        self.assertEqual(len(ids), 17)
        validate_catalogue(catalogue, ROOT)

    def test_related_posts_are_published_earlier(self):
        # 발행기는 아직 발행하지 않은 글을 관련 글로 연결하면 멈추므로 항상 앞선 순서여야 한다.
        order = [e['id'] for e in load('catalogue.json')]
        for index, entry in enumerate(load('catalogue.json')):
            for related in entry.get('related', []):
                self.assertIn(related, order[:index], f"{entry['id']}의 관련 글 {related}이 뒤에 있다")

    def test_archive_not_in_catalogue(self):
        self.assertEqual({e['id'] for e in load('archive.json')}, ARCHIVED)
        self.assertFalse(ARCHIVED & {e['id'] for e in load('catalogue.json')})


if __name__ == '__main__':
    unittest.main()
