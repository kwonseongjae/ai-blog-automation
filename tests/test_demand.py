import unittest
from unittest import mock

from automation import demand as d

ARTICLE = {'title': 'Claude Code 권한 설정: 파일을 만들기 전에 물어보게 하는 법', 'target_query': 'claude code 권한 설정',
           'demand': {'grade': 'B', 'basis': "구글 자동완성 2026-11-20: 'claude code 권한 설정'", 'checked_on': '2026-11-20'}}
SOURCE = '# 제목\n\nClaude Code의 권한 설정은 파일을 바꾸기 전에 묻게 할 수 있습니다.\n'


class DemandTest(unittest.TestCase):
    def test_basis_requires_same_expression_in_suggestions(self):
        found = {'google': ['claude code 권한 설정 방법'], 'naver': []}
        self.assertIn("'claude code 권한 설정 방법'", d.find_basis('Claude Code 권한 설정', found, '2026-11-20'))
        self.assertIsNone(d.find_basis('claude code 훅', {'google': ['claude code 후기'], 'naver': []}))

    def test_suggestions_survive_one_source_failing(self):
        client = mock.Mock()
        client.get.side_effect = [mock.Mock(json=lambda: ['q', ['a b']]), RuntimeError('down')]
        self.assertEqual(d.suggestions('a', client), {'google': ['a b'], 'naver': []})

    def test_valid_article_has_no_issues(self):
        self.assertEqual(d.demand_issues(ARTICLE, SOURCE), [])

    def test_missing_fields_title_lead_and_basis_are_flagged(self):
        self.assertTrue(d.demand_issues({'title': 'x'}, SOURCE))
        self.assertIn('제목', ' '.join(d.demand_issues(ARTICLE | {'title': '권한 이야기'}, SOURCE)))
        self.assertIn('첫 문단', ' '.join(d.demand_issues(ARTICLE, '# t\n\n전혀 다른 이야기입니다.\n')))
        bad = ARTICLE | {'demand': {'grade': 'B', 'basis': '근거 없음', 'checked_on': '2026-11-20'}}
        self.assertIn('인용', ' '.join(d.demand_issues(bad, SOURCE)))
        self.assertIn('등급', ' '.join(d.demand_issues(ARTICLE | {'demand': ARTICLE['demand'] | {'grade': 'Z'}}, SOURCE)))

    def test_grade_c_only_needs_a_basis_note(self):
        c = ARTICLE | {'demand': {'grade': 'C', 'basis': '자동완성에 같은 표현 없음(가설)', 'checked_on': '2026-11-20'}}
        self.assertEqual(d.demand_issues(c, SOURCE), [])


if __name__ == '__main__':
    unittest.main()
