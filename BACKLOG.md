- Add Validation for Template References
  - 관련 ISSUE: Add Validation for Template References (Issue #4)
  - 보류 사유: 현재 대부분의 프로젝트가 "template: none"을 사용하고 있어 우선순위가 낮음. 기존 validation이 충분함.

- Verify and Update Project Path Configuration
  - 관련 ISSUE: Project Path Inconsistency (Issue #8)
  - 보류 사유: 사용자와 정확한 프로젝트 구조 확인 필요. 실제 디렉토리 구조가 문서와 불일치할 수 있음.

## 조금 나중에 할 작업

- [ ] 브랜치 자동분할 멀티 agent 구동기능
  - 여러 브랜치로 자동 분할하여 멀티 에이전트를 구동할 수 있는 기능을 구현합니다. 이 기능은 병렬 처리를 통해 작업 효율성을 높이는 데 기여할 것입니다.
  - git remote 에서 branch를 나눠서 작업개시
  - develop에서 작업중이었다면 develop에서 feat/issuename으로 작업처리
  - 완료확인을 하면 rebase, merge. 충돌발생시 바로 합쳐서 처리하지 않고 각 feat/issuename에서 처리 후 다시 합치기. 여러개 브랜치가 있기 때문에 충돌발생시 각각의 브랜치에서 수정후 합쳐야 예상못했던 오류가 발생하지 않는다.(사람이 협업할 때 처럼)

- [ ] LLM으로 출력 판단하여 선택 자동 결정
  - LLM(대형 언어 모델)을 사용하여 출력 내용을 분석하고, 자동으로 적절한 선택을 결정하는 기능을 추가합니다. 이 기능은 자동화된 의사결정을 통해 사용자 개입을 최소화하는 데 도움을 줄 것입니다.

- [ ] 묻지마 1찍기능 데모크라쉬
