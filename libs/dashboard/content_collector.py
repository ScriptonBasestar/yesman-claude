"""Content collection system for Claude interactions"""

import time
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import logging
from ..utils import ensure_log_directory, get_default_log_path


class ClaudeContentCollector:
    """Collects and stores Claude Code interactions for pattern analysis"""
    
    def __init__(self, session_name: str):
        self.session_name = session_name
        self.logger = self._setup_logger()
        self.collection_path = self._setup_collection_directory()
        self.last_content_hash = ""
        self.interaction_count = 0
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for content collector"""
        logger = logging.getLogger(f"yesman.dashboard.content_collector.{self.session_name}")
        logger.setLevel(logging.INFO)
        logger.propagate = False
        
        log_path = ensure_log_directory(get_default_log_path())
        log_file = log_path / f"content_collector_{self.session_name}.log"
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def _setup_collection_directory(self) -> Path:
        """Setup directory for content collection"""
        collection_dir = ensure_log_directory(get_default_log_path() / "claude_interactions")
        session_dir = collection_dir / self.session_name
        session_dir.mkdir(exist_ok=True)
        return session_dir
    
    def _generate_content_hash(self, content: str) -> str:
        """Generate hash for content to detect changes"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()[:8]
    
    def collect_interaction(self, content: str, prompt_info: Optional[Dict] = None, 
                          response: Optional[str] = None) -> bool:
        """
        Collect Claude interaction data
        
        Args:
            content: The pane content
            prompt_info: Detected prompt information
            response: Auto-response that was sent
            
        Returns:
            True if content was collected (new/changed), False if duplicate
        """
        if not content or len(content.strip()) < 10:
            return False
            
        content_hash = self._generate_content_hash(content)
        
        # Skip if content hasn't changed significantly
        if content_hash == self.last_content_hash:
            return False
            
        self.last_content_hash = content_hash
        self.interaction_count += 1
        
        # Create interaction record
        interaction = {
            'timestamp': datetime.now().isoformat(),
            'session_name': self.session_name,
            'interaction_id': f"{self.session_name}_{self.interaction_count:04d}",
            'content_hash': content_hash,
            'content': content,
            'content_length': len(content),
            'prompt_detected': prompt_info is not None,
            'prompt_info': prompt_info,
            'auto_response': response,
            'collection_metadata': {
                'collector_version': '1.0',
                'content_source': 'tmux_pane_capture'
            }
        }
        
        # Save to file
        try:
            filename = f"interaction_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{content_hash}.json"
            filepath = self.collection_path / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(interaction, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Collected interaction {interaction['interaction_id']} - "
                           f"prompt: {prompt_info is not None}, response: {response}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save interaction: {e}")
            return False
    
    def collect_raw_content(self, content: str, metadata: Optional[Dict] = None) -> bool:
        """
        Collect raw content without prompt analysis
        
        Args:
            content: Raw pane content
            metadata: Additional metadata
            
        Returns:
            True if collected, False if skipped
        """
        if not content or len(content.strip()) < 10:
            return False
            
        content_hash = self._generate_content_hash(content)
        
        if content_hash == self.last_content_hash:
            return False
            
        self.last_content_hash = content_hash
        
        # Create raw content record
        record = {
            'timestamp': datetime.now().isoformat(),
            'session_name': self.session_name,
            'content_hash': content_hash,
            'content': content,
            'content_length': len(content),
            'metadata': metadata or {},
            'record_type': 'raw_content'
        }
        
        try:
            filename = f"raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{content_hash}.json"
            filepath = self.collection_path / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(record, f, indent=2, ensure_ascii=False)
            
            self.logger.debug(f"Collected raw content - hash: {content_hash}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save raw content: {e}")
            return False
    
    def get_collection_stats(self) -> Dict:
        """Get statistics about collected data"""
        try:
            files = list(self.collection_path.glob("*.json"))
            
            interaction_files = [f for f in files if f.name.startswith("interaction_")]
            raw_files = [f for f in files if f.name.startswith("raw_")]
            
            total_size = sum(f.stat().st_size for f in files)
            
            return {
                'total_files': len(files),
                'interaction_files': len(interaction_files),
                'raw_files': len(raw_files),
                'total_size_bytes': total_size,
                'collection_path': str(self.collection_path),
                'session_name': self.session_name,
                'last_interaction_count': self.interaction_count
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get collection stats: {e}")
            return {'error': str(e)}
    
    def cleanup_old_files(self, days_to_keep: int = 7) -> int:
        """
        Clean up old collection files
        
        Args:
            days_to_keep: Number of days to keep files
            
        Returns:
            Number of files deleted
        """
        try:
            cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
            files_deleted = 0
            
            for file_path in self.collection_path.glob("*.json"):
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    files_deleted += 1
            
            if files_deleted > 0:
                self.logger.info(f"Cleaned up {files_deleted} old collection files")
            
            return files_deleted
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old files: {e}")
            return 0


class ContentCollectionManager:
    """Manages content collectors for multiple sessions"""
    
    def __init__(self):
        self.collectors: Dict[str, ClaudeContentCollector] = {}
        self.logger = logging.getLogger("yesman.dashboard.content_collection_manager")
    
    def get_collector(self, session_name: str) -> ClaudeContentCollector:
        """Get or create collector for session"""
        if session_name not in self.collectors:
            self.collectors[session_name] = ClaudeContentCollector(session_name)
        return self.collectors[session_name]
    
    def collect_for_session(self, session_name: str, content: str, 
                          prompt_info: Optional[Dict] = None, 
                          response: Optional[str] = None) -> bool:
        """Collect content for a specific session"""
        collector = self.get_collector(session_name)
        return collector.collect_interaction(content, prompt_info, response)
    
    def get_all_stats(self) -> Dict[str, Dict]:
        """Get statistics for all sessions"""
        return {session: collector.get_collection_stats() 
                for session, collector in self.collectors.items()}
    
    def cleanup_all_sessions(self, days_to_keep: int = 7) -> Dict[str, int]:
        """Clean up old files for all sessions"""
        return {session: collector.cleanup_old_files(days_to_keep)
                for session, collector in self.collectors.items()}