"""Prompt input widget for manual Claude Code interaction"""

from textual.widgets import Static, Input, Button, Select, RadioSet, RadioButton
from textual.containers import Container, Horizontal, Vertical
from textual.app import ComposeResult
from textual.message import Message
from textual.reactive import reactive
from typing import Optional, List, Tuple, Callable
import logging

from .prompt_detector import PromptInfo, PromptType


class PromptInputWidget(Static):
    """Widget for manual prompt input to Claude Code"""
    
    class PromptSubmitted(Message):
        """Message sent when user submits a response"""
        def __init__(self, response: str, prompt_info: PromptInfo) -> None:
            self.response = response
            self.prompt_info = prompt_info
            super().__init__()
    
    current_prompt = reactive(None)
    is_visible = reactive(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logger = logging.getLogger("yesman.dashboard.prompt_input")
        self.submit_callback: Optional[Callable[[str], None]] = None
    
    def compose(self) -> ComposeResult:
        with Container(id="prompt-input-container", classes="hidden"):
            yield Static("No prompt detected", id="prompt-question")
            
            # Container for different input types
            with Container(id="input-container"):
                # Text input
                yield Input(placeholder="Enter your response...", id="text-input", classes="hidden")
                
                # Button container for options
                with Horizontal(id="button-container", classes="hidden"):
                    pass
                
                # Radio buttons for numbered selections
                with RadioSet(id="radio-container", classes="hidden"):
                    pass
            
            # Control buttons
            with Horizontal(id="control-buttons"):
                yield Button("Submit", id="submit-btn", variant="success")
                yield Button("Cancel", id="cancel-btn", variant="error")
    
    def set_submit_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback to be called when response is submitted"""
        self.submit_callback = callback
    
    def show_prompt(self, prompt_info: PromptInfo) -> None:
        """Display prompt and appropriate input controls"""
        self.current_prompt = prompt_info
        self.is_visible = True
        
        try:
            # Update question text
            question_widget = self.query_one("#prompt-question", Static)
            question_widget.update(f"[bold]{prompt_info.question}[/]")
            
            # Hide all input containers first
            self._hide_all_inputs()
            
            # Show appropriate input based on prompt type
            if prompt_info.type == PromptType.TEXT_INPUT:
                self._setup_text_input(prompt_info)
            elif prompt_info.type == PromptType.NUMBERED_SELECTION:
                self._setup_numbered_selection(prompt_info)
            elif prompt_info.type in [PromptType.BINARY_CHOICE, PromptType.TRUE_FALSE, PromptType.CONFIRMATION]:
                self._setup_binary_choice(prompt_info)
            else:
                self._setup_text_input(prompt_info)  # Fallback to text input
            
            # Show the container
            container = self.query_one("#prompt-input-container")
            container.remove_class("hidden")
            
            self.logger.info(f"Displayed prompt: {prompt_info.type.value}")
            
        except Exception as e:
            self.logger.error(f"Error displaying prompt: {e}")
    
    def hide_prompt(self) -> None:
        """Hide the prompt input widget"""
        self.is_visible = False
        self.current_prompt = None
        
        try:
            container = self.query_one("#prompt-input-container")
            container.add_class("hidden")
            self._hide_all_inputs()
            
        except Exception as e:
            self.logger.error(f"Error hiding prompt: {e}")
    
    def _hide_all_inputs(self) -> None:
        """Hide all input containers"""
        try:
            self.query_one("#text-input").add_class("hidden")
            self.query_one("#button-container").add_class("hidden")
            self.query_one("#radio-container").add_class("hidden")
            
            # Clear button container
            button_container = self.query_one("#button-container")
            button_container.children.clear()
            
            # Clear radio container
            radio_container = self.query_one("#radio-container")
            radio_container.children.clear()
            
        except Exception as e:
            self.logger.error(f"Error hiding inputs: {e}")
    
    def _setup_text_input(self, prompt_info: PromptInfo) -> None:
        """Setup text input for free-form responses"""
        try:
            text_input = self.query_one("#text-input", Input)
            text_input.remove_class("hidden")
            
            # Set placeholder based on prompt type
            if prompt_info.type == PromptType.TERMINAL_SETTINGS:
                text_input.placeholder = "Enter terminal setting value..."
            elif prompt_info.type == PromptType.LOGIN_REDIRECT:
                text_input.placeholder = "Enter authentication details..."
            else:
                text_input.placeholder = "Enter your response..."
            
            text_input.value = ""
            text_input.focus()
            
        except Exception as e:
            self.logger.error(f"Error setting up text input: {e}")
    
    def _setup_numbered_selection(self, prompt_info: PromptInfo) -> None:
        """Setup radio buttons for numbered selections"""
        try:
            radio_container = self.query_one("#radio-container", RadioSet)
            radio_container.remove_class("hidden")
            
            # Add radio buttons for each option
            for i, (key, description) in enumerate(prompt_info.options):
                radio = RadioButton(f"{key}. {description}", value=(i == 0), id=f"radio-{key}")
                radio_container.mount(radio)
            
        except Exception as e:
            self.logger.error(f"Error setting up numbered selection: {e}")
    
    def _setup_binary_choice(self, prompt_info: PromptInfo) -> None:
        """Setup buttons for binary choices"""
        try:
            button_container = self.query_one("#button-container")
            button_container.remove_class("hidden")
            
            # Add buttons for each option
            for key, description in prompt_info.options:
                if key.lower() in ['y', 'yes', 'true', '1']:
                    variant = "success"
                else:
                    variant = "error"
                
                button = Button(f"{description}", id=f"choice-{key}", variant=variant)
                button_container.mount(button)
            
        except Exception as e:
            self.logger.error(f"Error setting up binary choice: {e}")
    
    def _get_current_response(self) -> Optional[str]:
        """Get the current response based on input type"""
        if not self.current_prompt:
            return None
        
        try:
            if self.current_prompt.type == PromptType.TEXT_INPUT:
                text_input = self.query_one("#text-input", Input)
                return text_input.value.strip()
            
            elif self.current_prompt.type == PromptType.NUMBERED_SELECTION:
                radio_container = self.query_one("#radio-container", RadioSet)
                pressed_radio = radio_container.pressed_button
                if pressed_radio:
                    # Extract key from radio ID
                    return pressed_radio.id.replace("radio-", "")
                return None
            
            elif self.current_prompt.type in [PromptType.BINARY_CHOICE, PromptType.TRUE_FALSE, PromptType.CONFIRMATION]:
                # Will be handled by button press event
                return None
            
        except Exception as e:
            self.logger.error(f"Error getting current response: {e}")
        
        return None
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events"""
        button_id = event.button.id
        
        if button_id == "submit-btn":
            self._submit_response()
        elif button_id == "cancel-btn":
            self._cancel_prompt()
        elif button_id.startswith("choice-"):
            # Binary choice button pressed
            choice_key = button_id.replace("choice-", "")
            self._submit_response(choice_key)
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle text input submission (Enter key)"""
        if event.input.id == "text-input":
            self._submit_response()
    
    def _submit_response(self, response: Optional[str] = None) -> None:
        """Submit the current response"""
        if not self.current_prompt:
            return
        
        # Get response if not provided
        if response is None:
            response = self._get_current_response()
        
        if response is None or response == "":
            self.logger.warning("No response provided")
            return
        
        try:
            # Call submit callback if set
            if self.submit_callback:
                self.submit_callback(response)
            
            # Post message
            self.post_message(self.PromptSubmitted(response, self.current_prompt))
            
            self.logger.info(f"Submitted response: '{response}' for {self.current_prompt.type.value}")
            
            # Hide the prompt
            self.hide_prompt()
            
        except Exception as e:
            self.logger.error(f"Error submitting response: {e}")
    
    def _cancel_prompt(self) -> None:
        """Cancel the current prompt"""
        self.logger.info("Prompt cancelled by user")
        self.hide_prompt()
    
    def get_current_prompt_info(self) -> Optional[PromptInfo]:
        """Get information about the current prompt"""
        return self.current_prompt
    
    def is_prompt_active(self) -> bool:
        """Check if a prompt is currently active"""
        return self.is_visible and self.current_prompt is not None