"""
Keyboard Navigation System

Universal keyboard navigation manager for all dashboard interfaces
with context-aware bindings, focus management, and accessibility support.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class KeyModifier(Enum):
    """Keyboard modifier keys"""

    CTRL = "ctrl"
    SHIFT = "shift"
    ALT = "alt"
    META = "meta"  # Cmd on Mac, Windows key on Windows

    def __str__(self):
        return self.value


class NavigationContext(Enum):
    """Navigation contexts for different interface states"""

    GLOBAL = "global"
    DASHBOARD = "dashboard"
    MODAL = "modal"
    FORM = "form"
    LIST = "list"
    TREE = "tree"
    TABLE = "table"
    VIM_NORMAL = "vim_normal"
    VIM_INSERT = "vim_insert"
    VIM_VISUAL = "vim_visual"


@dataclass
class KeyBinding:
    """
    Represents a keyboard binding configuration

    Defines how key combinations map to actions with context support
    """

    key: str
    modifiers: List[KeyModifier] = field(default_factory=list)
    action: str = ""
    description: str = ""
    context: Optional[NavigationContext] = None
    enabled: bool = True
    priority: int = 0  # Higher priority takes precedence

    def __post_init__(self):
        """Validate and normalize key binding"""
        if not self.key:
            raise ValueError("Key cannot be empty")

        # Normalize key to lowercase
        self.key = self.key.lower()

        # Ensure modifiers are KeyModifier instances
        self.modifiers = [mod if isinstance(mod, KeyModifier) else KeyModifier(mod.lower()) for mod in self.modifiers]

    @property
    def key_combination(self) -> str:
        """Get normalized key combination string"""
        parts = []

        # Add modifiers in standard order
        for mod in [KeyModifier.CTRL, KeyModifier.SHIFT, KeyModifier.ALT, KeyModifier.META]:
            if mod in self.modifiers:
                parts.append(mod.value)

        parts.append(self.key)
        return "+".join(parts)

    def matches(self, key: str, modifiers: List[KeyModifier]) -> bool:
        """Check if this binding matches the given key combination"""
        return self.key.lower() == key.lower() and set(self.modifiers) == set(modifiers) and self.enabled

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "key": self.key,
            "modifiers": [mod.value for mod in self.modifiers],
            "action": self.action,
            "description": self.description,
            "context": self.context.value if self.context else None,
            "enabled": self.enabled,
            "priority": self.priority,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KeyBinding":
        """Create KeyBinding from dictionary"""
        return cls(
            key=data["key"],
            modifiers=[KeyModifier(mod) for mod in data.get("modifiers", [])],
            action=data.get("action", ""),
            description=data.get("description", ""),
            context=NavigationContext(data["context"]) if data.get("context") else None,
            enabled=data.get("enabled", True),
            priority=data.get("priority", 0),
        )


@dataclass
class FocusableElement:
    """Represents an element that can receive focus"""

    element_id: str
    element_type: str  # button, input, link, etc.
    tab_index: int = 0
    enabled: bool = True
    context: Optional[NavigationContext] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "element_id": self.element_id,
            "element_type": self.element_type,
            "tab_index": self.tab_index,
            "enabled": self.enabled,
            "context": self.context.value if self.context else None,
        }


class KeyboardNavigationManager:
    """
    Universal keyboard navigation manager

    Provides consistent keyboard navigation across all dashboard interfaces
    with context-aware bindings, focus management, and accessibility support.
    """

    _instance: Optional["KeyboardNavigationManager"] = None

    def __init__(self):
        """Initialize keyboard navigation manager"""
        if KeyboardNavigationManager._instance is not None:
            raise RuntimeError("KeyboardNavigationManager is a singleton, use get_instance()")
        self.bindings: Dict[str, List[KeyBinding]] = {}
        self.actions: Dict[str, Callable] = {}
        self.focusable_elements: List[FocusableElement] = []
        self.current_focus_index: int = -1
        self.current_context: NavigationContext = NavigationContext.GLOBAL
        self.vim_mode_enabled: bool = False
        self.vim_mode: NavigationContext = NavigationContext.VIM_NORMAL

        # Initialize default bindings
        self._setup_default_bindings()

    def _setup_default_bindings(self) -> None:
        """Setup default keyboard bindings"""
        # Global navigation
        self.register_binding("tab", [], "focus_next", "Next element", NavigationContext.GLOBAL)
        self.register_binding("tab", [KeyModifier.SHIFT], "focus_prev", "Previous element", NavigationContext.GLOBAL)
        self.register_binding("enter", [], "activate", "Activate element", NavigationContext.GLOBAL)
        self.register_binding("escape", [], "cancel", "Cancel/Close", NavigationContext.GLOBAL)

        # Common shortcuts
        self.register_binding("r", [KeyModifier.CTRL], "refresh", "Refresh", NavigationContext.GLOBAL)
        self.register_binding("f", [KeyModifier.CTRL], "find", "Find", NavigationContext.GLOBAL)
        self.register_binding("s", [KeyModifier.CTRL], "save", "Save", NavigationContext.GLOBAL)
        self.register_binding("z", [KeyModifier.CTRL], "undo", "Undo", NavigationContext.GLOBAL)
        self.register_binding("y", [KeyModifier.CTRL], "redo", "Redo", NavigationContext.GLOBAL)

        # Dashboard navigation
        self.register_binding("1", [], "switch_view_1", "View 1", NavigationContext.DASHBOARD)
        self.register_binding("2", [], "switch_view_2", "View 2", NavigationContext.DASHBOARD)
        self.register_binding("3", [], "switch_view_3", "View 3", NavigationContext.DASHBOARD)
        self.register_binding("4", [], "switch_view_4", "View 4", NavigationContext.DASHBOARD)
        self.register_binding("5", [], "switch_view_5", "View 5", NavigationContext.DASHBOARD)

        # Arrow key navigation
        self.register_binding("arrowup", [], "navigate_up", "Navigate up", NavigationContext.GLOBAL)
        self.register_binding("arrowdown", [], "navigate_down", "Navigate down", NavigationContext.GLOBAL)
        self.register_binding("arrowleft", [], "navigate_left", "Navigate left", NavigationContext.GLOBAL)
        self.register_binding("arrowright", [], "navigate_right", "Navigate right", NavigationContext.GLOBAL)

        # Vim mode bindings
        self.register_binding(":", [], "vim_command_mode", "Command mode", NavigationContext.VIM_NORMAL)
        self.register_binding("i", [], "vim_insert_mode", "Insert mode", NavigationContext.VIM_NORMAL)
        self.register_binding("v", [], "vim_visual_mode", "Visual mode", NavigationContext.VIM_NORMAL)
        self.register_binding("h", [], "vim_left", "Left", NavigationContext.VIM_NORMAL)
        self.register_binding("j", [], "vim_down", "Down", NavigationContext.VIM_NORMAL)
        self.register_binding("k", [], "vim_up", "Up", NavigationContext.VIM_NORMAL)
        self.register_binding("l", [], "vim_right", "Right", NavigationContext.VIM_NORMAL)
        self.register_binding("escape", [], "vim_normal_mode", "Normal mode", NavigationContext.VIM_INSERT)

        # Register default actions
        self._setup_default_actions()

    def _setup_default_actions(self) -> None:
        """Setup default action handlers"""
        self.register_action("focus_next", self.focus_next)
        self.register_action("focus_prev", self.focus_prev)
        self.register_action("activate", self.activate_element)
        self.register_action("cancel", self.cancel_action)
        self.register_action("refresh", self.refresh_action)
        self.register_action("find", self.find_action)
        self.register_action("navigate_up", lambda: self.navigate_direction("up"))
        self.register_action("navigate_down", lambda: self.navigate_direction("down"))
        self.register_action("navigate_left", lambda: self.navigate_direction("left"))
        self.register_action("navigate_right", lambda: self.navigate_direction("right"))

        # Vim mode actions
        self.register_action("vim_command_mode", self.vim_command_mode)
        self.register_action("vim_insert_mode", self.vim_insert_mode)
        self.register_action("vim_visual_mode", self.vim_visual_mode)
        self.register_action("vim_normal_mode", self.vim_normal_mode)
        self.register_action("vim_left", lambda: self.navigate_direction("left"))
        self.register_action("vim_down", lambda: self.navigate_direction("down"))
        self.register_action("vim_up", lambda: self.navigate_direction("up"))
        self.register_action("vim_right", lambda: self.navigate_direction("right"))

    @classmethod
    def get_instance(cls) -> "KeyboardNavigationManager":
        """Get the singleton instance of the keyboard manager."""
        if cls._instance is None:
            cls._instance = KeyboardNavigationManager()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance."""
        cls._instance = None

    def register_binding(
        self,
        key: str,
        modifiers: List[KeyModifier],
        action: str,
        description: str = "",
        context: Optional[NavigationContext] = None,
        priority: int = 0,
    ) -> None:
        """
        Register a keyboard binding

        Args:
            key: Key name (e.g., 'a', 'enter', 'arrowup')
            modifiers: List of modifier keys
            action: Action name to execute
            description: Human-readable description
            context: Context where binding is active
            priority: Binding priority (higher takes precedence)
        """
        binding = KeyBinding(
            key=key,
            modifiers=modifiers,
            action=action,
            description=description,
            context=context,
            priority=priority,
        )

        key_combo = binding.key_combination
        if key_combo not in self.bindings:
            self.bindings[key_combo] = []

        # Insert binding in priority order (highest first)
        self.bindings[key_combo].append(binding)
        self.bindings[key_combo].sort(key=lambda b: b.priority, reverse=True)

        logger.debug(f"Registered key binding: {key_combo} -> {action}")

    def unregister_binding(self, key: str, modifiers: List[KeyModifier], context: Optional[NavigationContext] = None) -> bool:
        """
        Unregister a keyboard binding

        Args:
            key: Key name
            modifiers: List of modifier keys
            context: Context to remove binding from (None for all)

        Returns:
            True if binding was removed, False otherwise
        """
        key_combo = "+".join([mod.value for mod in modifiers] + [key.lower()])

        if key_combo not in self.bindings:
            return False

        original_count = len(self.bindings[key_combo])

        if context is None:
            # Remove all bindings for this key combination
            del self.bindings[key_combo]
        else:
            # Remove only bindings for specific context
            self.bindings[key_combo] = [b for b in self.bindings[key_combo] if b.context != context]

            # Clean up empty key combination
            if not self.bindings[key_combo]:
                del self.bindings[key_combo]

        removed_count = original_count - len(self.bindings.get(key_combo, []))
        logger.debug(f"Removed {removed_count} bindings for {key_combo}")
        return removed_count > 0

    def register_action(self, action_name: str, handler: Callable) -> None:
        """
        Register an action handler

        Args:
            action_name: Name of the action
            handler: Function to call when action is triggered
        """
        self.actions[action_name] = handler
        logger.debug(f"Registered action: {action_name}")

    def unregister_action(self, action_name: str) -> bool:
        """
        Unregister an action handler

        Args:
            action_name: Name of the action to remove

        Returns:
            True if action was removed, False otherwise
        """
        if action_name in self.actions:
            del self.actions[action_name]
            logger.debug(f"Unregistered action: {action_name}")
            return True
        return False

    def handle_key_event(self, key: str, modifiers: List[KeyModifier], context: Optional[NavigationContext] = None) -> bool:
        """
        Handle a keyboard event

        Args:
            key: Key that was pressed
            modifiers: Active modifier keys
            context: Current context (uses self.current_context if None)

        Returns:
            True if event was handled, False otherwise
        """
        if context is None:
            context = self.current_context

        # Special handling for Vim mode
        if self.vim_mode_enabled and context in [NavigationContext.VIM_NORMAL, NavigationContext.VIM_INSERT, NavigationContext.VIM_VISUAL]:
            context = self.vim_mode

        key_combo = "+".join([mod.value for mod in modifiers] + [key.lower()])

        if key_combo not in self.bindings:
            logger.debug(f"No bindings found for {key_combo}")
            return False

        # Find best matching binding based on context and priority
        best_binding = None

        for binding in self.bindings[key_combo]:
            if not binding.enabled:
                continue

            # Check context match
            if (binding.context is None or binding.context in (context, NavigationContext.GLOBAL)) and (best_binding is None or binding.priority > best_binding.priority):
                best_binding = binding

        if best_binding is None:
            logger.debug(f"No matching binding for {key_combo} in context {context}")
            return False

        # Execute action
        return self.execute_action(best_binding.action)

    def execute_action(self, action_name: str, *args, **kwargs) -> bool:
        """
        Execute a registered action

        Args:
            action_name: Name of the action to execute
            *args, **kwargs: Arguments to pass to action handler

        Returns:
            True if action was executed, False otherwise
        """
        if action_name not in self.actions:
            logger.warning(f"Unknown action: {action_name}")
            return False

        try:
            handler = self.actions[action_name]

            # Handle async actions
            if asyncio.iscoroutinefunction(handler):
                asyncio.create_task(handler(*args, **kwargs))
            else:
                handler(*args, **kwargs)

            logger.debug(f"Executed action: {action_name}")
            return True

        except Exception as e:
            logger.error(f"Error executing action {action_name}: {e}")
            return False

    def set_context(self, context: NavigationContext) -> None:
        """Set the current navigation context"""
        self.current_context = context
        logger.debug(f"Navigation context changed to: {context}")

    def add_focusable_element(self, element_id: str, element_type: str = "generic", tab_index: int = 0, context: Optional[NavigationContext] = None) -> None:
        """
        Add a focusable element to the navigation system

        Args:
            element_id: Unique identifier for the element
            element_type: Type of element (button, input, etc.)
            tab_index: Tab order index
            context: Context where element is focusable
        """
        element = FocusableElement(
            element_id=element_id,
            element_type=element_type,
            tab_index=tab_index,
            context=context,
        )

        # Insert in tab order
        insert_index = len(self.focusable_elements)
        for i, existing in enumerate(self.focusable_elements):
            if existing.tab_index > tab_index:
                insert_index = i
                break

        self.focusable_elements.insert(insert_index, element)
        logger.debug(f"Added focusable element: {element_id}")

    def remove_focusable_element(self, element_id: str) -> bool:
        """
        Remove a focusable element

        Args:
            element_id: ID of element to remove

        Returns:
            True if element was removed, False otherwise
        """
        for i, element in enumerate(self.focusable_elements):
            if element.element_id == element_id:
                self.focusable_elements.pop(i)

                # Adjust focus index if necessary
                if i <= self.current_focus_index:
                    self.current_focus_index -= 1

                logger.debug(f"Removed focusable element: {element_id}")
                return True

        return False

    def focus_next(self) -> bool:
        """Focus the next element in tab order"""
        if not self.focusable_elements:
            return False

        start_index = self.current_focus_index
        next_index = (start_index + 1) % len(self.focusable_elements)

        # Find next enabled element in current context
        attempts = 0
        while attempts < len(self.focusable_elements):
            element = self.focusable_elements[next_index]

            if element.enabled and (element.context is None or element.context == self.current_context):
                self.current_focus_index = next_index
                self._focus_element(element)
                return True

            next_index = (next_index + 1) % len(self.focusable_elements)
            attempts += 1

        return False

    def focus_prev(self) -> bool:
        """Focus the previous element in tab order"""
        if not self.focusable_elements:
            return False

        start_index = self.current_focus_index
        prev_index = (start_index - 1) % len(self.focusable_elements)

        # Find previous enabled element in current context
        attempts = 0
        while attempts < len(self.focusable_elements):
            element = self.focusable_elements[prev_index]

            if element.enabled and (element.context is None or element.context == self.current_context):
                self.current_focus_index = prev_index
                self._focus_element(element)
                return True

            prev_index = (prev_index - 1) % len(self.focusable_elements)
            attempts += 1

        return False

    def focus_element(self, element_id: str) -> bool:
        """
        Focus a specific element by ID

        Args:
            element_id: ID of element to focus

        Returns:
            True if element was focused, False otherwise
        """
        for i, element in enumerate(self.focusable_elements):
            if element.element_id == element_id and element.enabled:
                self.current_focus_index = i
                self._focus_element(element)
                return True

        return False

    def _focus_element(self, element: FocusableElement) -> None:
        """Internal method to focus an element"""
        logger.debug(f"Focusing element: {element.element_id}")
        # This would be implemented by subclasses or interface-specific handlers

    def get_current_focus(self) -> Optional[FocusableElement]:
        """Get the currently focused element"""
        if 0 <= self.current_focus_index < len(self.focusable_elements):
            return self.focusable_elements[self.current_focus_index]
        return None

    # Default action implementations

    def activate_element(self) -> None:
        """Activate the currently focused element"""
        element = self.get_current_focus()
        if element:
            logger.debug(f"Activating element: {element.element_id}")

    def cancel_action(self) -> None:
        """Handle cancel/escape action"""
        logger.debug("Cancel action triggered")

    def refresh_action(self) -> None:
        """Handle refresh action"""
        logger.debug("Refresh action triggered")

    def find_action(self) -> None:
        """Handle find action"""
        logger.debug("Find action triggered")

    def navigate_direction(self, direction: str) -> None:
        """Handle directional navigation"""
        logger.debug(f"Navigate {direction}")

    # Vim mode methods

    def enable_vim_mode(self) -> None:
        """Enable Vim-style keyboard navigation"""
        self.vim_mode_enabled = True
        self.vim_mode = NavigationContext.VIM_NORMAL
        logger.debug("Vim mode enabled")

    def disable_vim_mode(self) -> None:
        """Disable Vim-style keyboard navigation"""
        self.vim_mode_enabled = False
        logger.debug("Vim mode disabled")

    def vim_command_mode(self) -> None:
        """Enter Vim command mode"""
        if self.vim_mode_enabled:
            logger.debug("Vim command mode")

    def vim_insert_mode(self) -> None:
        """Enter Vim insert mode"""
        if self.vim_mode_enabled:
            self.vim_mode = NavigationContext.VIM_INSERT
            logger.debug("Vim insert mode")

    def vim_visual_mode(self) -> None:
        """Enter Vim visual mode"""
        if self.vim_mode_enabled:
            self.vim_mode = NavigationContext.VIM_VISUAL
            logger.debug("Vim visual mode")

    def vim_normal_mode(self) -> None:
        """Enter Vim normal mode"""
        if self.vim_mode_enabled:
            self.vim_mode = NavigationContext.VIM_NORMAL
            logger.debug("Vim normal mode")

    # Serialization methods

    def export_bindings(self) -> Dict[str, Any]:
        """Export all key bindings to dictionary"""
        exported = {}
        for key_combo, bindings in self.bindings.items():
            exported[key_combo] = [binding.to_dict() for binding in bindings]
        return exported

    def import_bindings(self, bindings_data: Dict[str, Any]) -> None:
        """Import key bindings from dictionary"""
        self.bindings.clear()

        for key_combo, binding_list in bindings_data.items():
            self.bindings[key_combo] = [KeyBinding.from_dict(binding_data) for binding_data in binding_list]

    def get_help_text(self, context: Optional[NavigationContext] = None) -> List[str]:
        """Get help text for current context"""
        help_lines = []
        processed_actions = set()

        valid_contexts = {None, context, NavigationContext.GLOBAL}

        for key_combo, bindings in self.bindings.items():
            for binding in bindings:
                if binding.context in valid_contexts and binding.action not in processed_actions:
                    help_lines.append(f"{binding.key_combination:<20} {binding.description}")
                    processed_actions.add(binding.action)

        return help_lines
