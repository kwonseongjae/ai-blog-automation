import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from automation.learning_blog import BLOG, kst_day, publish_daily, render_markdown, resolve_pending, validate_article, validate_catalogue, validate_url


class LearningBlogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.now = datetime(2026, 11, 13, 12, 0, tzinfo=timezone.utc)
        self.article = {
            'id': 'timezone', 'title': '한국 날짜 기준으로 하루 한 번 실행하기',
            'category': 'Python·자동화', 'markdown': 'docs/posts/timezone.md',
            'lab': 'timezone', 'sources': ['https://docs.python.org/3/library/zoneinfo.html'],
        }
        self.source = self.root / 'docs/posts/timezone.md'
        self.source.parent.mkdir(parents=True)
        self.source.write_text('# 한국 날짜 기준으로 하루 한 번 실행하기\n\n'
                               '## 해결할 문제\n날짜 경계를 명시해야 합니다.\n\n'
                               '## 실행 코드\n```python\nprint("<hello>")\n```\n\n'
                               '## 확인 결과\n시간대를 지정합니다.\n\n'
                               '## 주의할 점\n실행 환경을 확인합니다.\n', encoding='utf-8')

    def publish(self, **kwargs):
        return publish_daily(self.root, [self.article], root=self.root,
                             publish=kwargs.pop('publish', lambda _: f'https://{BLOG}/2'),
                             verify=kwargs.pop('verify', lambda *_: True),
                             now=kwargs.pop('now', self.now), **kwargs)

    def test_kst_midnight_uses_local_date(self):
        self.assertEqual(kst_day(datetime(2026, 11, 12, 15, 1, tzinfo=timezone.utc)), '2026-11-13')
        with self.assertRaises(ValueError):
            kst_day(datetime(2026, 11, 13))

    def test_exact_target_only(self):
        self.assertEqual(validate_url(f'https://{BLOG}/12'), f'https://{BLOG}/12')
        for url in ['https://jack-0314.tistory.com/2', f'https://{BLOG}.evil.test/2',
                    f'http://{BLOG}/2', f'https://user@{BLOG}/2', f'https://{BLOG}/manage',
                    f'https://{BLOG}:444/2', f'https://{BLOG}/2?preview=1']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate_url(url)

    def test_markdown_escapes_code_and_rejects_active_html(self):
        html = render_markdown(self.source.read_text())
        self.assertIn('&lt;hello&gt;', html)
        self.assertIn('<pre><code', html)
        for source in ['<script>alert(1)</script>', '[x](javascript:alert(1))', '```python\nunterminated']:
            with self.subTest(source=source), self.assertRaises(ValueError):
                render_markdown(source)

    def test_untrusted_manifest_paths_and_categories_are_rejected(self):
        for change in [{'markdown': '../outside.md'}, {'category': '주식'},
                       {'id': '../other'}, {'sources': ['http://evil.test']}]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_article(self.article | change, self.root)

    def test_one_publication_per_kst_day(self):
        self.assertEqual(self.publish()['status'], 'published')
        self.assertEqual(self.publish()['status'], 'already_published')

    def test_pending_is_saved_before_call_and_blocks_next_day(self):
        def fail(_):
            state = json.loads((self.root / 'state.json').read_text())
            self.assertEqual(state['pending']['id'], 'timezone')
            raise RuntimeError('connection lost after submit')
        with self.assertRaises(RuntimeError):
            self.publish(publish=fail)
        result = self.publish(now=datetime(2026, 11, 14, 12, tzinfo=timezone.utc))
        self.assertEqual(result['status'], 'needs_confirmation')

    def test_wrong_returned_url_and_failed_verification_never_mark_success(self):
        for kwargs in [{'publish': lambda _: 'https://jack-0314.tistory.com/2'},
                       {'verify': lambda *_: False}]:
            with self.subTest(kwargs=kwargs):
                (self.root / 'state.json').unlink(missing_ok=True)
                with self.assertRaises((ValueError, RuntimeError)):
                    self.publish(**kwargs)
                state = json.loads((self.root / 'state.json').read_text())
                self.assertIsNotNone(state.get('pending'))
                self.assertEqual(state.get('posted', []), [])

    def test_corrupt_state_and_changed_source_fail_closed(self):
        (self.root / 'state.json').write_text('{broken')
        with self.assertRaises(ValueError):
            self.publish()

    def test_exhausted_inventory_does_not_republish(self):
        self.publish()
        result = self.publish(now=datetime(2026, 11, 14, 12, tzinfo=timezone.utc))
        self.assertEqual(result['status'], 'empty')

    def test_duplicate_id_path_and_body_are_rejected(self):
        for other in [self.article.copy(), self.article | {'id': 'alias'}]:
            with self.assertRaises(ValueError):
                validate_catalogue([self.article, other], self.root)
        self.publish()
        alias = self.article | {'id': 'alias'}
        with self.assertRaises(ValueError):
            publish_daily(self.root, [alias], root=self.root, publish=lambda _: self.fail('duplicate'),
                          verify=lambda *_: True, now=datetime(2026, 11, 14, 12, tzinfo=timezone.utc))

    def test_resolve_verifies_before_releasing_pending(self):
        with self.assertRaises(RuntimeError):
            self.publish(verify=lambda *_: False)
        with self.assertRaises(RuntimeError):
            resolve_pending(self.root, f'https://{BLOG}/2', verify=lambda *_: False, now=self.now)
        resolve_pending(self.root, f'https://{BLOG}/2', verify=lambda *_: True, now=self.now)
        self.assertEqual(self.publish()['status'], 'already_published')

    def test_clear_pending_never_discards_a_known_url(self):
        with self.assertRaises(RuntimeError):
            self.publish(verify=lambda *_: False)
        with self.assertRaises(ValueError):
            resolve_pending(self.root, clear=True, now=self.now)

    def test_explicit_clear_for_confirmed_nonpublication(self):
        with self.assertRaises(RuntimeError):
            self.publish(publish=lambda _: (_ for _ in ()).throw(RuntimeError('before submit')))
        resolve_pending(self.root, clear=True, now=self.now)
        self.assertEqual(self.publish()['status'], 'published')

    def test_dry_run_does_not_reserve_or_publish(self):
        result = self.publish(dry_run=True, publish=lambda _: self.fail('must not publish'))
        self.assertEqual(result['status'], 'ready')
        self.assertFalse((self.root / 'state.json').exists())


if __name__ == '__main__':
    unittest.main()
