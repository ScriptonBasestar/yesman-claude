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

/* Tree controller node styling */
Tree > .tree--cursor {
    background: $boost;
}

Tree > .tree--highlight {
    text-style: bold;
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

/* Custom footer styling */
CustomFooter {
    background: $surface;
    color: $text-muted;
    height: 1;
    dock: bottom;
}

#footer-container {
    height: 1;
    width: 100%;
    background: $surface;
    padding: 0 1;
}

.footer-key {
    text-align: center;
    color: $text-muted;
    background: $surface;
    width: 1fr;
    padding: 0 1;
}

/* Control panel specific styling */
#session-title {
    text-align: center;
    margin: 0 0 1 0;
    color: $primary;
    text-style: bold;
}

.control-label {
    width: auto;
    min-width: 10;
    text-align: right;
    margin: 0 1 0 0;
    color: $text;
}

#model-radio {
    width: 1fr;
    layout: horizontal;
}

#model-radio RadioButton {
    margin: 0 1 0 0;
    text-style: none;
}

#model-radio RadioButton:hover {
    background: $boost;
}

/* RadioButton styles */
RadioButton {
    padding: 0 1;
}

RadioButton > .toggle--label {
    color: $text-muted;
}

RadioButton.-on > .toggle--label {
    color: $primary;
    text-style: bold;
}

RadioButton.-on > .toggle--button {
    color: $primary;
}

RadioButton:focus > .toggle--label {
    text-style: underline;
}

/* Switch and auto status */
#auto-status-text {
    margin: 0 0 0 1;
    text-style: bold;
}

#auto-next-switch {
    width: auto;
}

#control-status {
    text-align: center;
    margin: 1 0 0 0;
    color: $text-muted;
    text-style: italic;
}

#controller-activity {
    text-align: center;
    margin: 0 0 0 0;
    color: $accent;
    text-style: bold;
    background: $surface;
    padding: 0 1;
    border: round;
}
"""