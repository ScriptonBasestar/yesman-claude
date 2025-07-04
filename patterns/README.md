# Patterns Directory

This directory contains auto-response patterns for different prompt types that Claude Code may present.

## Structure

- `123/` - For numbered selection prompts (1, 2, 3 options)
- `yn/` - For yes/no binary choices  
- `12/` - For simple binary selections (1/2 options)

## Pattern Files

Each pattern file contains regex patterns to match specific prompt formats and define appropriate responses.

## Usage

The ClaudePromptDetector uses these patterns to:
1. Identify prompt types
2. Extract options and context
3. Determine appropriate automated responses

Patterns are loaded automatically when the Claude manager starts.