# URL에 블로그 이름이 들어 있으면 안전할까: 정확한 발행 대상 확인

자동화가 여러 주소를 다룰 때 문자열에 블로그 이름이 있는지만 확인하면 잘못된 대상으로 요청할 수 있습니다. 비슷한 호스트 이름이나 사용자 정보에 같은 문자열이 들어갈 수 있기 때문입니다. 이 글은 네트워크 요청을 보내지 않고 URL 구조를 나누어 허용할 대상을 비교하는 실습입니다.

## 왜 이 조건을 확인할까

urlsplit()은 스킴과 네트워크 위치, 경로 등을 구분합니다. 여기서는 HTTPS와 정확한 netloc가 모두 일치할 때만 허용합니다. 고정된 한 블로그만 대상으로 하는 간단한 작업이라면 넓은 규칙보다 이 조건이 읽기 쉽습니다. URL을 파싱하는 것과 신뢰할 수 있는 URL인지 검증하는 것은 별개입니다.

## 독립 실행 예제

아래 코드는 Python 3.12.3 / Linux에서 실행해 확인했습니다. 입력값은 실습용 고정 자료입니다.

```python
def lesson_url():
    from urllib.parse import urlsplit

    expected = 'jacks-aiblog.tistory.com'

    def allowed(value):
        parsed = urlsplit(value)
        return parsed.scheme == 'https' and parsed.netloc == expected

    assert allowed('https://jacks-aiblog.tistory.com/2')
    assert not allowed('https://jacks-aiblog.tistory.com.evil.test/2')
    assert not allowed('https://jacks-aiblog.tistory.com@evil.test/2')
    assert not allowed('http://jacks-aiblog.tistory.com/2')
    assert not allowed('https://jack-0314.tistory.com/2')
    return ['정확한 HTTPS 호스트: 허용', '비슷한 이름·사용자 정보·다른 블로그: 거부',
            '검증: 문자열 포함 여부로 발행 대상을 판단하지 않았습니다.']

for line in lesson_url():
    print(line)
```

## 실행 결과와 읽는 방법

```text
정확한 HTTPS 호스트: 허용
비슷한 이름·사용자 정보·다른 블로그: 거부
검증: 문자열 포함 여부로 발행 대상을 판단하지 않았습니다.
```

정확한 새 블로그 주소는 허용하고, 그 이름 뒤에 다른 도메인이 붙은 주소, 사용자 정보에 블로그 이름을 넣은 주소, HTTP 주소, 다른 블로그 주소는 거부합니다. assert가 실패하면 어떤 조건이 바뀌었는지 바로 확인할 수 있습니다. 실제 코드에서는 최종 리디렉션 주소도 다시 검사해야 합니다.

## 적용할 때 주의할 점

이 예제는 고정 호스트를 확인하는 최소한의 조건입니다. 특정 포트, 경로, 쿼리, 국제화 도메인, DNS 해석 결과와 내부망 접근을 다루는 일반 URL 검증기는 아닙니다. 신뢰할 수 없는 외부 URL을 서버에서 조회한다면 네트워크 접근 범위까지 별도로 제한해야 합니다. 파서가 결과를 반환했다고 주소가 유효하다는 보장은 없습니다.

## 다음 실습에서 확인할 것

블로그 글쓰기 자동화에서는 편집기를 연 뒤와 최종 저장 버튼을 누르기 직전에 실제 호스트가 맞는지 확인할 수 있습니다. 공개 결과를 기록할 때는 글 번호를 포함한 경로까지 제한합니다. 주소가 예상과 다르면 기존 블로그로 대체하지 않고 중단해야 잘못된 발행을 피할 수 있습니다.

## 코드와 공식 출처

전체 예제와 테스트는 공개 저장소에서 확인할 수 있습니다.

- [예제 코드](https://github.com/kwonseongjae/ai-blog-automation/blob/main/labs/learning_basics.py)
- [검증 테스트](https://github.com/kwonseongjae/ai-blog-automation/blob/main/tests/test_learning_labs.py)
- [공식 문서 1](https://docs.python.org/3.12/library/urllib.parse.html#urllib.parse.urlsplit)
