# 이슈: `YesmanConfig`에 설정 저장 기능 부재

## 문제 발생 단계

- **계획 파일:** `04-migrate-other-logic.md`
- **작업:** `api/routers/config.py`에 설정 관리 엔드포인트 구현

## 현상

`libs/yesman_config.py`의 `YesmanConfig` 클래스는 `yesman.yaml` 파일에서 설정을 읽어오는 기능(`get`)만 제공하며, 설정을 파일에 다시 저장하는 기능(`set` 또는
`save`)이 구현되어 있지 않습니다.

## 원인 분석

`YesmanConfig`는 현재 읽기 전용으로 설계되었습니다. 설정 변경은 사용자가 `yesman.yaml` 파일을 직접 수정하는 것을 전제로 하고 있는 것으로 보입니다.

## 해결 방안

1. **`config.py` 수정:** 현재 구현 가능한 `GET /config` (설정 조회) 엔드포인트만 구현하고, `POST /config` (설정 저장) 엔드포인트는 주석 처리하거나 임시로 제거합니다.
1. **`YesmanConfig` 확장:** `yesman.yaml` 파일에 변경된 설정 내용을 저장하는 `save(config_data: dict)`와 같은 메서드를 `YesmanConfig` 클래스에 새로
   추가해야 합니다. 이 작업은 별도의 태스크로 관리합니다.

## 후속 조치

- `api/routers/config.py` 파일에서 설정 저장 엔드포인트를 제거합니다.
- `YesmanConfig` 클래스에 설정 저장 기능을 추가하는 작업을 백로그나 새로운 이슈로 등록하고, 해당 기능이 구현된 후에 `POST /config` 엔드포인트를 다시 구현합니다.
