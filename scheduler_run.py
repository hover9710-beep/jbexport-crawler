import requests
import json
from datetime import datetime
from pathlib import Path

URL = "http://127.0.0.1:5000/api/jbexport/run"

# 로그 폴더 자동 생성
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# 로그 파일명
now_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_file = log_dir / f"scheduler_run_{now_str}.log"

try:
    # API 호출
    r = requests.post(URL, timeout=120)

    # 응답 텍스트 먼저 확인
    text = r.text

    # JSON 변환 시도
    try:
        result = r.json()
    except Exception:
        result = {
            "status": "error",
            "message": "JSON 응답 아님",
            "raw_text": text
        }

    output = {
        "run_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status_code": r.status_code,
        "result": result
    }

    # 화면 출력
    print(json.dumps(output, ensure_ascii=False, indent=2))

    # 로그 저장
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

except Exception as e:
    error_output = {
        "run_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "error",
        "error": str(e)
    }

    print(json.dumps(error_output, ensure_ascii=False, indent=2))

    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(error_output, f, ensure_ascii=False, indent=2)