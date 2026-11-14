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

    def test_learning_widgets_keep_native_category_recent_posts_and_comments(self):
        source = '''<html><head></head><body><header class="header"></header>
<main class="main"><div class="area-main"><s_article_rep><s_rp>댓글</s_rp></s_article_rep></div>
<aside class="area-aside"><s_sidebar>
<s_sidebar_element><div class="box-profile"><img class="img-profile" src="default_L.png"></div></s_sidebar_element>
<s_sidebar_element><div class="box-category">[##_category_list_##]</div></s_sidebar_element>
<s_sidebar_element><div class="box-recent"><s_rctps_rep>[##_rctps_rep_link_##]</s_rctps_rep></div></s_sidebar_element>
</s_sidebar></aside></main><s_search>검색</s_search></body></html>'''
        result = transform(source)
        self.assertIn('[##_category_list_##]', result)
        self.assertIn('[##_rctps_rep_link_##]', result)
        self.assertIn('<s_rp>댓글</s_rp>', result)
        self.assertIn('<s_search>검색</s_search>', result)
        self.assertEqual(result.count('<s_sidebar_element>'), 3)
        self.assertNotIn('default_L.png', result)
        self.assertIn('href="/1"', result)
        self.assertIn('aria-label="블로그 메뉴"', result)
        self.assertIn('learning-widgets', result)
        self.assertEqual(transform(result), result)


if __name__ == '__main__':
    unittest.main()
