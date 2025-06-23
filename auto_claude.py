import pexpect
import sys
import time
import os
import glob
import yaml
import logging
import signal
import shutil

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
    # Check last 1000 chars for better matching
    recent_buffer = buffer[-1000:] if len(buffer) > 1000 else buffer
    
    for group, patterns in patterns_by_group.items():
        for pattern in patterns:
            if pattern.lower() in recent_buffer.lower():
                return group, pattern
    return None, None

def run_claude_code():
    config = load_config()
    
    # Get choice configuration (previously auto_select)
    choice_config = config.get("choise", config.get("choice", {}))
    patterns_by_group = load_patterns()
    
    # Set up logging
    log_level = config.get("log_level", "INFO").upper()
    log_path = config.get("log_path", "~/tmp/logs/yesman/")
    log_path = os.path.expanduser(log_path)
    os.makedirs(log_path, exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_path, "auto_claude.log")),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger("auto_claude")
    
    logger.info(f"Loaded config: {config}")
    logger.info(f"Choice config: {choice_config}")
    logger.info(f"Loaded patterns: {patterns_by_group}")

    child = pexpect.spawn("claude", encoding='utf-8', timeout=None)
    # Adjust child pty size to match current terminal
    rows, cols = shutil.get_terminal_size()
    child.setwinsize(rows, cols)
    signal.signal(signal.SIGWINCH, lambda sig, frm: child.setwinsize(*shutil.get_terminal_size()))
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

            # Check more frequently for patterns (0.5 seconds instead of 1.0)
            if choice_config and idle_time >= 0.5:
                # Log current buffer for debugging
                logger.debug(f"Buffer content (last 500 chars): {buffer[-500:]}")
                
                matched_group, matched = match_pattern(buffer, patterns_by_group)
                if matched_group and matched_group in choice_config:
                    answer = choice_config[matched_group]
                    logger.info(f"Pattern matched - Group: '{matched_group}', Pattern: '{matched}', Auto-selecting: '{answer}'")
                    print(f"\n🧠 매칭된 그룹: '{matched_group}' 패턴: '{matched}' → '{answer}' 자동 선택\n")
                    child.sendline(str(answer))
                    buffer = ""
                    continue
                else:
                    # Check for common Claude prompts even without pattern files
                    recent_buffer = buffer[-500:] if len(buffer) > 500 else buffer
                    
                    # Check for numbered options (looking for patterns like "1) " or "1. ")
                    has_option_1 = any(pattern in recent_buffer for pattern in ["1)", "1.", "1:"])
                    has_option_2 = any(pattern in recent_buffer for pattern in ["2)", "2.", "2:"])
                    has_option_3 = any(pattern in recent_buffer for pattern in ["3)", "3.", "3:"])
                    
                    # Yes/No patterns
                    if any(keyword in recent_buffer.lower() for keyword in ["(y/n)", "yes/no", "continue?", "proceed?"]):
                        if "yn" in choice_config:
                            answer = choice_config["yn"]
                            logger.info(f"Default y/n pattern detected, auto-selecting: '{answer}'")
                            print(f"\n🧠 기본 yes/no 패턴 감지 → '{answer}' 자동 선택\n")
                            child.sendline(str(answer))
                            buffer = ""
                            continue
                    # 1-3 options
                    elif has_option_1 and has_option_2 and has_option_3:
                        if "123" in choice_config:
                            answer = choice_config["123"]
                            logger.info(f"Default 1-3 pattern detected, auto-selecting: '{answer}'")
                            print(f"\n🧠 기본 1-3 선택 패턴 감지 → '{answer}' 자동 선택\n")
                            child.sendline(str(answer))
                            buffer = ""
                            continue
                    # 1-2 options
                    elif has_option_1 and has_option_2 and not has_option_3:
                        if "12" in choice_config:
                            answer = choice_config["12"]
                            logger.info(f"Default 1-2 pattern detected, auto-selecting: '{answer}'")
                            print(f"\n🧠 기본 1-2 선택 패턴 감지 → '{answer}' 자동 선택\n")
                            child.sendline(str(answer))
                            buffer = ""
                            continue
                    
                    # No auto-match: switch to interactive mode for manual selection
                    logger.info("No pattern matched, switching to interactive mode")
                    print("\nℹ️ No automatic pattern matched. Entering interactive mode for manual input...\n")
                    child.interact()
                    # Reset buffer and timer
                    buffer = ""
                    last_output_time = time.time()
                    continue

        except pexpect.exceptions.EOF:
            print("\n✅ 프로세스 종료됨")
            break
        except Exception as e:
            print(f"[에러] {e}")
            break

if __name__ == "__main__":
    run_claude_code()
