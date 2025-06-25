# Claude Code Selection Patterns

This document contains patterns detected by the yesman controller for automatic response.

## Trust Prompts

### Pattern 1: File Trust Dialog
```
Do you trust the files in this folder?
Claude Code may read files in this folder
[1] Yes, proceed
[2] No, cancel
```
**Auto Response**: `1`

## Selection Prompts

### Pattern 2: Numbered Options (2 choices)
```
[1] Option A
[2] Option B
```
**Auto Response**: `1` (default from config)

### Pattern 3: Numbered Options (3 choices)
```
[1] Option A
[2] Option B
[3] Option C
```
**Auto Response**: `1` (default from config)

### Pattern 4: Alternative Numbering Style
```
1) Option A
2) Option B
```
**Auto Response**: `1`

### Pattern 5: Dot Numbering Style
```
1. Option A
2. Option B
```
**Auto Response**: `1`

## Yes/No Prompts

### Pattern 6: Basic Yes/No
```
Continue? (yes/no)
```
**Auto Response**: `yes`

### Pattern 7: Y/N Format
```
Proceed? (y/n)
```
**Auto Response**: `yes`

### Pattern 8: Confirm Pattern
```
Confirm? [Y/n]
```
**Auto Response**: `yes`

## Idle/Welcome Screens

### Pattern 9: Welcome Screen (Full)
```
╭───────────────────────────────────────────────────╮
│ ✻ Welcome to Claude Code!                         │
│                                                   │
│   /help for help, /status for your current setup  │
│                                                   │
│   cwd: /home/archmagece/tmp/test1/test1-dir       │
╰───────────────────────────────────────────────────╯

 Tips for getting started:

 1. Ask Claude to create a new app or clone a repository
 2. Use Claude to help with file analysis, editing, bash commands and git
 3. Be as specific as you would with another engineer for the best results

 ※ Tip: Start with small features or bug fixes, tell Claude to propose a plan, and verify its suggested edits

╭────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ > Try "create a util logging.py that..."                                                                                                                                                                                                                                               │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
  ? for shortcuts
```
**Detection**: Waiting for user input, no auto response
**Key Elements**: 
- Welcome box with "✻ Welcome to Claude Code!"
- Empty prompt box with ">"
- Tips section visible

### Pattern 10: User Input in Progress
```
╭───────────────────────────────────────────────────╮
│ ✻ Welcome to Claude Code!                         │
│                                                   │
│   /help for help, /status for your current setup  │
│                                                   │
│   cwd: /home/archmagece/tmp/test1/test1-dir       │
╰───────────────────────────────────────────────────╯

 Tips for getting started:

 1. Ask Claude to create a new app or clone a repository
 2. Use Claude to help with file analysis, editing, bash commands and git
 3. Be as specific as you would with another engineer for the best results

 ※ Tip: Start with small features or bug fixes, tell Claude to propose a plan, and verify its suggested edits

╭────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ > ㄹㅈㄷㅈㄷㄹ                                                                                                                                                                                                                                                                         │
│                                                                                                                                                                                                                                                                                        │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```
**Detection**: User actively typing, no auto response
**Key Elements**: 
- User input visible after ">"
- Box expanded to show input
- Controller should NOT interrupt

### Pattern 11: Tip Screen
```
Tip: Use /memory
```
**Detection**: Idle state, no auto response

### Pattern 12: Simple Command Prompt
```
cwd: /path/to/directory
>
```
**Detection**: Ready for input, no auto response

## Controller Behavior

### Auto Next Feature
When enabled, the controller will:
1. Detect when Claude process exits
2. Automatically restart Claude with the selected model
3. Continue monitoring for prompts

### Model Selection
- **Default**: `claude`
- **Opus4**: `claude --model claude-3-5-opus-20241022`
- **Sonnet4**: `claude --model claude-3-5-sonnet-20241022`

## Pattern Detection Logic

The controller uses these methods:
1. **capture_pane_content()**: Gets last 50 lines of tmux pane
2. **detect_prompt_type()**: Identifies pattern type
3. **auto_respond()**: Generates appropriate response
4. **detect_trust_prompt()**: Special handling for trust dialogs
5. **is_idle_screen()**: Detects non-interactive states
6. **is_input_state()**: Detects when Claude is waiting for input

## Configuration

Default choices can be configured in `~/.yesman/yesman.yaml`:
```yaml
choice:
  yn: "yes"
  12: "1"
  123: "1"
```