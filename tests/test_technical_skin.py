import unittest

from automation.technical_skin import transform


class TechnicalSkinTests(unittest.TestCase):
    def test_injection_preserves_skin_tags_and_is_idempotent(self):
        source = '<html><head>\n\n</head><body><main class="main"><div class="area-main">\n\n  <s_list>목록</s_list><s_article_rep>본문</s_article_rep></div></main></body></html>'
        result = transform(source)
        self.assertEqual(result.count('id="learning-home"'), 1)
        self.assertIn('<s_article_rep>본문</s_article_rep>', result)
        self.assertEqual(transform(result), result)
        self.assertIn('https://github.com/kwonseongjae/ai-blog-automation', result)
        self.assertNotIn('jack-0314', result)
        self.assertIn('prefers-reduced-motion', result)

    def test_unrecognized_template_is_not_silently_overwritten(self):
        with self.assertRaises(ValueError):
            transform('<html>unknown</html>')


if __name__ == '__main__':
    unittest.main()
