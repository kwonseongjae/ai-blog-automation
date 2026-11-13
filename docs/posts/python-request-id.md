# 같은 요청이 두 번 왔을 때: SQLite 고유 키로 중복 저장 막기

응답을 받지 못한 호출자는 같은 요청을 다시 보낼 수 있습니다. 서버가 이전 요청을 처리했는지와 응답이 도착했는지는 서로 다른 문제입니다. 여기서는 같은 식별자의 요청을 두 번 저장하고 실제 행이 한 개만 남는지 확인합니다. 외부 결제나 글 발행을 한 번만 실행하도록 보장하는 전체 구현은 아닙니다.

## 왜 이 조건을 확인할까

저장하기 전에 조회하고 없으면 추가하는 코드만으로는 여러 실행이 동시에 통과할 수 있습니다. 데이터베이스의 고유 제약을 사용하면 저장 경계에서 같은 키가 겹치는 것을 막을 수 있습니다. 이 예제는 PRIMARY KEY와 INSERT OR IGNORE를 사용해 처음 추가와 재요청을 구분합니다.

## 독립 실행 예제

아래 코드는 Python 3.12.3 / Linux에서 실행해 확인했습니다. 입력값은 실습용 고정 자료입니다.

```python
def lesson_duplicate():
    import sqlite3

    with sqlite3.connect(':memory:') as db:
        db.execute('CREATE TABLE jobs (request_id TEXT PRIMARY KEY, result TEXT NOT NULL)')
        first = db.execute('INSERT OR IGNORE INTO jobs VALUES (?, ?)', ('request-1', 'done')).rowcount
        second = db.execute('INSERT OR IGNORE INTO jobs VALUES (?, ?)', ('request-1', 'done')).rowcount
        count = db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]
        assert (first, second, count) == (1, 0, 1)
    return ['첫 요청 저장: 1개', '같은 요청 다시 저장: 0개', '남은 행: 1개',
            '검증: 같은 식별자를 중복 저장하지 않았습니다.']

for line in lesson_duplicate():
    print(line)
```

## 실행 결과와 읽는 방법

```text
첫 요청 저장: 1개
같은 요청 다시 저장: 0개
남은 행: 1개
검증: 같은 식별자를 중복 저장하지 않았습니다.
```

메모리 데이터베이스에 jobs 테이블을 만들고 같은 request-1을 두 번 넣습니다. 첫 실행의 rowcount는 1, 두 번째는 0이고 전체 행은 1개입니다. 이 세 조건을 함께 확인해야 두 번째 요청을 무시한 것과 첫 요청 자체가 저장되지 않은 상황을 구분할 수 있습니다. 값은 문자열 조합 대신 매개변수로 전달합니다.

## 적용할 때 주의할 점

테이블에 한 행만 있다는 사실이 외부 동작도 한 번만 실행됐다는 뜻은 아닙니다. 외부 발행 성공 후 데이터 저장 전에 멈추면 결과가 불확실할 수 있습니다. 요청 식별자는 무작위로 새로 만들기보다 같은 논리 요청에서 재사용할 수 있어야 합니다. 같은 식별자에 다른 내용을 보내면 어떻게 처리할지도 별도로 정해야 합니다.

## 다음 실습에서 확인할 것

실제 자동화에서는 요청 키, 처리 중 상태, 외부 결과의 식별자와 확인 상태를 나누어 기록합니다. 이미 수행됐을 가능성이 있는 작업을 무조건 재시도하지 않는 것도 중요한 설계입니다. 이 실습은 저장 단계의 중복을 막는 출발점이며, 외부 동작의 중복 방지는 대상 서비스의 특성과 함께 검토해야 합니다.

## 코드와 공식 출처

전체 예제와 테스트는 공개 저장소에서 확인할 수 있습니다.

- [예제 코드](https://github.com/kwonseongjae/ai-blog-automation/blob/main/labs/learning_basics.py)
- [검증 테스트](https://github.com/kwonseongjae/ai-blog-automation/blob/main/tests/test_learning_labs.py)
- [공식 문서 1](https://docs.python.org/3.12/library/sqlite3.html)
