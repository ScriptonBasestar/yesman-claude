# Yesman Agent Tauri Dashboard

## 개요

Yesman Agent의 Tauri 기반 데스크톱 대시보드입니다. 실시간 모니터링, 성능 분석, 배포 관리 등의 기능을 제공합니다.

## 주요 기능

### 🔍 시스템 모니터링
- 실시간 시스템 리소스 사용량 모니터링
- CPU, 메모리, 디스크 사용률 추적
- 네트워크 연결 상태 모니터링

### 🏥 상태 점검
- 서비스 헬스 체크
- 컴포넌트별 상태 추적
- 자동 장애 감지 및 알림

### 📊 성능 분석
- 응답시간 메트릭 수집
- 성능 트렌드 분석
- 병목 지점 식별

### 🚀 배포 관리
- 카나리 배포 지원
- 자동 롤백 기능
- 배포 진행 상황 모니터링

### 📋 프로세스 관리
- 실행 중인 프로세스 모니터링
- 프로세스 시작/중지 제어
- 리소스 사용량 추적

## 기술 스택

- **Frontend**: SvelteKit + TypeScript
- **Backend Bridge**: Tauri (Rust)
- **UI Framework**: DaisyUI + Tailwind CSS
- **State Management**: Svelte Stores
- **Build Tool**: Vite

## 프로젝트 구조

```
tauri-dashboard/
├── src/                    # 프론트엔드 소스코드
│   ├── lib/               # 라이브러리 및 컴포넌트
│   │   ├── components/    # Svelte 컴포넌트
│   │   ├── stores/        # 상태 관리
│   │   ├── utils/         # 유틸리티 함수
│   │   └── types/         # TypeScript 타입 정의
│   ├── routes/            # 페이지 라우트
│   └── app.html           # HTML 템플릿
├── src-tauri/             # Tauri Rust 백엔드
│   ├── src/               # Rust 소스코드
│   └── Cargo.toml         # Rust 의존성 설정
├── static/                # 정적 파일
├── tests/                 # 테스트 파일
└── docs/                  # 문서
```

## 개발 환경 설정

### 필수 요구사항

- Node.js 18+
- Rust 1.70+
- Tauri CLI

### 설치 및 실행

```bash
# 의존성 설치
pnpm install

# 개발 서버 실행
pnpm tauri dev

# 프로덕션 빌드
pnpm tauri build
```

## 컴포넌트 가이드

### Health Status Indicator
시스템 전반의 상태를 표시하는 컴포넌트입니다.

```svelte
<HealthStatusIndicator 
  showDetails={true} 
  size="lg" 
  orientation="horizontal" 
/>
```

### Connection Status Badge
연결 상태를 실시간으로 표시하는 배지 컴포넌트입니다.

```svelte
<ConnectionStatusBadge 
  showText={true} 
  showIcon={true} 
  size="md" 
  clickable={true} 
/>
```

### Troubleshooting Widget
문제 해결 및 진단 기능을 제공하는 위젯입니다.

```svelte
<TroubleshootingWidget 
  title="문제 해결" 
  showAdvanced={false} 
/>
```

### Onboarding Wizard
신규 사용자를 위한 온보딩 가이드입니다.

```svelte
<OnboardingWizard 
  title="시작하기 가이드" 
  autoStart={false} 
/>
```

## API 사용법

### Health Status API

```typescript
import { api } from '$lib/utils/api';

// 헬스 상태 조회
const response = await api.getHealthStatus();
if (response.success) {
  console.log('Overall status:', response.data.overall);
}

// 헬스 체크 실행
await api.runHealthCheck();
```

### Performance Metrics API

```typescript
// 성능 메트릭 조회
const metrics = await api.getPerformanceMetrics();
if (metrics.success) {
  console.log('CPU usage:', metrics.data.cpu.percent);
  console.log('Memory usage:', metrics.data.memory.percent);
}
```

## 상태 관리

### Health Store

```typescript
import { health, healthStatus, isHealthy } from '$lib/stores/health';

// 상태 구독
health.subscribe(status => {
  console.log('Health status changed:', status);
});

// 상태 업데이트
updateHealthStatus('database', 'healthy', 'Connection successful');
```

## 배포

### 개발 빌드
```bash
pnpm run build
```

### 프로덕션 빌드
```bash
pnpm tauri build
```

빌드된 파일은 `src-tauri/target/release/bundle/` 디렉토리에 생성됩니다.

## 문제 해결

### 일반적인 문제

1. **빌드 실패**: Node.js와 Rust 버전을 확인하세요
2. **Tauri 에러**: `pnpm tauri info`로 환경을 확인하세요
3. **의존성 문제**: `pnpm install`을 다시 실행하세요

### 로그 확인

개발 모드에서는 브라우저 개발자 도구의 콘솔에서 로그를 확인할 수 있습니다.

## 기여하기

1. 이슈를 생성하여 버그 리포트 또는 기능 요청을 해주세요
2. Fork 후 기능 브랜치를 생성하세요
3. 커밋은 의미있는 단위로 나누어 주세요
4. Pull Request를 생성하세요

## 라이선스

MIT License