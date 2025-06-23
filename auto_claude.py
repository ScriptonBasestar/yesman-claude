import pexpect
import sys
import time
import os
import glob
import yaml

# 패턴 디렉토리 경로
PATTERN_DIRS = {
    "yn": os.path.expanduser("~/.yesman/pattern/yn"),
    "123": os.path.expanduser("~/.yesman/pattern/123"),
    "12": os.path.expanduser("~/.yesman/pattern/12"),
}

YESMAN_CONFIG_PATH = os.path.expanduser("~/.yesman/yesman.yaml")

# 설정 파일 로드
def load_config():
    import yaml

    global_path = os.path.expanduser("~/.yesman/yesman.yaml")
    local_path = os.path.abspath("./.yesman/yesman.yaml")

    global_cfg = {}
    local_cfg = {}

    # Load global config if available
    if os.path.exists(global_path):
        with open(global_path, "r", encoding="utf-8") as f:
            global_cfg = yaml.safe_load(f) or {}

    # Load local config if available
    if os.path.exists(local_path):
        with open(local_path, "r", encoding="utf-8") as f:
            local_cfg = yaml.safe_load(f) or {}
    else:
        if global_cfg.get("debug"):
            print("[yesman] 로컬 설정 없음")

    # Determine mode
    mode = local_cfg.get("mode", "merge")

    if mode == "local":
        if not local_cfg:
            raise RuntimeError("mode: local 이지만 ./.yesman/yesman.yaml 이 존재하지 않거나 비어 있음")
        return local_cfg
    elif mode == "merge":
        # Local overrides global
        merged = {**global_cfg, **local_cfg}
        return merged
    else:
        raise ValueError(f"지원되지 않는 설정 모드: {mode}")


# 패턴 파일 로드
def load_patterns():
    patterns_by_group = {}
    for group, path in PATTERN_DIRS.items():
        group_patterns = []
        for file in glob.glob(os.path.join(path, "*.txt")):
            with open(file, encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    group_patterns.append(content)
        patterns_by_group[group] = group_patterns
    return patterns_by_group

# 패턴이 매칭되는지 확인
def match_pattern(buffer, patterns_by_group):
    for group, patterns in patterns_by_group.items():
        for pattern in patterns:
            if pattern in buffer:
                return group, pattern
    return None, None

def run_claude_code():
    config = load_config()
    auto_select_enabled = config.get("auto_select_on_pattern", False)
    auto_select_map = config.get("auto_select", {})
    patterns_by_group = load_patterns()

    child = pexpect.spawn("sbyes claude", encoding='utf-8', timeout=None)
    child.logfile = sys.stdout

    buffer = ""
    last_output_time = time.time()

    print("🚀 Claude Code 자동 제어 시작...\n")

    while True:
        try:
            output = child.read_nonblocking(size=1024, timeout=1)
            buffer += output
            sys.stdout.write(output)
            sys.stdout.flush()
            last_output_time = time.time()

            if len(buffer) > 5000:
                buffer = buffer[-2000:]

        except pexpect.exceptions.TIMEOUT:
            idle_time = time.time() - last_output_time

            if (auto_select_map or auto_select_enabled) and idle_time >= 1.0:
                matched_group, matched = match_pattern(buffer, patterns_by_group)
                if matched_group:
                    if matched_group in auto_select_map:
                        answer = auto_select_map[matched_group]
                        print(f"\n🧠 매칭된 그룹: '{matched_group}' 패턴: '{matched}' → '{answer}' 자동 선택\n")
                        child.sendline(str(answer))
                    elif auto_select_enabled:
                        print(f"\n🧠 매칭된 그룹: '{matched_group}' 패턴: '{matched}' → '1' 자동 선택\n")
                        child.sendline("1")
                    buffer = ""
                    continue

        except pexpect.exceptions.EOF:
            print("\n✅ 프로세스 종료됨")
            break
        except Exception as e:
            print(f"[에러] {e}")
            break

if __name__ == "__main__":
    run_claude_code()
