# Task 1.1: 프로젝트 구조 및 환경 설정

**예상 시간**: 2시간  
**선행 조건**: 없음  
**우선순위**: 높음

## 목표
웹 대시보드를 위한 기본 프로젝트 구조를 생성하고 개발 환경을 설정한다.

## 작업 내용

### 1. 디렉토리 구조 생성
```bash
mkdir -p web-dashboard/{static/{js/{components,utils},css/{components,themes},templates},tests}
mkdir -p libs/dashboard/renderers
```

### 2. package.json 생성 및 의존성 설치
```bash
cd web-dashboard
npm init -y
```

package.json 수정:
```json
{
  "name": "yesman-claude-web-dashboard",
  "version": "1.0.0",
  "scripts": {
    "dev": "node build.js --watch",
    "build": "node build.js --production",
    "test": "jest"
  }
}
```

의존성 설치:
```bash
npm install -D esbuild tailwindcss @tailwindcss/forms prettier eslint
npm install alpinejs axios socket.io-client chart.js
```

### 3. 빌드 설정 파일 생성

**web-dashboard/build.js**:
- esbuild 설정
- 개발/프로덕션 모드 구분
- 파일 감시 기능

**web-dashboard/tailwind.config.js**:
- Tauri 대시보드와 동일한 색상 테마
- 다크모드 지원
- 커스텀 컴포넌트 클래스

### 4. ESLint/Prettier 설정
- .eslintrc.json 생성
- .prettierrc 생성
- 코드 스타일 통일

## 완료 기준
- [x] 디렉토리 구조 생성 완료
- [x] package.json 및 의존성 설치 완료
- [x] 빌드 시스템 설정 완료
- [x] 린터 설정 완료
- [x] `npm run dev` 명령어 정상 작동

## 테스트
```bash
cd web-dashboard
npm run dev  # 에러 없이 실행되어야 함
```