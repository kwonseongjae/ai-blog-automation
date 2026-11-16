import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from automation import telegram_reports as t


class TelegramReportsTest(unittest.TestCase):
    def test_settings_prefer_environment_then_env_file(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / '.env').write_text('TELEGRAM_BOT_TOKEN="file-token"\nTELEGRAM_CHAT_ID=42\nOTHER=x\n', encoding='utf-8')
            with mock.patch.dict(os.environ, {'BLOG_AUTOMATION_ROOT': d, 'TELEGRAM_BOT_TOKEN': 'env-token'}, clear=True):
                self.assertEqual(t.telegram_settings(), ('env-token', '42'))
            with mock.patch.dict(os.environ, {'BLOG_AUTOMATION_ROOT': d}, clear=True):
                self.assertEqual(t.telegram_settings(), ('file-token', '42'))

    def test_missing_settings_raise_without_values(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {'BLOG_AUTOMATION_ROOT': d}, clear=True):
            with self.assertRaisesRegex(ValueError, 'not set'):
                t.telegram_settings()

    def test_daily_text_counts_today_and_remaining(self):
        posted = [{'date': '2026-11-15', 'title': '앞 글', 'url': 'u1'}, {'date': '2026-11-16', 'title': '오늘 글', 'url': 'u2'}]
        text = t.daily_text(posted, 19, '2026-11-16', '내일 07:30', 'success')
        self.assertIn('오늘 발행: 1건', text)
        self.assertIn('남은 원고 17편', text)
        self.assertIn('마지막 글: 오늘 글', text)
        self.assertIn('수집하지 않음', text)

    def test_daily_text_without_posts(self):
        self.assertIn('오늘 발행: 0건', t.daily_text([], 3, '2026-11-16', '-', '-'))

    def test_verify_text_marks_unindexed_and_unknown_separately(self):
        ads = {'adsense': False, 'adfit': False}
        text = t.verify_text([{'url': 'a', 'status': 200, 'ads': ads, 'google': False},
                              {'url': 'b', 'status': 200, 'ads': ads, 'google': None},
                              {'url': 'c', 'status': 404, 'ads': ads, 'google': True}], '2026-11-16')
        self.assertIn('❌미색인', text)
        self.assertIn('조회 불가', text)
        self.assertEqual(text.count('⚠️'), 2)

    def test_check_ads_detects_codes(self):
        self.assertEqual(t.check_ads('<ins class="adsbygoogle">'), {'adsense': True, 'adfit': False})
        self.assertEqual(t.check_ads('//t1.daumcdn.net/kas/x'), {'adsense': False, 'adfit': True})

    def test_send_failure_does_not_leak_token(self):
        import httpx
        with mock.patch.object(t, 'telegram_settings', return_value=('SECRET', '1')), \
             mock.patch.object(t.httpx, 'post', side_effect=httpx.ConnectError('https://api.telegram.org/botSECRET/x')):
            with self.assertRaises(RuntimeError) as ctx:
                t.send('x')
        self.assertNotIn('SECRET', str(ctx.exception))


if __name__ == '__main__':
    unittest.main()
