#!/usr/bin/env python3
"""
MCP Integration Testing Script

Tests whether MCP servers work correctly with claude -p option
and provides methods to verify MCP functionality in LangChain integration.
"""

import asyncio
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional


class MCPTester:
    """Test MCP server functionality with Claude CLI."""

    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path)
        self.test_results = {}

    def test_basic_mcp_functionality(self) -> Dict[str, Any]:
        """Test basic MCP server functionality without -p option."""

        print("🧪 Testing basic MCP functionality...")

        # Test 1: Check if MCP servers are available
        cmd = ["claude", "List available MCP servers and their capabilities"]
        result = self._run_claude_command(cmd)

        test_result = {
            "test_name": "basic_mcp_list",
            "success": result["success"],
            "output": result["output"],
            "has_mcp_servers": "mcp" in result["output"].lower() or "server" in result["output"].lower(),
        }

        self.test_results["basic_mcp"] = test_result
        return test_result

    def test_mcp_with_custom_prompt(self, custom_prompt: str) -> Dict[str, Any]:
        """Test MCP functionality with -p option."""

        print(f"🧪 Testing MCP with custom prompt: {custom_prompt}")

        # Test MCP servers with custom prompt
        cmd = [
            "claude",
            "-p",
            custom_prompt,
            "Use MCP tools to list files in current directory",
        ]
        result = self._run_claude_command(cmd)

        test_result = {
            "test_name": "mcp_with_custom_prompt",
            "custom_prompt": custom_prompt,
            "success": result["success"],
            "output": result["output"],
            "used_mcp_tools": self._detect_mcp_tool_usage(result["output"]),
        }

        self.test_results["mcp_custom_prompt"] = test_result
        return test_result

    def test_specific_mcp_server(self, server_name: str, test_command: str) -> Dict[str, Any]:
        """Test specific MCP server functionality."""

        print(f"🧪 Testing specific MCP server: {server_name}")

        # Test specific server
        cmd = ["claude", f"Use {server_name} MCP server to {test_command}"]
        result = self._run_claude_command(cmd)

        test_result = {
            "test_name": f"specific_mcp_{server_name}",
            "server_name": server_name,
            "test_command": test_command,
            "success": result["success"],
            "output": result["output"],
            "server_responded": server_name.lower() in result["output"].lower(),
        }

        self.test_results[f"mcp_{server_name}"] = test_result
        return test_result

    def test_mcp_continuity_with_sessions(self) -> Dict[str, Any]:
        """Test MCP functionality with session continuity."""

        print("🧪 Testing MCP with session continuity...")

        # First command - establish session
        cmd1 = ["claude", "Create a file using MCP tools and remember the filename"]
        result1 = self._run_claude_command(cmd1)

        # Extract session info if available
        session_id = self._extract_session_id(result1["output"])

        # Second command - continue session
        if session_id:
            cmd2 = [
                "claude",
                "--continue",
                session_id,
                "What was the filename I just created?",
            ]
        else:
            cmd2 = [
                "claude",
                "What was the filename I just created in the previous command?",
            ]

        result2 = self._run_claude_command(cmd2)

        test_result = {
            "test_name": "mcp_session_continuity",
            "first_command_success": result1["success"],
            "second_command_success": result2["success"],
            "session_id": session_id,
            "continuity_preserved": self._check_context_continuity(result1["output"], result2["output"]),
        }

        self.test_results["mcp_continuity"] = test_result
        return test_result

    def run_comprehensive_mcp_tests(self) -> Dict[str, Any]:
        """Run comprehensive MCP integration tests."""

        print("🚀 Starting comprehensive MCP tests...")

        test_suite = {
            "basic_functionality": self.test_basic_mcp_functionality(),
            "custom_prompt_simple": self.test_mcp_with_custom_prompt("Act as a file system assistant"),
            "custom_prompt_complex": self.test_mcp_with_custom_prompt("You are a development assistant with access to filesystem and database tools"),
            "session_continuity": self.test_mcp_continuity_with_sessions(),
        }

        # Test common MCP servers if available
        common_servers = ["filesystem", "database", "web", "git"]
        for server in common_servers:
            test_suite[f"server_{server}"] = self.test_specific_mcp_server(server, "perform a basic operation")

        # Generate summary
        test_suite["summary"] = self._generate_test_summary(test_suite)

        return test_suite

    def _run_claude_command(self, cmd: List[str], timeout: int = 30) -> Dict[str, Any]:
        """Run Claude CLI command and capture result."""

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "returncode": result.returncode,
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": "Command timed out",
                "returncode": -1,
            }
        except Exception as e:
            return {"success": False, "output": "", "error": str(e), "returncode": -1}

    def _detect_mcp_tool_usage(self, output: str) -> List[str]:
        """Detect which MCP tools were used in the output."""

        mcp_indicators = [
            "mcp__",
            "MCP:",
            "Using tool:",
            "Tool:",
            "Server:",
            "filesystem",
            "database",
            "web_fetch",
            "git",
            "context7",
            "shrimp",
        ]

        used_tools = []
        output_lower = output.lower()

        for indicator in mcp_indicators:
            if indicator.lower() in output_lower:
                used_tools.append(indicator)

        return used_tools

    def _extract_session_id(self, output: str) -> Optional[str]:
        """Extract session ID from Claude output if available."""

        # This is a simplified version - actual implementation would parse
        # Claude's output format for session information
        lines = output.split("\n")
        for line in lines:
            if "session" in line.lower() and len(line.split()) > 1:
                # Try to find UUID-like strings
                import re

                uuid_pattern = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
                match = re.search(uuid_pattern, line, re.IGNORECASE)
                if match:
                    return match.group()

        return None

    def _check_context_continuity(self, first_output: str, second_output: str) -> bool:
        """Check if context was preserved between commands."""

        # Simple heuristic - look for references to previous content
        continuity_indicators = [
            "previous",
            "earlier",
            "before",
            "mentioned",
            "created",
            "filename",
            "file",
            "earlier command",
        ]

        second_lower = second_output.lower()
        return any(indicator in second_lower for indicator in continuity_indicators)

    def _generate_test_summary(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of test results."""

        total_tests = len([k for k in test_results.keys() if k != "summary"])
        successful_tests = sum(1 for k, v in test_results.items() if k != "summary" and v.get("success", False))

        mcp_tool_usage = []
        for test_name, result in test_results.items():
            if test_name != "summary" and "used_mcp_tools" in result:
                mcp_tool_usage.extend(result["used_mcp_tools"])

        return {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": successful_tests / total_tests if total_tests > 0 else 0,
            "mcp_tools_detected": list(set(mcp_tool_usage)),
            "mcp_functionality_confirmed": len(mcp_tool_usage) > 0,
            "recommendations": self._generate_recommendations(test_results),
        }

    def _generate_recommendations(self, test_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on test results."""

        recommendations = []

        # Check if basic MCP functionality works
        if not test_results.get("basic_functionality", {}).get("success", False):
            recommendations.append("MCP servers may not be properly configured")

        # Check if custom prompts affect MCP
        custom_prompt_tests = [k for k in test_results.keys() if "custom_prompt" in k]
        custom_success = [test_results[k].get("success", False) for k in custom_prompt_tests]

        if not any(custom_success):
            recommendations.append("MCP functionality may be affected by custom prompts (-p option)")
        elif all(custom_success):
            recommendations.append("MCP works well with custom prompts")

        # Check session continuity
        if not test_results.get("session_continuity", {}).get("continuity_preserved", False):
            recommendations.append("Session continuity may not preserve MCP context properly")

        return recommendations


# Test script functions
def create_test_config() -> Dict[str, Any]:
    """Create test configuration for MCP testing."""

    return {
        "test_prompts": [
            "Act as a filesystem assistant with full MCP access",
            "You are a development helper with database and web access",
            "Perform system administration tasks using available tools",
        ],
        "mcp_servers_to_test": ["context7", "shrimp", "filesystem", "database"],
        "test_commands": {
            "filesystem": "list files in current directory",
            "database": "show available database connections",
            "web": "fetch information from a public API",
            "git": "show current git status",
        },
    }


async def run_mcp_integration_tests():
    """Run comprehensive MCP integration tests."""

    print("🧪 Starting MCP Integration Tests...")

    # Initialize tester
    tester = MCPTester()

    # Run comprehensive tests
    results = tester.run_comprehensive_mcp_tests()

    # Save results
    results_file = Path("mcp_test_results.json")
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"📄 Test results saved to: {results_file}")

    # Print summary
    summary = results.get("summary", {})
    print("\n📊 Test Summary:")
    print(f"   Total Tests: {summary.get('total_tests', 0)}")
    print(f"   Successful: {summary.get('successful_tests', 0)}")
    print(f"   Success Rate: {summary.get('success_rate', 0):.1%}")
    print(f"   MCP Tools Detected: {summary.get('mcp_tools_detected', [])}")
    print(f"   MCP Functionality: {'✅ Confirmed' if summary.get('mcp_functionality_confirmed') else '❌ Not Detected'}")

    if summary.get("recommendations"):
        print("\n💡 Recommendations:")
        for rec in summary["recommendations"]:
            print(f"   • {rec}")

    return results


def test_langchain_mcp_integration():
    """Test MCP integration specifically for LangChain use case."""

    print("🔗 Testing LangChain-MCP Integration...")

    # Test command that simulates LangChain calling Claude with MCP
    test_commands = [
        {
            "name": "Simple MCP call",
            "cmd": ["claude", "Use available tools to list files"],
            "expected_mcp": True,
        },
        {
            "name": "Custom prompt with MCP",
            "cmd": [
                "claude",
                "-p",
                "You are a coding assistant with file access",
                "Show me the project structure",
            ],
            "expected_mcp": True,
        },
        {
            "name": "Complex workflow simulation",
            "cmd": [
                "claude",
                "-p",
                "Execute multi-step development workflow",
                "Analyze codebase and suggest improvements",
            ],
            "expected_mcp": True,
        },
    ]

    results = {}
    tester = MCPTester()

    for test in test_commands:
        print(f"   Testing: {test['name']}")
        result = tester._run_claude_command(test["cmd"])

        mcp_usage = tester._detect_mcp_tool_usage(result["output"])

        results[test["name"]] = {
            "success": result["success"],
            "mcp_detected": len(mcp_usage) > 0,
            "mcp_tools": mcp_usage,
            "meets_expectation": (len(mcp_usage) > 0) == test["expected_mcp"],
        }

    return results


if __name__ == "__main__":
    # Run tests
    asyncio.run(run_mcp_integration_tests())

    print("\n" + "=" * 50)

    # Test LangChain integration
    langchain_results = test_langchain_mcp_integration()

    print("\n🔗 LangChain Integration Results:")
    for test_name, result in langchain_results.items():
        status = "✅" if result["meets_expectation"] else "❌"
        print(f"   {status} {test_name}: MCP={'detected' if result['mcp_detected'] else 'not detected'}")
