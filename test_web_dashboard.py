#!/usr/bin/env python3
"""
임시 웹 대시보드 테스트 스크립트
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from commands.dashboard import launch_web_dashboard

if __name__ == "__main__":
    print("🌐 Starting Web Dashboard Test...")
    launch_web_dashboard(host="localhost", port=8080, dev=True)