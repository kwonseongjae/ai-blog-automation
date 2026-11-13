# 터미널에서는 되는데 예약 실행에서는 파일을 못 찾는 이유

프로그램을 실행한 위치가 바뀌면 같은 상대경로가 다른 파일을 가리킬 수 있습니다. 예약 실행이나 다른 폴더에서 호출할 때 파일을 찾지 못하는 상황을 작은 디렉터리 두 개로 확인합니다. 실제 운영 중의 장애 원인을 단정하는 글이 아니라 경로 해석을 직접 비교하는 실습입니다.

## 왜 이 조건을 확인할까

data/example.txt는 프로그램 파일이 있는 곳이 아니라 현재 작업 디렉터리를 기준으로 해석됩니다. 이 기준을 생략하면 호출하는 사람이 폴더를 먼저 옮겨야 정상 동작하는 프로그램이 됩니다. pathlib의 Path 객체로 기준 디렉터리와 데이터 경로를 조합하면 경로의 의도를 읽기 쉽고 운영체제의 구분자 차이도 덜 신경 쓸 수 있습니다.

## 독립 실행 예제

아래 코드는 Python 3.12.3 / Linux에서 실행해 확인했습니다. 입력값은 실습용 고정 자료입니다.

```python
def lesson_paths():
    from pathlib import Path
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as directory:
        base = Path(directory)
        data = base / 'data'
        data.mkdir()
        (data / 'example.txt').write_text('학습 기록', encoding='utf-8')
        nested = base / 'other'
        nested.mkdir()
        assert (base / 'data/example.txt').read_text(encoding='utf-8') == '학습 기록'
        assert not (nested / 'data/example.txt').exists()
        assert not (base / '../outside').resolve().is_relative_to(base.resolve())
    return ['기준 경로에서 읽기: 성공', '다른 작업 경로에서 같은 상대경로: 파일 없음',
            '검증: 기준 디렉터리 밖 경로를 구분했습니다.']

for line in lesson_paths():
    print(line)
```

## 실행 결과와 읽는 방법

```text
기준 경로에서 읽기: 성공
다른 작업 경로에서 같은 상대경로: 파일 없음
검증: 기준 디렉터리 밖 경로를 구분했습니다.
```

예제는 임시 디렉터리 안에 data/example.txt를 만들고 같은 기준에서 읽습니다. 다른 하위 폴더를 기준으로 같은 상대경로를 조합하면 파일이 없습니다. 실제 파일을 옮기거나 현재 디렉터리를 바꾸지 않고 두 기준을 직접 비교하므로 테스트가 다른 작업에 영향을 주지 않습니다. 임시 디렉터리는 블록이 끝나면 정리됩니다.

## 적용할 때 주의할 점

파일 기반 스크립트에서는 Path(__file__).resolve().parent를 기준으로 삼을 수 있지만, 노트북이나 실행 패키지는 상황이 다릅니다. 사용자 데이터 경로를 프로그램 코드 위치에 고정하는 것이 항상 정답은 아닙니다. 또한 resolve()는 심볼릭 링크를 해석하므로 허용 디렉터리 밖으로 나가는 입력을 검사할 때 의미가 달라질 수 있습니다.

## 다음 실습에서 확인할 것

실제 예약 작업에는 실행 위치를 명시하고, 프로그램 내부에서도 코드·설정·사용자 데이터의 경로를 구분합니다. 사용자에게서 받은 파일명을 사용할 때는 기준 디렉터리 밖으로 나가지 않는지도 확인해야 합니다. 경로 문제가 의심될 때 현재 작업 위치와 최종 해석된 경로부터 비교하면 원인을 좁힐 수 있습니다.

## 코드와 공식 출처

전체 예제와 테스트는 공개 저장소에서 확인할 수 있습니다.

- [예제 코드](https://github.com/kwonseongjae/ai-blog-automation/blob/main/labs/learning_basics.py)
- [검증 테스트](https://github.com/kwonseongjae/ai-blog-automation/blob/main/tests/test_learning_labs.py)
- [공식 문서 1](https://docs.python.org/3.12/library/pathlib.html)
