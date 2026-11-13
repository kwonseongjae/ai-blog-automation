# 끝나지 않는 작업을 기다리지 않도록 subprocess 제한 시간 두기

자동화가 외부 프로그램을 호출할 때 실행 시간이 끝없이 늘어날 수 있습니다. 한 작업이 멈추면 뒤의 일정도 밀리므로 기다릴 수 있는 한도를 정해야 합니다. 이 실습은 짧은 파이썬 자식 프로세스를 실행해 정상 출력과 TimeoutExpired를 비교합니다. 네트워크나 실제 브라우저 장애를 재현하는 시험은 아닙니다.

## 왜 이 조건을 확인할까

subprocess.run()에 timeout을 주면 정해진 시간 안에 끝나지 않는 자식 프로세스를 실패로 구분할 수 있습니다. check=True는 종료 코드가 잘못됐을 때도 성공으로 넘기지 않도록 합니다. timeout, 종료 코드, 프로그램이 남긴 출력은 서로 다른 정보이므로 하나의 성공 여부로 뭉뚱그리지 않는 편이 좋습니다.

## 독립 실행 예제

아래 코드는 Python 3.12.3 / Linux에서 실행해 확인했습니다. 입력값은 실습용 고정 자료입니다.

```python
def lesson_timeout():
    import subprocess
    import sys

    normal = subprocess.run([sys.executable, '-c', 'print("ok")'], capture_output=True,
                            text=True, timeout=3, check=True)
    assert normal.stdout.strip() == 'ok'
    stopped = False
    try:
        subprocess.run([sys.executable, '-c', 'import time; time.sleep(2)'], timeout=0.1, check=True)
    except subprocess.TimeoutExpired:
        stopped = True
    assert stopped
    return ['정상 작업 출력: ok', '지연 작업: TimeoutExpired',
            '검증: 제한 시간을 넘긴 작업을 성공으로 처리하지 않았습니다.']

for line in lesson_timeout():
    print(line)
```

## 실행 결과와 읽는 방법

```text
정상 작업 출력: ok
지연 작업: TimeoutExpired
검증: 제한 시간을 넘긴 작업을 성공으로 처리하지 않았습니다.
```

첫 프로세스는 ok를 출력하고 종료하며, 반환된 표준 출력이 기대값과 같은지 확인합니다. 두 번째 프로세스는 대기하도록 만들고 그보다 짧은 제한 시간을 줍니다. 지정한 예외가 발생했는지 assert로 확인하지만 실제 걸린 시간을 측정하거나 정확한 지연 시간을 보장하지는 않습니다. 실행 환경이 느려도 결과 해석의 기준은 같습니다.

## 적용할 때 주의할 점

timeout은 전체 작업의 모든 단계에 적용되는 하나의 만능 제한이 아닙니다. 프로세스 생성 단계의 지연이나 자식이 다시 만든 다른 프로세스의 정리까지 요구한다면 추가 검토가 필요합니다. HTTP 요청과 브라우저의 탐색에도 별도의 제한 시간이 있습니다. 재시도는 작업이 이미 외부 효과를 냈는지 확인한 뒤 결정해야 합니다.

## 다음 실습에서 확인할 것

종료 코드가 0이라고 원하는 파일이나 외부 결과가 생겼다고 단정하지 않습니다. 예제에서 출력값을 확인한 것처럼 실제 작업에서도 산출물을 확인해야 합니다. 반복 실행할 작업은 제한 시간 초과 시 상태와 오류를 남기고, 다음 실행에서 중복 효과가 생기지 않도록 결과가 불확실한 경우를 분리합니다.

## 코드와 공식 출처

전체 예제와 테스트는 공개 저장소에서 확인할 수 있습니다.

- [예제 코드](https://github.com/kwonseongjae/ai-blog-automation/blob/main/labs/learning_basics.py)
- [검증 테스트](https://github.com/kwonseongjae/ai-blog-automation/blob/main/tests/test_learning_labs.py)
- [공식 문서 1](https://docs.python.org/3.12/library/subprocess.html#subprocess.run)
