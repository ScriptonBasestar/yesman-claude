# Configuration Hierarchy and Priority

Yesman-Claude는 여러 위치의 설정 파일을 지원하며, 다음과 같은 우선순위로 적용됩니다.

## 설정 파일 우선순위 (높은 순)

1. **환경변수** - 가장 높은 우선순위
   ```bash
   export YESMAN_LOG_LEVEL=debug
   export YESMAN_SESSION_NAME=my-custom-session
   ```

2. **현재 디렉토리 설정**
   ```
   ./yesman.yaml
   ./projects.yaml
   ```

3. **프로젝트별 설정**
   ```
   ~/project/.yesman/yesman.yaml
   ~/project/.yesman/projects.yaml
   ```

4. **사용자 글로벌 설정**
   ```
   ~/.scripton/yesman/yesman.yaml
   ~/.scripton/yesman/projects.yaml
   ~/.scripton/yesman/sessions/*.yaml
   ```

5. **시스템 기본 설정**
   ```
   /etc/yesman/config.yaml
   ```

## 설정 병합 규칙

- 하위 설정이 상위 설정을 오버라이드
- 배열은 병합되지 않고 완전히 대체됨
- 객체는 깊은 병합(deep merge) 수행

## 예시: 설정 병합

### 글로벌 설정 (~/.scripton/yesman/yesman.yaml)
```yaml
log_level: info
log_path: ~/.scripton/yesman/logs/
choice:
  yn: yes
  '123': 1
```

### 프로젝트 설정 (./yesman.yaml)
```yaml
log_level: debug  # 오버라이드
choice:
  yn: yes
  '123': 2      # 오버라이드
  'abc': a      # 추가
```

### 최종 결과
```yaml
log_level: debug  # 프로젝트 설정 우선
log_path: ~/.scripton/yesman/logs/  # 글로벌 설정 유지
choice:
  yn: yes
  '123': 2      # 프로젝트 설정 우선
  'abc': a      # 프로젝트에서 추가
```