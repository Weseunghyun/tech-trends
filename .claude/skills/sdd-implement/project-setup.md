# 프로젝트 설정 검증

## 무시 파일 감지 및 생성 로직

실제 프로젝트 설정에 기반하여 무시 파일을 생성/검증합니다.

### 감지 규칙

- git 저장소인지 확인 (`git rev-parse --git-dir 2>/dev/null`) → .gitignore
- Dockerfile* 또는 plan.md에 Docker → .dockerignore
- .eslintrc* → .eslintignore
- eslint.config.* → config의 `ignores` 항목 확인
- .prettierrc* → .prettierignore
- .npmrc 또는 package.json → .npmignore (배포 시)
- *.tf → .terraformignore
- helm 차트 존재 → .helmignore

### 파일 처리

- **이미 존재**: 필수 패턴이 포함되어 있는지 확인, 누락된 중요 패턴만 추가
- **없는 경우**: 감지된 기술에 대한 전체 패턴 세트로 생성

### 기술별 일반 패턴

| 기술 | 패턴 |
|------|------|
| Node.js/JS/TS | `node_modules/`, `dist/`, `build/`, `*.log`, `.env*` |
| Python | `__pycache__/`, `*.pyc`, `.venv/`, `venv/`, `dist/`, `.env`, `*.key`, `*-sa.json`, `service-account*.json` (시크릿 커밋 방지, SEC-09) |
| Java | `target/`, `*.class`, `*.jar`, `.gradle/`, `build/` |
| C#/.NET | `bin/`, `obj/`, `*.user`, `*.suo`, `packages/` |
| Go | `*.exe`, `*.test`, `vendor/`, `*.out` |
| Ruby | `.bundle/`, `log/`, `tmp/`, `*.gem` |
| PHP | `vendor/`, `*.log`, `*.cache`, `*.env` |
| Rust | `target/`, `debug/`, `release/`, `.idea/`, `.env*` |
| Kotlin | `build/`, `out/`, `.gradle/`, `.idea/` |
| C/C++ | `build/`, `bin/`, `obj/`, `*.o`, `*.so`, `*.exe` |
| Swift | `.build/`, `DerivedData/`, `*.swiftpm/` |
| 공통 | `.DS_Store`, `Thumbs.db`, `*.tmp`, `.vscode/`, `.idea/` |

### 도구별 패턴

| 도구 | 패턴 |
|------|------|
| Docker | `node_modules/`, `.git/`, `*.log*`, `.env*`, `coverage/` |
| ESLint | `node_modules/`, `dist/`, `build/`, `coverage/` |
| Prettier | `node_modules/`, `dist/`, `package-lock.json`, `yarn.lock` |
| Terraform | `.terraform/`, `*.tfstate*`, `*.tfvars` |
| K8s | `*.secret.yaml`, `secrets/`, `.kube/`, `*.key`, `*.crt` |
