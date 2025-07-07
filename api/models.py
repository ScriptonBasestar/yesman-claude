from pydantic import BaseModel
from typing import List, Optional

class PaneInfo(BaseModel):
    command: Optional[str] = None
    is_claude: bool = False
    is_controller: bool = False

class WindowInfo(BaseModel):
    index: int
    name: str
    panes: List[PaneInfo] = []

class SessionInfo(BaseModel):
    session_name: str
    project_name: Optional[str] = None
    status: str
    template: Optional[str] = None
    windows: List[WindowInfo] = [] 