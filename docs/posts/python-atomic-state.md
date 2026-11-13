# JSON 상태 파일을 덮어쓰다 멈추면: 임시 파일과 원자적 교체

작업의 마지막 실행일이나 처리 결과를 JSON으로 저장할 때, 원본 파일을 바로 비우고 쓰면 중간에 멈춘 순간 파일이 깨질 수 있습니다. 이 실습에서는 임시 파일을 쓰는 동안 기존 상태가 남는지, 교체가 끝난 뒤 새 상태를 읽는지 확인합니다. 전원 차단이나 저장 장치 고장을 실제로 재현한 시험은 아닙니다.

## 왜 이 조건을 확인할까

기존 파일을 읽는 쪽이 완성되지 않은 새 JSON을 보지 않도록, 같은 디렉터리에 임시 파일을 완성한 뒤 os.replace()로 이름을 교체할 수 있습니다. 핵심은 데이터를 쓰는 단계와 원본 이름을 바꾸는 단계를 나누는 것입니다. 같은 파일시스템 안에서 사용해야 하며 교체가 실패하는 예외도 처리해야 합니다.

## 독립 실행 예제

아래 코드는 Python 3.12.3 / Linux에서 실행해 확인했습니다. 입력값은 실습용 고정 자료입니다.

```python
def lesson_atomic():
    import json
    import os
    from pathlib import Path
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as directory:
        target = Path(directory) / 'state.json'
        temp = target.with_suffix('.tmp')
        target.write_text('{"status":"before"}', encoding='utf-8')
        temp.write_text('{"status":', encoding='utf-8')
        assert json.loads(target.read_text())['status'] == 'before'
        temp.write_text('{"status":"after"}', encoding='utf-8')
        os.replace(temp, target)
        assert json.loads(target.read_text())['status'] == 'after'
        assert not temp.exists()
    return ['교체 전 기존 상태: before', '교체 후 새 상태: after',
            '검증: 임시 파일을 쓰는 중에는 기존 JSON이 보존됐습니다.']

for line in lesson_atomic():
    print(line)
```

## 실행 결과와 읽는 방법

```text
교체 전 기존 상태: before
교체 후 새 상태: after
검증: 임시 파일을 쓰는 중에는 기존 JSON이 보존됐습니다.
```

예제는 기존 상태를 before로 저장한 뒤 임시 파일에는 일부러 불완전한 JSON을 씁니다. 이때 원본을 읽으면 before가 유지됩니다. 임시 파일을 올바른 JSON으로 완성하고 교체하면 after가 읽히고 임시 경로는 사라집니다. 파일 이름이 바뀌는 동작을 확인한 것이며 저장 장치에 물리적으로 기록됐는지를 측정한 결과는 아닙니다.

## 적용할 때 주의할 점

원자적 교체와 동시 실행 제어는 별개입니다. 두 프로세스가 서로 다른 새 상태를 만들면 마지막 교체가 앞선 변경을 덮을 수 있습니다. 고정된 임시 파일 이름도 동시 쓰기에는 충돌합니다. 운영 코드에서는 고유한 임시 파일, 잠금, flush와 fsync, 필요한 경우 디렉터리 동기화까지 요구 조건에 맞춰 검토해야 합니다.

## 다음 실습에서 확인할 것

상태 파일이 깨졌을 때 빈 상태로 초기화하고 계속 실행하면 이미 처리한 작업을 다시 수행할 수 있습니다. 오류를 숨기기보다 중단하고 복구할 자료를 남기는 편이 안전한 경우가 많습니다. 저장 방식은 작게 시작하되, 트랜잭션이나 여러 프로세스의 갱신이 필요해지면 데이터베이스를 검토할 수 있습니다.

## 코드와 공식 출처

전체 예제와 테스트는 공개 저장소에서 확인할 수 있습니다.

- [예제 코드](https://github.com/kwonseongjae/ai-blog-automation/blob/main/labs/learning_basics.py)
- [검증 테스트](https://github.com/kwonseongjae/ai-blog-automation/blob/main/tests/test_learning_labs.py)
- [공식 문서 1](https://docs.python.org/3.12/library/os.html#os.replace)
- [공식 문서 2](https://docs.python.org/3.12/library/tempfile.html)
