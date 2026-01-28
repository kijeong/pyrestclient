# 데스크탑 REST 클라이언트

## 0) 목표

* Rocky Linux 9에서 개발/실행 가능한 **GUI 기반 REST API 테스트 클라이언트** 프로토타입을 만든다.(Insomnia 유사)
* 향후 Windows 11 / macOS 15+까지 확장 가능한 구조로 설계한다(초기 구현은 Rocky 9 중심).
* 초기 저장소는 **JSON 파일**로 한다(나중에 SQLite로 쉽게 마이그레이션 가능하도록 설계).


## 1) 타깃 런타임/버전 고정

* OS(개발): Rocky Linux 9.x
* Python: 3.14
* GUI: **PySide6 (Qt for Python)**

### 1.1 필수/선택 설치 항목

* 필수
  * PySide6
  * httpx
* 선택
  * PyInstaller (배포용)
  * pytest (테스트 실행)

### 1.2 패키지 버전 정책(권장)

* 기본 방침: 안정 버전 고정(semantic version pin)
  * 예: `pyside6==X.Y.Z`, `httpx==X.Y.Z`
* 보안 패치 반영을 위해 정기적으로 버전 점검
* 배포용(PyInstaller) 버전은 빌드 재현성을 위해 고정


## 2) 프로토타입 범위(MVP)

### 2.1 UI 기능

* 메인 레이아웃(권장: Qt Widgets)

  * 좌측: Collections/폴더 트리
  * 중앙: Request 편집(메서드, URL, 헤더, 바디 탭)
  * 하단/우측: Response 뷰(Body/Headers 탭, status code, elapsed time)
  * 상단: Send / Cancel 버튼, **Environment 선택/관리**
* 탭 기반 멀티 요청 편집(최소 1개 탭은 필수)
* Environment 관리자 (Global/Collection 변수 편집) UI

### 2.2 HTTP 기능

* GET/POST/PUT/PATCH/DELETE
* headers/query/body 지원
* Body 타입(최소):

  * raw text
  * JSON(pretty print)
  * x-www-form-urlencoded(가능하면)
  * Multipart/form-data (파일 업로드 - 후순위지만 MVP 고려)
* Auth 지원 (MVP):
  * No Auth
  * Basic Auth
  * Bearer Token
* Timeout
* Cancel(중요): UI가 멈추지 않게 “비동기 실행 + 취소” 보장
* 네트워크 고급 (개발자 필수):
  * Proxy 설정 (HTTP/HTTPS)
  * SSL Verification Toggle (Self-signed 인증서 허용)
  * Redirect Follow Toggle

### 2.3 UI/UX 편의성
* 단축키: Send Request (Ctrl+Enter / Cmd+Enter)
* 응답 뷰어:
  * Copy to Clipboard
  * Search (Find in text)
  * Word Wrap Toggle
* 폰트: 에디터 영역 Monospace 폰트 및 크기 조절

### 2.4 저장 기능(초기 JSON)

* workspace 저장/로드
* 최소 저장 대상:

  * collections / folders / requests / environments / meta(schema_version)
* Atomic write(저장 중 크래시로 파일 깨짐 방지)

### 2.5 비범위(후순위)

* OAuth2 고급 플로우, WebSocket/SSE, gRPC, 협업/동기화, Pre-request/Test scripting

### 2.6 시스템/디버깅
* Logging: 파일 및 콘솔 로그 (Crash 분석용)
* Global Exception Handler: UI 멈춤 방지 및 에러 다이얼로그

### 2.7 배포 (Distribution)
* Target: Rocky Linux 9 (x86_64)
* 패키징: PyInstaller (Single File or Directory)
* 형식: AppImage (권장 - 이식성 높음) 또는 RPM

---

## 3) 아키텍처 원칙(중요)

### 3.1 UI와 Core 분리

* UI(Pyside6)는 “표시/입력”만 책임지고,
* core는 “요청 모델/실행/저장/변수치환”만 책임지게 분리.

> 이유: 나중에 SQLite로 저장소 바꾸거나, CLI 러너 붙이거나, Windows/macOS 패키징할 때 고통이 급감.

### 3.2 저장소 추상화

* `Storage` 인터페이스(혹은 Protocol)로 추상화

  * `load_workspace()`, `save_workspace(workspace)`
  * `append_history(entry)` (선택)
* 초기 구현: `JsonFileStorage`
* 후속 구현: `SqliteStorage` (마이그레이션 로직 포함)

### 3.3 비동기 실행 모델

* UI 스레드에서 네트워크 호출 금지.

* 최소 요건:

  * 요청 실행은 worker(스레드/태스크)에서 수행
  * 완료/실패/취소는 signal로 UI에 전달
* 구현 선택지(Claude가 선택):

  * (A) QThread/QRunnable 기반 워커
  * (B) asyncio + Qt 이벤트루프 브리지(qasync)
* MVP에선 (A)가 단순하고 안정적인 편.

---

## 5) 프로젝트 구조(권장)

```
rest-client/
  app/
    main.py              # 엔트리
    ui/
      main_window.py
      panels/
        collection_tree.py
        request_editor.py
        response_viewer.py
  core/
    config.py            # 앱 설정 (폰트, 테마, 프록시 등)
    logger.py            # 로깅 설정
    model.py             # Request/Response/Workspace dataclasses
    http_client.py        # httpx 기반 실행기(순수 로직)
    template.py           # {{var}} 치환
    storage/
      base.py             # Storage 인터페이스
      json_storage.py     # workspace.json 저장/로드 + atomic write
      history_jsonl.py    # (선택) history.jsonl append
  workers/
    request_worker.py     # 비동기 실행/취소 래퍼
  resources/
    icons/
    sample_workspace.json
  tests/
    test_template.py
    test_storage_json.py
    test_http_building.py
  requirements.txt
  README.md
```

---

## 6) 데이터/저장(JSON) 명세

### 6.1 Workspace 포맷(필수 필드)

* 최상단:

  * `schema_version: int` (필수)
  * `updated_at` (선택)
* 엔티티는 “중첩 트리”보다 **ID 참조형(정규화 스타일)** 권장:

  * `collections[]`: `{id, name, ...}`
  * `folders[]`: `{id, collection_id, parent_id|null, name, order}`
  * `requests[]`: `{id, folder_id, name, method, url, headers[], query[], body, auth, timeout_ms}`
  * `environments[]`: `{scope: global|collection|request, owner_id, vars{...}}`

### 6.2 Atomic write

* 저장 시:

  * 임시파일에 먼저 기록
  * fsync(가능하면)
  * rename으로 교체


## 7) 구현 우선순위(마일스톤)

### M1: UI 골격

* 메인 윈도우 레이아웃 완성(좌/중/하)
* Dummy 데이터로 트리/에디터/뷰어 연결

### M2: HTTP 실행 + 표시

* httpx로 요청 실행(비동기)
* 응답 status/headers/body 표시
* JSON pretty print
* Timeout 처리
* Basic Auth / Bearer Token 지원

### M3: 시스템 & 네트워크 고급

* Logging & Exception Handler 적용
* Proxy / SSL Verification 설정
* Environment 변수 치환 로직 연동

### M4: Cancel

* 진행 중 요청 취소
* UI 상태 복구(버튼/스피너/상태바)
* 연속 요청에서도 UI 프리즈 없음

### M5: JSON 저장/로드

* workspace.json 저장/로드
* schema_version 포함
* atomic write 적용
* Environment 데이터 저장/로드

(선택) M6: History JSONL

* history.jsonl append 방식
* UI에 최근 요청 목록 표시


