import unittest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from automation.tistory_publisher import check_management_url, load_saved_cookies, normalize_cookies, post_url, verify


class PublisherBoundaryTests(unittest.TestCase):
    def test_cookie_snapshot_excludes_unrelated_domains_and_invalid_fields(self):
        cookies = normalize_cookies([
            {'name': 'session', 'value': 'example', 'domain': '.tistory.com', 'path': '/', 'sameSite': 'unset', 'expiry': 0},
            {'name': 'other', 'value': 'example', 'domain': 'accounts.kakao.com', 'path': '/'},
            {'name': 'other', 'value': 'example', 'domain': '.eviltistory.com', 'path': '/'},
            {'name': 'missing'},
        ])
        self.assertEqual(len(cookies), 1)
        self.assertNotIn('expiry', cookies[0])
        self.assertEqual(cookies[0]['sameSite'], 'Lax')

    def test_login_redirect_and_other_blog_are_rejected(self):
        check_management_url('https://jacks-aiblog.tistory.com/manage/newpost')
        for url in ['https://www.tistory.com/auth/login?redirectUrl=https://jacks-aiblog.tistory.com/manage',
                    'https://jack-0314.tistory.com/manage/newpost',
                    'https://jacks-aiblog.tistory.com/2']:
            with self.subTest(url=url), self.assertRaises(RuntimeError):
                check_management_url(url)

    def test_response_must_have_the_documented_entry_id(self):
        self.assertEqual(post_url({'entryId': 2}), 'https://jacks-aiblog.tistory.com/2')
        for result in [None, [], {'id': 2}, {'entryId': '2/../manage'}, {'entryId': True}]:
            with self.subTest(result=result), self.assertRaises(ValueError):
                post_url(result)

    def test_public_verification_rejects_truncated_body_with_a_valid_marker(self):
        from types import SimpleNamespace
        article = {'title': 'A & B', 'marker': 'learning-example',
                   'html': '<div id="learning-example"><pre><code>print(1)</code></pre><p>끝까지 쓴 원고</p></div>'}
        for text, expected in [
            ('<title>A &amp; B</title>' + article['html'], True),
            ('<title>A &amp; B</title><div id="learning-example"><pre>print(1)</pre><p>잘린 원고</p></div>', False),
        ]:
            with self.subTest(expected=expected), patch('httpx.get', return_value=SimpleNamespace(status_code=200, text=text)):
                self.assertEqual(verify('https://jacks-aiblog.tistory.com/2', article), expected)

    def test_reading_session_does_not_export_secrets_or_import_private_code(self):
        from cryptography.fernet import Fernet
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            key = Fernet.generate_key()
            (root / '.env').write_text('SESSION_ENCRYPT_KEY=' + key.decode() + '\nUNRELATED_PRIVATE_KEY=must-not-export\n')
            sessions = root / 'data/sessions'
            sessions.mkdir(parents=True)
            data = [{'name': 'sid', 'value': 'example', 'domain': '.tistory.com'}]
            (sessions / 'tistory.session').write_bytes(Fernet(key).encrypt(json.dumps(data).encode()))
            with patch.dict(os.environ, {'BLOG_AUTOMATION_ROOT': directory}):
                before = os.environ.copy()
                self.assertEqual(len(load_saved_cookies()), 1)
                self.assertEqual(os.environ.copy(), before)


if __name__ == '__main__':
    unittest.main()
