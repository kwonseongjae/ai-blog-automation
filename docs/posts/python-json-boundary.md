# JSON에 title이 있어도 바로 쓰면 안 되는 이유: 입력 검증 실습

외부 응답에서 title을 읽을 때 키가 있는지만 확인하면 충분할까요? 값이 null이거나 숫자, 공백 문자열일 수도 있습니다. 이 글에서는 JSON을 읽은 뒤 얻는 파이썬 값의 타입과 필수 필드를 검사합니다. 외부 API를 실제로 호출하지 않고 고정된 입력으로 경계를 확인하므로 인증정보가 필요하지 않습니다.

## 왜 이 조건을 확인할까

payload.get("title", "")는 키가 없을 때의 기본값을 정할 뿐, null이나 숫자를 문자열로 바꾸지 않습니다. 잘못된 값을 나중에 처리하려고 하면 오류가 화면 표시나 저장 단계까지 퍼집니다. 입력을 처음 받는 곳에서 객체·문자열·빈 값의 조건을 검사하면 이후 코드가 기대할 수 있는 값을 분명히 만들 수 있습니다.

## 독립 실행 예제

아래 코드는 Python 3.12.3 / Linux에서 실행해 확인했습니다. 입력값은 실습용 고정 자료입니다.

```python
def lesson_input():
    def read_title(payload):
        if not isinstance(payload, dict):
            raise ValueError('객체가 필요합니다')
        title = payload.get('title')
        if not isinstance(title, str) or not title.strip():
            raise ValueError('비어 있지 않은 제목이 필요합니다')
        return title.strip()

    assert read_title({'title': '  첫 실습  '}) == '첫 실습'
    failures = 0
    for value in [None, [], {}, {'title': None}, {'title': '  '}, {'title': 12}]:
        try:
            read_title(value)
        except ValueError:
            failures += 1
    assert failures == 6
    return ['정상 제목: 첫 실습', '거부한 잘못된 입력: 6개',
            '검증: 필드의 존재뿐 아니라 타입과 빈 문자열을 확인했습니다.']

for line in lesson_input():
    print(line)
```

## 실행 결과와 읽는 방법

```text
정상 제목: 첫 실습
거부한 잘못된 입력: 6개
검증: 필드의 존재뿐 아니라 타입과 빈 문자열을 확인했습니다.
```

정상 입력에는 앞뒤 공백을 넣고 반환값이 정리되는지 확인합니다. 잘못된 입력은 객체가 아닌 값, 키가 없는 객체, null, 공백 문자열, 숫자입니다. 각각 ValueError로 거부하는지 세고 전체가 거부됐는지 assert로 확인합니다. 오류를 전부 무시하는 대신 입력의 조건을 명시적으로 검사하는 것이 핵심입니다.

## 적용할 때 주의할 점

이 예제는 title 하나만 다룹니다. 문자열 최대 길이, 중첩 구조, 알 수 없는 필드, 허용 문자 등은 제품 요구에 따라 달라집니다. 여러 필드를 검증한다면 이미 프로젝트에 쓰는 검증 도구를 먼저 확인하는 편이 좋습니다. 입력이 잘못됐다는 이유만으로 응답 전체나 인증 헤더를 로그에 남기면 비밀 값이 노출될 수 있습니다.

## 다음 실습에서 확인할 것

입력 검증의 목표는 어떤 값이 와도 적당히 문자열로 바꿔 계속 실행하는 것이 아닙니다. 유효한 값과 거부할 값을 나누고, 거부 사유를 호출하는 쪽에 알려주는 것입니다. 이후 API를 연결할 때도 정상 응답뿐 아니라 누락·null·타입 변화가 있는 응답을 고정 자료로 남겨 같은 테스트를 유지할 수 있습니다.

## 코드와 공식 출처

전체 예제와 테스트는 공개 저장소에서 확인할 수 있습니다.

- [예제 코드](https://github.com/kwonseongjae/ai-blog-automation/blob/main/labs/learning_basics.py)
- [검증 테스트](https://github.com/kwonseongjae/ai-blog-automation/blob/main/tests/test_learning_labs.py)
- [공식 문서 1](https://docs.python.org/3.12/library/json.html)
- [공식 문서 2](https://docs.python.org/3.12/library/stdtypes.html#dict.get)
