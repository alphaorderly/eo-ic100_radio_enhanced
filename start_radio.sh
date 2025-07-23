#!/bin/bash

# FM Radio Enhanced 시작 스크립트
# macOS에서 sudo 없이 USB 장치에 접근하기 위한 설정

echo "FM Radio Enhanced 시작 중..."
echo "USB 장치 권한 설정..."

# USB 장치 찾기 및 권한 설정
for device in /dev/tty.usbserial-* /dev/cu.usbserial-*; do
    if [ -e "$device" ]; then
        echo "USB 장치 발견: $device"
        # 현재 사용자가 읽기/쓰기 권한을 가지도록 설정
        sudo chmod 666 "$device" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "권한 설정 완료: $device"
        else
            echo "권한 설정 실패: $device (관리자 권한 필요)"
        fi
    fi
done

# 일반 사용자 권한으로 Python 애플리케이션 실행
echo "애플리케이션 시작..."
export PYTHONPATH="$(pwd):$PYTHONPATH"

# GUI 애플리케이션을 일반 사용자 권한으로 실행
python3 main.py

echo "애플리케이션 종료됨."
