"""Claude monitoring and auto-response system"""

import asyncio
import logging
import threading
from typing import Optional, Any
from .prompt_detector import ClaudePromptDetector, PromptInfo, PromptType
from .content_collector import ClaudeContentCollector


class ClaudeMonitor:
    """Handles Claude monitoring and auto-response logic"""
    
    def __init__(self, session_manager, process_controller, status_manager):
        self.session_manager = session_manager
        self.process_controller = process_controller
        self.status_manager = status_manager
        self.session_name = session_manager.session_name
        
        # Monitoring state
        self.is_running = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        
        # Auto-response settings
        self.is_auto_next_enabled = True
        self.yn_mode = "Auto"
        self.yn_response = "y"
        self.mode12 = "Auto"
        self.mode12_response = "1"
        self.mode123 = "Auto"
        self.mode123_response = "1"
        
        # Prompt detection
        self.prompt_detector = ClaudePromptDetector()
        self.content_collector = ClaudeContentCollector(session_manager.session_name)
        self.current_prompt: Optional[PromptInfo] = None
        self.waiting_for_input = False
        
        self.logger = logging.getLogger(f"yesman.claude_monitor.{self.session_name}")
    
    def set_auto_next(self, enabled: bool):
        """Enable or disable auto-next responses"""
        self.is_auto_next_enabled = enabled
        status = "enabled" if enabled else "disabled"
        self.status_manager.update_status(f"[cyan]Auto next {status}[/]")
    
    def set_mode_yn(self, mode: str, response: str):
        """Set manual override for Y/N prompts"""
        self.yn_mode = mode
        self.yn_response = response
    
    def set_mode_12(self, mode: str, response: str):
        """Set manual override for 1/2 prompts"""
        self.mode12 = mode
        self.mode12_response = response
    
    def set_mode_123(self, mode: str, response: str):
        """Set manual override for 1/2/3 prompts"""
        self.mode123 = mode
        self.mode123_response = response
    
    def start_monitoring(self) -> bool:
        """Start the monitoring loop"""
        if not self.session_manager.get_claude_pane():
            self.status_manager.update_status(f"[red]Cannot start: No Claude pane in session[/]")
            return False
            
        if self.is_running:
            self.status_manager.update_status("[yellow]Monitor already running[/]")
            return False
        
        try:
            self.is_running = True
            self.status_manager.update_status(f"[green]Starting claude monitor for {self.session_name}[/]")
            
            # Start monitoring in a separate thread with its own event loop
            self._monitor_thread = threading.Thread(target=self._run_monitor_loop, daemon=True)
            self._monitor_thread.start()
            
            return True
            
        except Exception as e:
            self.is_running = False
            self.status_manager.update_status(f"[red]Failed to start claude monitor: {e}[/]")
            self.logger.error(f"Failed to start claude monitor: {e}", exc_info=True)
            return False
    
    def stop_monitoring(self) -> bool:
        """Stop the monitoring loop"""
        if not self.is_running:
            self.status_manager.update_status("[yellow]Claude monitor not running[/]")
            return False
        
        self.is_running = False
        
        # Stop the event loop if it's running
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        
        # Wait for thread to finish
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2.0)
        
        self.status_manager.update_status(f"[red]Stopped claude monitor for {self.session_name}[/]")
        return True
    
    def _run_monitor_loop(self):
        """Run the monitor loop in its own thread with event loop"""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        
        try:
            self._loop.run_until_complete(self._monitor_loop())
        except Exception as e:
            self.logger.error(f"Monitor loop error: {e}", exc_info=True)
        finally:
            self._loop.close()
            self.is_running = False
    
    async def _monitor_loop(self):
        """Main monitoring loop that runs in background"""
        if not self.session_manager.get_claude_pane():
            self.logger.error(f"Cannot start monitoring: no Claude pane for {self.session_name}")
            self.is_running = False
            return
            
        self.logger.info(f"Starting monitoring loop for {self.session_name}")
        last_content = ""
        
        try:
            while self.is_running:
                await asyncio.sleep(1)  # Check every second
                
                try:
                    content = self.session_manager.capture_pane_content()
                    
                    # Check if Claude is still running
                    if not self.process_controller.is_claude_running():
                        if self.is_auto_next_enabled:
                            self.status_manager.update_activity("🔄 Auto-restarting Claude...")
                            self.process_controller.restart_claude_pane()
                            continue
                        else:
                            self.status_manager.update_status("[yellow]Claude not running. Auto-restart disabled.[/]")
                            continue
                    
                    # Auto-respond to trust prompts
                    if self._auto_trust_if_needed():
                        self.status_manager.update_activity("✅ Auto-responded to trust prompt")
                        self.status_manager.record_response("trust_prompt", "1", content)
                        continue
                    
                    # Check for prompts and auto-respond if enabled
                    prompt_info = self._check_for_prompt(content)
                    
                    if prompt_info:
                        # Try auto-response first if auto_next is enabled
                        if self.is_auto_next_enabled:
                            if self._auto_respond_to_selection(prompt_info):
                                self.status_manager.update_activity(f"✅ Auto-responded to {prompt_info.type.value}")
                                self.status_manager.record_response(prompt_info.type.value, "auto", content)
                                self._clear_prompt_state()
                                continue
                        
                        # If auto-response didn't handle it, show waiting status
                        self.status_manager.update_activity(f"⏳ Waiting for input: {prompt_info.type.value}")
                        self.logger.debug(f"Prompt detected: {prompt_info.type.value} - {prompt_info.question}")
                    elif self.waiting_for_input:
                        self.status_manager.update_activity("⏳ Waiting for user input...")
                    else:
                        # Clear prompt state if no longer waiting
                        self._clear_prompt_state()
                    
                    # Collect content for pattern analysis
                    if content != last_content and len(content.strip()) > 0:
                        try:
                            # Convert PromptInfo to dict for collection compatibility
                            prompt_dict = None
                            if prompt_info:
                                prompt_dict = {
                                    'type': prompt_info.type.value,
                                    'question': prompt_info.question,
                                    'options': prompt_info.options,
                                    'confidence': prompt_info.confidence
                                }
                            self.content_collector.collect_interaction(content, prompt_dict, None)
                        except Exception as e:
                            self.logger.error(f"Failed to collect content: {e}")
                    
                    # Update activity if content changed
                    if content != last_content:
                        self.status_manager.update_activity("📝 Content updated")
                        last_content = content
                
                except Exception as e:
                    self.logger.error(f"Error in monitoring loop: {e}")
                    await asyncio.sleep(5)  # Wait longer on errors
                    
        except asyncio.CancelledError:
            self.logger.info("Monitoring loop cancelled")
        except Exception as e:
            self.logger.error(f"Monitoring loop error: {e}")
        finally:
            self.is_running = False
            self.status_manager.update_status("[red]Claude monitor stopped[/]")
    
    def _check_for_prompt(self, content: str) -> Optional[PromptInfo]:
        """Check if content contains a prompt waiting for input"""
        prompt_info = self.prompt_detector.detect_prompt(content)
        
        if prompt_info:
            self.current_prompt = prompt_info
            self.waiting_for_input = True
            self.logger.info(f"Prompt detected: {prompt_info.type.value} - {prompt_info.question}")
        else:
            # Check if we're still waiting for input based on content patterns
            self.waiting_for_input = self.prompt_detector.is_waiting_for_input(content)
        
        return prompt_info
    
    def _clear_prompt_state(self) -> None:
        """Clear the current prompt state"""
        self.current_prompt = None
        self.waiting_for_input = False
    
    def _auto_trust_if_needed(self) -> bool:
        """Auto-respond to trust prompts if detected"""
        content = self.session_manager.capture_pane_content()
        if self._detect_trust_prompt(content):
            self.process_controller.send_input("1")
            return True
        return False
    
    def _detect_trust_prompt(self, content: str) -> bool:
        """Detect trust prompt in content"""
        import re
        trust_patterns = [
            r"Do you trust the files in this folder",
            r"\[1\] Yes, proceed",
            r"\[2\] No, cancel"
        ]
        
        for pattern in trust_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        return False
    
    def _auto_respond_to_selection(self, prompt_info: PromptInfo) -> bool:
        """Auto-respond to selection prompts based on patterns and manual overrides"""
        if not self.is_auto_next_enabled:
            self.logger.debug("Auto-response disabled, skipping")
            return False
            
        self.logger.info(f"Attempting auto-response for prompt type: {prompt_info.type.value}")
        
        try:
            if prompt_info.type == PromptType.NUMBERED_SELECTION:
                return self._handle_numbered_selection(prompt_info)
            elif prompt_info.type == PromptType.BINARY_CHOICE:
                return self._handle_binary_choice(prompt_info)
            elif prompt_info.type == PromptType.BINARY_SELECTION:
                return self._handle_binary_selection(prompt_info)
            elif prompt_info.type == PromptType.LOGIN_REDIRECT:
                return self._handle_login_redirect(prompt_info)
                
        except Exception as e:
            self.logger.error(f"Error in auto_respond_to_selection: {e}")
            
        return False
    
    def _handle_numbered_selection(self, prompt_info: PromptInfo) -> bool:
        """Handle numbered selection prompts (1, 2, 3 options)"""
        opts_count = prompt_info.metadata.get('option_count', len(prompt_info.options))
        
        # Check manual overrides
        if opts_count == 2 and self.mode12 == "Manual":
            response = self.mode12_response
        elif opts_count >= 3 and self.mode123 == "Manual":
            response = self.mode123_response
        else:
            # Use pattern-based response or fallback
            response = getattr(prompt_info, 'recommended_response', None) or "1"
        
        self.process_controller.send_input(response)
        self.status_manager.record_response(prompt_info.type.value, response, prompt_info.question)
        self.logger.info(f"Auto-responding to numbered selection with: {response}")
        return True
    
    def _handle_binary_choice(self, prompt_info: PromptInfo) -> bool:
        """Handle binary choice prompts (y/n)"""
        # Check manual override
        if self.yn_mode == "Manual":
            response = self.yn_response.lower() if isinstance(self.yn_response, str) else str(self.yn_response)
        else:
            # Use pattern-based response or fallback
            response = getattr(prompt_info, 'recommended_response', None) or "y"
        
        self.process_controller.send_input(response)
        self.status_manager.record_response(prompt_info.type.value, response, prompt_info.question)
        self.logger.info(f"Auto-responding to binary choice with: {response}")
        return True
    
    def _handle_binary_selection(self, prompt_info: PromptInfo) -> bool:
        """Handle binary selection prompts ([1] [2])"""
        # Check manual override
        if self.mode12 == "Manual":
            response = self.mode12_response
        else:
            # Use pattern-based response or fallback
            response = getattr(prompt_info, 'recommended_response', None) or "1"
        
        self.process_controller.send_input(response)
        self.status_manager.record_response(prompt_info.type.value, response, prompt_info.question)
        self.logger.info(f"Auto-responding to binary selection with: {response}")
        return True
    
    def _handle_login_redirect(self, prompt_info: PromptInfo) -> bool:
        """Handle login redirect prompts"""
        question = prompt_info.question.lower()
        
        if "continue" in question or "press enter" in question:
            response = ""  # Just press Enter
            self.process_controller.send_input(response)
            self.status_manager.record_response(prompt_info.type.value, "Enter", prompt_info.question)
            self.logger.info("Auto-responding to login redirect with Enter")
            return True
        
        return False
    
    # Public interface methods
    def is_waiting_for_input(self) -> bool:
        """Check if Claude is currently waiting for user input"""
        return self.waiting_for_input
    
    def get_current_prompt(self) -> Optional[PromptInfo]:
        """Get the current prompt information"""
        return self.current_prompt
    
    def get_collection_stats(self) -> dict:
        """Get content collection statistics"""
        return self.content_collector.get_collection_stats()
    
    def cleanup_old_collections(self, days_to_keep: int = 7) -> int:
        """Clean up old collection files"""
        return self.content_collector.cleanup_old_files(days_to_keep)