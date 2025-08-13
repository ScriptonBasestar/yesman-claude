#!/usr/bin/env python3

"""Onboarding package for Yesman Claude Agent.

This package provides intelligent onboarding and setup capabilities including:
- Guided setup assistant
- Environment validation and configuration
- User preference management
- Automated system configuration
"""

from .setup_assistant import (
    IntelligentSetupAssistant,
    SetupResult,
    SetupStatus,
    SetupStep,
)

__all__ = [
    "IntelligentSetupAssistant",
    "SetupStep",
    "SetupResult",
    "SetupStatus",
]
