import base64
import json
import tempfile
import unittest
import contextlib
import io
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from automation.learning_blog import publish_daily, render_markdown, validate_article
from automation.tistory_publisher import body_signature, new_image_url, verify


PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=')


class RichPostTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'guide.md').write_text('# 안내\n## 비교\n| A | B |\n| --- | --- |\n| 입력 | 결과 |\n\n![흐름](asset:flow)\n')
        (self.root / 'cover.png').write_bytes(PNG)
        self.article = {'id': 'agent-guide', 'kind': 'guide', 'title': '에이전트 첫 작업',
                        'category': 'AI 시작하기', 'markdown': 'guide.md', 'checked_on': '2026-11-15',
                        'verification': 'README 읽기 결과 대조. 새 설치는 수행하지 않음.',
                        'sources': ['https://learn.chatgpt.com/docs/working-with-agents.md',
                                    'https://code.claude.com/docs/en/permissions'],
                        'tags': ['AI 에이전트', 'AI 입문', '첫 작업'],
                        'assets': {'cover': 'cover.png', 'flow': 'cover.png'}}

    def test_guide_does_not_require_fake_lab_and_rejects_invalid_evidence_assets_sources(self):
        validate_article(self.article, self.root)
        for changes in [{'kind': 'unknown'}, {'checked_on': '2026-02-30'}, {'verification': ''},
                        {'assets': {'cover': '../outside.png'}}, {'assets': {}},
                        {'sources': ['https://learn.chatgpt.com.evil.test/docs']},
                        {'sources': ['https://github.com/unknown/repo', self.article['sources'][0]]}]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                validate_article(self.article | changes, self.root)
        (self.root / 'cover.png').write_bytes(b'not a PNG')
        with self.assertRaises(ValueError):
            validate_article(self.article, self.root)

    def test_guide_tags_3_to_6(self):
        for tags in ([], ['a', 'b'], ['a', 'b', 'c', 'd', 'e', 'f', 'g'], ['a', 'b', ''], ['a', 'b', 3]):
            with self.subTest(tags=tags), self.assertRaises(ValueError):
                validate_article(self.article | {'tags': tags}, self.root)
        with self.assertRaises(ValueError):
            validate_article({k: v for k, v in self.article.items() if k != 'tags'}, self.root)
        validate_article(self.article | {'tags': list('abcdef')}, self.root)

    def test_table_escapes_cells_and_requires_complete_rows(self):
        result = render_markdown('| 項目 | 値 |\n| --- | --- |\n| `<img>` | A \\| B |')
        self.assertIn('<table>', result)
        self.assertIn('<th scope="col">', result)
        self.assertIn('&lt;img&gt;', result)
        self.assertIn('A | B', result)
        with self.assertRaises(ValueError):
            render_markdown('| A | B |\n| --- | --- |\n| missing |')
        with self.assertRaises(ValueError):
            render_markdown('![unsafe](https://evil.test/img.png)')
        with self.assertRaises(ValueError):
            render_markdown('![missing](asset:unknown)')

    def test_guide_publishes_cover_and_flow_and_image_change_alters_hash(self):
        payloads = []
        def publish(article):
            payloads.append(article.copy())
            return 'https://jacks-aiblog.tistory.com/3'
        for day in (15, 16):
            state_dir = self.root / str(day)
            result = publish_daily(state_dir, [self.article], root=self.root, publish=publish,
                                   verify=lambda *_: True, now=datetime(2026, 11, day, tzinfo=timezone.utc))
            self.assertEqual(result['status'], 'published')
            self.assertEqual(publish_daily(state_dir, [self.article], root=self.root, publish=publish,
                                          verify=lambda *_: True, now=datetime(2026, 11, day, tzinfo=timezone.utc))['status'], 'already_published')
            (self.root / 'cover.png').write_bytes(PNG + b'changed')
        self.assertIn('data:image/png;base64,', payloads[0]['html'])
        self.assertEqual(payloads[0]['html'].count('<img '), 2)
        self.assertNotEqual(payloads[0]['hash'], payloads[1]['hash'])

    def test_public_verification_checks_images_and_table_structure_without_forcing_code(self):
        image = 'https://blog.kakaocdn.net/dn/example/img.png'
        body = f'<div id="learning-guide"><table><tr><th>入力</th><td>結果</td></tr></table><figure><img src="{image}" alt="流れ"></figure></div>'
        article = {'title': '案内', 'kind': 'guide', 'marker': 'learning-guide', 'html': body}
        for actual, expected in [(body, True), (body.replace(image, 'data:image/png;base64,AAAA'), False),
                                 (body.replace(image, 'https://evil.test/image.png'), False),
                                 (body.replace('<table>', '<div>').replace('</table>', '</div>'), False),
                                 (body.replace(f'<img src="{image}" alt="流れ">', ''), False)]:
            text = f'<title>案内</title><meta property="og:image" content="{image}">' + actual
            with self.subTest(expected=expected), patch('httpx.get', return_value=SimpleNamespace(status_code=200, text=text)):
                self.assertEqual(verify('https://jacks-aiblog.tistory.com/3', article), expected)

    def test_pending_recovery_keeps_content_contract_and_rejects_wrong_cover(self):
        image = 'https://blog.kakaocdn.net/dn/cover/img.png'
        body = f'<div id="learning-guide"><p>実行結果</p><img src="{image}" alt="表紙"></div>'
        pending = {'title': '案内', 'kind': 'guide', 'marker': 'learning-guide',
                   'expected_body': body_signature(body, 'learning-guide')}
        cases = [(body, image, True), (body.replace('実行結果', '別の結果'), image, False),
                 (body, 'https://blog.kakaocdn.net/dn/another/img.png', False),
                 (body.replace(image, 'blob:temporary'), image, False)]
        for actual, cover, expected in cases:
            response = f'<title>案内</title><meta property="og:image" content="{cover}">' + actual
            with self.subTest(expected=expected), patch('httpx.get', return_value=SimpleNamespace(status_code=200, text=response)):
                self.assertEqual(verify('https://jacks-aiblog.tistory.com/3', pending), expected)

    def test_preparing_legacy_labs_preserves_guide_order_and_cover_metadata(self):
        from scripts import prepare_learning_posts
        directory = self.root / 'docs/posts'
        directory.mkdir(parents=True)
        legacy = {'id': 'python-kst-date', 'assets': {'cover': 'existing.png'}}
        (directory / 'catalogue.json').write_text(json.dumps([self.article, legacy]))
        with patch.object(prepare_learning_posts, 'ROOT', self.root), contextlib.redirect_stdout(io.StringIO()):
            prepare_learning_posts.main()
        entries = json.loads((directory / 'catalogue.json').read_text())
        self.assertEqual(entries[0], self.article)
        self.assertEqual(entries[1]['assets'], legacy['assets'])
        self.assertEqual(len(entries), 8)

    def test_new_upload_is_found_when_editor_inserts_before_previous_image(self):
        cover = 'https://blog.kakaocdn.net/dn/cover/img.png?a=1'
        flow = 'https://blog.kakaocdn.net/dn/flow/img.png'
        self.assertEqual(new_image_url([cover], [flow, cover]), flow)
        for current in [[cover], [cover.replace('a=1', 'a=2')], ['https://evil.test/img.png', cover]]:
            with self.subTest(current=current), self.assertRaises(RuntimeError):
                new_image_url([cover], current)
