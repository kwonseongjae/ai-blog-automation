# Python 자동화의 하루 기준을 한국 시간으로 정하는 방법

하루 한 번 실행하는 작업에서 먼저 정할 것은 실행 시각과 날짜의 기준입니다. 서버가 UTC를 쓰고 사용자는 한국 날짜로 기록을 본다면, 같은 순간을 서로 다른 날로 판단할 수 있습니다. 이 글에서는 고정된 시각 하나를 변환해 차이를 확인합니다. 실서비스 장애를 재현한 기록이 아니라, 날짜 경계를 이해하기 위한 독립 예제입니다.

## 왜 이 조건을 확인할까

datetime.now()를 인자 없이 호출하면 실행 환경의 로컬 설정에 영향을 받습니다. 작업 상태를 저장할 때와 다음 실행에서 비교할 때 기준이 달라지면 중복 실행이나 누락으로 이어질 수 있습니다. 시간대가 붙은 시각을 만든 다음 Asia/Seoul로 변환해 날짜를 구하면 판단 기준을 코드에 드러낼 수 있습니다.

## 독립 실행 예제

아래 코드는 Python 3.12.3 / Linux에서 실행해 확인했습니다. 입력값은 실습용 고정 자료입니다.

```python
def lesson_timezone():
    from datetime import datetime, timezone
    from zoneinfo import ZoneInfo

    utc = datetime(2026, 11, 12, 15, 1, tzinfo=timezone.utc)
    korean = utc.astimezone(ZoneInfo('Asia/Seoul'))
    assert utc.date().isoformat() == '2026-11-12'
    assert korean.date().isoformat() == '2026-11-13'
    assert korean.tzinfo is not None
    return [f'UTC 날짜: {utc.date()}', f'한국 날짜: {korean.date()}',
            '검증: 같은 순간에도 날짜가 다를 수 있습니다.']

for line in lesson_timezone():
    print(line)
```

## 실행 결과와 읽는 방법

```text
UTC 날짜: 2026-11-12
한국 날짜: 2026-11-13
검증: 같은 순간에도 날짜가 다를 수 있습니다.
```

예제의 UTC 시각은 11월 12일 15시 1분입니다. 한국으로 변환하면 11월 13일이 됩니다. 두 시각은 같은 순간이며 날짜가 다른 이유는 시간대입니다. 문자열에 날짜를 직접 더하거나 9시간을 더한 뒤 시간대 정보를 잃는 방식 대신 astimezone()을 사용합니다. 고정 입력을 쓰므로 언제 실행해도 예제의 결과는 같습니다.

## 적용할 때 주의할 점

시간대가 없는 datetime을 입력받았다면 어느 지역의 시각인지 먼저 확인해야 합니다. replace(tzinfo=...)는 시간대를 표시하는 동작이고 서로 다른 시간대 사이의 변환과는 다릅니다. 또한 ZoneInfo는 시간대 데이터베이스가 필요합니다. 일부 환경에는 tzdata 패키지를 따로 설치해야 하므로 배포 환경에서 확인해야 합니다.

## 다음 실습에서 확인할 것

날짜를 올바르게 구했다고 하루 한 번 실행이 보장되지는 않습니다. 여러 프로세스의 동시 실행, 상태 저장 실패, 이미 완료한 작업의 재시도는 별도로 막아야 합니다. 우선 같은 UTC 입력이 한국 날짜 경계를 넘는지 테스트하고, 그 날짜를 작업 기록의 키로 사용하는 단계까지 확인하면 됩니다.

## 코드와 공식 출처

전체 예제와 테스트는 공개 저장소에서 확인할 수 있습니다.

- [예제 코드](https://github.com/kwonseongjae/ai-blog-automation/blob/main/labs/learning_basics.py)
- [검증 테스트](https://github.com/kwonseongjae/ai-blog-automation/blob/main/tests/test_learning_labs.py)
- [공식 문서 1](https://docs.python.org/3.12/library/zoneinfo.html)
- [공식 문서 2](https://docs.python.org/3.12/library/datetime.html)
