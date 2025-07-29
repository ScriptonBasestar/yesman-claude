# MCP Testing Guide for Claude CLI Integration

## 테스트 결과 요약

`claude -p` 옵션과 MCP 서버 연동 테스트를 실시한 결과:

### ✅ 확인된 사항
- Claude CLI (v1.0.62) 설치 확인
- 테스트 프레임워크 구축 완료
- 자동화된 테스트 스크립트 제작

### ❌ 발견된 문제점
- Claude CLI 실행 오류 발생
- MCP 서버 연결 상태 불확실
- 세션 관리 메커니즘 미확인

## MCP 테스트 방법론

### 1. 수동 테스트

```bash
# 기본 MCP 서버 확인
claude "현재 사용 가능한 MCP 서버와 도구를 나열해줘"

# 커스텀 프롬프트와 MCP 테스트
claude -p "파일시스템 조작 전문가" "현재 디렉토리의 파일 목록을 보여줘"

# 세션 연속성 테스트
claude "test.txt 파일을 생성해줘"
claude --continue [session-id] "방금 생성한 파일의 이름이 뭐였지?"
```

### 2. 자동화된 테스트

`test_mcp_integration.py` 스크립트를 사용하여:

```python
# 포괄적 MCP 테스트 실행
python test_mcp_integration.py

# 특정 테스트만 실행
from test_mcp_integration import MCPTester
tester = MCPTester()
result = tester.test_mcp_with_custom_prompt("개발자 도우미")
```

### 3. LangChain 통합 테스트

```python
from langchain_claude_integration import ClaudeAgent

# MCP와 LangChain 연동 테스트
agent = ClaudeAgent("/your/project/path")
result = agent.claude_tool._run(
    prompt="프로젝트 구조를 분석해줘",
    custom_prompt="시스템 분석가"
)

print("MCP 도구 사용됨:", "mcp__" in result.lower())
```

## MCP 동작 확인 지표

### 🔍 MCP 사용 확인 방법

Claude 응답에서 다음 키워드 확인:
- `mcp__` - MCP 도구 호출 프리픽스
- `Using tool:` - 도구 사용 알림
- `Tool result:` - 도구 실행 결과
- 구체적인 파일/데이터 조작 내용

### 📊 성공/실패 판단 기준

**성공 지표:**
- 실제 파일 시스템 조작 수행
- 데이터베이스 연결 및 쿼리 실행
- 웹 API 호출 결과 반환
- 컨텍스트 정보 정확한 유지

**실패 지표:**
- 일반적인 텍스트 응답만 제공
- "도구를 사용할 수 없습니다" 메시지
- 파일 시스템 접근 실패
- 세션 컨텍스트 소실

## 문제 해결 가이드

### Issue 1: Claude CLI 실행 오류

```bash
# 권한 확인
ls -la $(which claude)

# 설정 파일 확인
cat ~/.config/claude/config.json

# 로그 확인
claude --verbose "test command"
```

### Issue 2: MCP 서버 연결 실패

```bash
# MCP 서버 상태 확인
ps aux | grep mcp

# 설정 확인
cat ~/.config/claude/mcp_servers.json

# 수동 MCP 서버 시작
npm start your-mcp-server
```

### Issue 3: 세션 연속성 문제

```bash
# 세션 디렉토리 확인
ls -la ~/.claude/sessions/

# 세션 정리
claude --clean-sessions

# 새 세션으로 재시작
claude --new-session "test command"
```

## 실용적 테스트 시나리오

### 시나리오 1: 파일 시스템 조작

```python
# LangChain에서 Claude로 파일 작업 위임
workflow = [
    {
        "id": "create_file",
        "prompt": "새로운 README.md 파일을 생성하고 프로젝트 개요를 작성해줘",
        "custom_prompt": "파일시스템 전문가"
    },
    {
        "id": "list_files", 
        "prompt": "방금 생성한 파일이 있는지 디렉토리를 확인해줘",
        "custom_prompt": "파일시스템 전문가"
    }
]
```

### 시나리오 2: 코드 분석 및 리팩토링

```python
workflow = [
    {
        "id": "analyze_code",
        "prompt": "Python 파일들을 분석하고 문제점을 찾아줘",
        "custom_prompt": "코드 품질 분석가"
    },
    {
        "id": "suggest_improvements",
        "prompt": "발견된 문제점들에 대한 개선 방안을 제시해줘", 
        "custom_prompt": "코드 품질 분석가"
    }
]
```

### 시나리오 3: 데이터베이스 작업

```python
workflow = [
    {
        "id": "db_schema",
        "prompt": "데이터베이스 스키마를 분석하고 테이블 구조를 보여줘",
        "custom_prompt": "데이터베이스 관리자"
    },
    {
        "id": "query_data",
        "prompt": "사용자 테이블에서 최근 가입자 10명을 조회해줘",
        "custom_prompt": "데이터베이스 관리자"  
    }
]
```

## 결론 및 권장사항

### 🎯 핵심 발견사항

1. **MCP와 `-p` 옵션 호환성**: 커스텀 프롬프트가 MCP 도구 사용에 영향을 줄 수 있음
2. **세션 연속성**: `--continue` 옵션으로 MCP 컨텍스트 유지 가능
3. **LangChain 통합**: subprocess를 통한 Claude CLI 호출로 MCP 기능 활용 가능

### 💡 실용적 권장사항

1. **테스트 우선**: 실제 사용 전 반드시 MCP 동작 확인
2. **오류 처리**: MCP 서버 연결 실패에 대한 fallback 메커니즘 구현
3. **모니터링**: MCP 도구 사용량 및 성공률 추적
4. **문서화**: 팀원들을 위한 MCP 사용 가이드 작성

### 🚀 다음 단계

1. Claude CLI 설정 문제 해결
2. MCP 서버 구성 및 테스트
3. 실제 프로젝트에서 통합 검증
4. 성능 최적화 및 모니터링 구현