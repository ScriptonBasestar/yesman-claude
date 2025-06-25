"""CSS styles for dashboard"""

DASHBOARD_CSS = """
/* Main layout */
#main-container {
    layout: grid;
    grid-size: 2 2;
    grid-gutter: 1;
    grid-columns: 2fr 1fr;
    grid-rows: 1fr 1fr;
    background: $surface;
}

/* Project panel styling */
#project-panel {
    row-span: 2;
    border: round $primary;
    border-title-align: center;
    border-title-style: bold;
    border-title-color: $primary;
    border-title-background: $surface;
    padding: 1;
    background: $panel;
    box-sizing: border-box;
}

#session-content {
    padding: 1;
    color: $text;
    text-align: left;
    height: 100%;
    overflow-y: auto;
}

/* Control panel styling */
#control-panel {
    border: round $secondary;
    border-title-align: center;
    border-title-style: bold;
    border-title-color: $secondary;
    border-title-background: $surface;
    padding: 1;
    background: $panel;
}

#info-panel {
    border: round $accent;
    border-title-align: center;
    border-title-style: bold;
    border-title-color: $accent;
    border-title-background: $surface;
    padding: 1;
    background: $panel;
}

/* Button styling */
Button {
    margin: 1 0;
    width: 100%;
    border: round;
    text-style: bold;
}

Button:hover {
    border: thick;
}

Button.-success {
    background: $success;
    color: $text;
}

Button.-error {
    background: $error;
    color: $text;
}

Button.-warning {
    background: $warning;
    color: $text;
}

#selected-info {
    margin-top: 1;
    text-align: center;
    text-style: italic;
    color: $text-muted;
    background: $surface;
    padding: 1;
    border: round;
}

#info-content {
    text-align: left;
    color: $text-muted;
    padding: 1;
}

/* Header and footer styling */
Header {
    background: $primary;
    color: $text;
    text-style: bold;
}

Footer {
    background: $surface;
    color: $text-muted;
}
"""