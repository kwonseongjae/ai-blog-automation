import unittest

from automation import technical_skin
from automation.technical_skin import side_promo, start_here, transform


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
        self.assertEqual(result.count('google-site-verification'), 1)
        self.assertEqual(result.count('id="learning-extras"'), 1)
        self.assertIn('data-learning-theme', result)
        self.assertIn('data-count-for', result.split('class="learning-topics"')[1])
        self.assertEqual(result.count('naver-site-verification'), 1)

    def test_login_menu_navigates_in_same_window(self):
        result = transform('<html><head></head><body><main class="main"><div class="area-main"></div></main></body></html>')
        extras = result.split('id="learning-extras"')[1]
        self.assertIn('auth/login', extras)
        self.assertIn('stopImmediatePropagation', extras)

    def test_ga4_uses_direct_gtag_and_skips_internal_visits(self):
        extras = transform('<html><head></head><body><main class="main"><div class="area-main"></div></main></body></html>').split('id="learning-extras"')[1]
        self.assertIn('G-KYEEZVW0X2', extras)
        self.assertIn("if(internal)return;", extras)
        self.assertIn('ga_internal', extras)
        self.assertIn('HeadlessChrome', extras)
        self.assertIn("'scroll_depth'", extras)
        self.assertNotIn('GTM-', extras)

    def test_claude_code_post_uses_codex_style_list_card(self):
        js = technical_skin.SCRIPT
        self.assertIn("Claude Code\\n처음 쓰는 설정", js)
        self.assertIn('/^\\/[1-5]$/', js)

    def test_start_here_only_own_blog(self):
        self.assertIn('https://jacks-aiblog.tistory.com/3', start_here())
        original = technical_skin.START_HERE
        try:
            technical_skin.START_HERE = (('외부', 'https://evil.test/3'),)
            with self.assertRaises(ValueError):
                start_here()
        finally:
            technical_skin.START_HERE = original

    def test_side_promo_only_own_urls(self):
        self.assertIn('https://jacks-aiblog.tistory.com/3', side_promo())
        original = technical_skin.SIDE_LINKS
        try:
            for url in ('https://evil.test/3', 'https://github.com/other/repo'):
                technical_skin.SIDE_LINKS = (('제목', '설명', url),)
                with self.assertRaises(ValueError):
                    side_promo()
            technical_skin.SIDE_LINKS = (('제목', '설명', 'https://github.com/kwonseongjae/ai-blog-automation'),)
            self.assertIn('ai-blog-automation', side_promo())
        finally:
            technical_skin.SIDE_LINKS = original

    def test_popular_tab_stays_hidden(self):
        self.assertIn('.area-aside .list-recent.list-tab{display:none!important}', technical_skin.CSS)

    def test_cover_stays_under_thumbnail(self):
        self.assertNotIn('.thumbnail[has-thumbnail="1"] .learning-cover{display:none}', technical_skin.CSS)
        self.assertIn('.thumbnail.learning-loaded .learning-cover{display:none}', technical_skin.CSS)
        self.assertIn('background-image:none!important', technical_skin.CSS)

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
        self.assertIn('AI 코딩 도구, 설정부터 같이 확인합니다', result)
        topics = result.split('class="learning-topics"')[1].split('</nav>')[0]
        for name in ('AI 시작하기', '도구·모델 비교', '프로젝트 적용기'):
            self.assertIn(name, topics)
        self.assertEqual(topics.count('<a '), 3)
        self.assertNotIn('Python·자동화', topics)
        principles = result.split('class="learning-principles"')[1].split('</ul>')[0]
        for text in ('하루 최대 한 편', '직접 실행해 확인한 내용', '확인일과 공식 출처'):
            self.assertIn(text, principles)
        self.assertIn('처음이라면 이 순서로', result)
        self.assertIn('<code>codex --version</code>', result)
        self.assertNotIn('class="learning-cards"', result)
        self.assertIn('Jack', result)
        self.assertIn('aria-label="블로그 메뉴"', result)
        self.assertIn('learning-widgets', result)
        self.assertEqual(transform(result), result)

    def test_cover_keeps_native_image_and_uses_real_post_placeholders(self):
        source = '''<html><head></head><body><header><h1>[##_title_##]</h1></header>
<div class="area-main"><s_list_rep><article>
<a href="[##_list_rep_link_##]"><p class="thumbnail" <s_list_rep_thumbnail>has-thumbnail="1"</s_list_rep_thumbnail>>
<img src="[##_list_rep_thumbnail_raw_url_##]" class="img-thumbnail" role="presentation"></p></a>
</article></s_list_rep></div><footer>[##_var_footerCopyright_##]</footer></body></html>'''
        result = transform(source)
        self.assertIn('class="learning-cover"', result)
        self.assertIn('[##_list_rep_title_text_##]', result)
        self.assertIn('[##_list_rep_category_##]', result)
        self.assertIn('<s_list_rep_thumbnail>has-thumbnail="1"</s_list_rep_thumbnail>', result)
        self.assertIn('aria-label="[##_list_rep_title_text_##]"', result)
        self.assertIn('Jack의 AI 개발노트', result)
        self.assertLess(result.index('aria-label="블로그 메뉴"'), result.index('</header>'))
        self.assertEqual(transform(result), result)


if __name__ == '__main__':
    unittest.main()
