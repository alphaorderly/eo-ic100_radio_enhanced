# FM Radio Enhanced

Samsung Galaxy 이어폰의 FM 라디오 기능을 PC/Mac에서 사용할 수 있는 애플리케이션입니다.

> 이 프로젝트는 [kjy00302/eo-ic100_radio](https://github.com/kjy00302/eo-ic100_radio)를 포크하여 개선한 버전입니다.
>
> **주요 개선사항:**
>
> - 현대적인 GUI 인터페이스
> - 오디오 팝 사운드 방지 기능
> - 크로스 플랫폼 지원 (Windows/macOS)
> - 사용자 친화적인 설치 및 실행

## 지원 기기

- Samsung Galaxy 이어폰 (EO-IC100 시리즈)
- USB로 연결 가능한 Samsung Galaxy 스마트폰

## 다운로드 및 설치

### 1. 실행 파일 다운로드 (권장)

**[릴리스 페이지](../../releases)**에서 운영체제에 맞는 파일을 다운로드하세요:

- **Mac 사용자**: `FM-Radio-Enhanced-macOS-arm64.tar.gz` 다운로드
- **Windows 사용자**: `FM-Radio-Enhanced-Windows-x64.zip` 다운로드

### 2. 설치 및 실행

#### Mac 사용자

1. 다운로드한 파일을 더블클릭해서 압축 해제
2. 터미널을 열고 압축 해제된 폴더로 이동
3. 다음 명령어로 실행:
   ```bash
   sudo ./FM-Radio-Enhanced-macOS-arm64
   ```

#### Windows 사용자

1. 다운로드한 ZIP 파일을 압축 해제
2. `FM-Radio-Enhanced-Windows-x64.exe` 파일을 더블클릭해서 실행

## 사용법

1. **기기 연결**: Samsung Galaxy 이어폰이나 스마트폰을 USB로 컴퓨터에 연결
2. **애플리케이션 실행**: 위 설치 방법에 따라 프로그램 실행
3. **기기 선택**: 연결된 기기 목록에서 FM 라디오 지원 기기 선택
4. **라디오 청취**: Power 버튼을 눌러 라디오 켜고 주파수 조정

## 주요 기능

- **주파수 조정**: +1.0, +0.1 MHz 단위로 정밀 조정
- **볼륨 조절**: 0-15 단계 볼륨 조절
- **프리셋 저장**: 즐겨듣는 주파수 6개까지 저장
- **자동 스캔**: 수신 가능한 방송국 자동 검색
- **RDS 정보**: 방송국 이름 및 곡 정보 표시

## 문제 해결

### Mac에서 "권한 거부" 오류가 발생하는 경우

- 반드시 `sudo` 명령어를 사용해서 실행하세요
- USB 기기를 다시 연결해보세요

### Windows에서 실행이 안 되는 경우

- 관리자 권한으로 실행해보세요
- Windows Defender에서 차단했는지 확인하세요

### 기기가 인식되지 않는 경우

- USB 케이블을 다시 연결해보세요
- 다른 USB 포트를 사용해보세요
- Samsung Galaxy 기기에서 USB 디버깅이 활성화되어 있는지 확인하세요

## 원본 프로젝트

이 프로젝트는 [kjy00302](https://github.com/kjy00302)님의 [eo-ic100_radio](https://github.com/kjy00302/eo-ic100_radio) 프로젝트를 기반으로 개발되었습니다. 원본 프로젝트에 감사드립니다.

## 라이센스

이 프로젝트는 오픈소스입니다.
