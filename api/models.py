"""Copyright notice."""
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

from pydantic import BaseModel


class PaneInfo(BaseModel):
    command: str | None = None
    is_claude: bool = False
    is_controller: bool = False


class WindowInfo(BaseModel):
    index: int
    name: str
    panes: list[PaneInfo] = []


class SessionInfo(BaseModel):
    session_name: str
    project_name: str | None = None
    status: str
    template: str | None = None
    windows: list[WindowInfo] = []
