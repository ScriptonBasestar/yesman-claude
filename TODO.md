# TODO.md (MVP 필수 기능)

## 이번에 할 작업

- [x] yesman controller 등 controller 개념을 없애고 dashboard에서 사용되는 claude_manager만 사용하기로 했는데 아직도 코드와 문서에 controller이 남아있다. 필요없는 것들은 제거하고 claude_manager와 관련되어서 변경해야 하는것들은 변경해줘.
- [x] Tmux Sessions 화면에서 treenode의 항목을 클릭해서 펼쳤을 때 화면이 리프레시 되면서 도로 닫히는 문제가 있다. 이게 유지될 수 있도록 수정해줘.
- [x] Tmux Sessions 화면에서 treenode의 Template:에서 N/A라는게 보이는데 template이 projects.yaml에 정의되어 있지 않은 상태라면 N/A가 아닌 none이 더 적합하다. N/A는 template이 기록되어 있지만 사용할 수 없는 상태일 때만 나오도록 해줘.
- [x] claude_manager.py의 동작을 검증해. claude_manager는 Controller 의존성을 제거하고 자체적으로 Claude 세션 모니터링 기능을 구현함

## 조금 나중에 할 작업

- [ ] 브랜치 자동분할 멀티 agent 구동기능
  - 여러 브랜치로 자동 분할하여 멀티 에이전트를 구동할 수 있는 기능을 구현합니다. 이 기능은 병렬 처리를 통해 작업 효율성을 높이는 데 기여할 것입니다.

- [ ] LLM으로 출력 판단하여 선택 자동 결정
  - LLM(대형 언어 모델)을 사용하여 출력 내용을 분석하고, 자동으로 적절한 선택을 결정하는 기능을 추가합니다. 이 기능은 자동화된 의사결정을 통해 사용자 개입을 최소화하는 데 도움을 줄 것입니다.
