# OpenGL-study

## 개발 환경 설정

### Anaconda 환경 관리
1. 환경 내보내기 (메인 컴퓨터)
```bash
conda env export --no-builds > environment.yml
```

2. 환경 생성 (다른 컴퓨터)
```bash
conda env create -f environment.yml
```

3. 환경 업데이트 (패키지 변경 시)
```bash
conda env update -f environment.yml
```

### Git 관리 전략
- environment.yml 파일만 버전 관리
- 실제 conda 환경 폴더는 .gitignore에 추가
- 운영체제 간 호환성 유지