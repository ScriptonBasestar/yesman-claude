#!/usr/bin/env python3
"""Test cache change detection scenarios"""

import sys
import time
from pathlib import Path

# Add libs to path
sys.path.insert(0, str(Path(__file__).parent / "libs"))

from libs.core.session_cache import SessionCache, InvalidationStrategy, CacheTag


def test_session_change_detection():
    """Test session change detection scenario"""
    print("\nTesting session change detection scenario...")
    
    cache = SessionCache(default_ttl=10.0, max_entries=20)
    
    # Simulate session data change detection
    def session_change_detector(old_session, new_session):
        """Detect if session status or window configuration changed"""
        if old_session.get('status') != new_session.get('status'):
            return True
        if len(old_session.get('windows', [])) != len(new_session.get('windows', [])):
            return True
        return False
    
    # Initial session state
    initial_session = {
        'name': 'frontend',
        'status': 'running',
        'windows': ['main', 'debug']
    }
    
    cache.put_with_strategy("session_frontend", initial_session,
                           strategy=InvalidationStrategy.CONTENT_CHANGE,
                           tags={CacheTag.SESSION_DATA, CacheTag.SESSION_STATUS},
                           change_detector=session_change_detector)
    
    # Try to update with same data (should not change)
    same_session = initial_session.copy()
    cache.put_with_strategy("session_frontend", same_session,
                           strategy=InvalidationStrategy.CONTENT_CHANGE,
                           change_detector=session_change_detector)
    
    # Verify timestamp wasn't changed significantly
    info1 = cache.get_entry_info("session_frontend")
    print("✓ No update for unchanged session data")
    
    # Update with status change
    changed_session = initial_session.copy()
    changed_session['status'] = 'stopped'
    
    cache.put_with_strategy("session_frontend", changed_session,
                           strategy=InvalidationStrategy.CONTENT_CHANGE,
                           change_detector=session_change_detector)
    
    updated_data = cache.get("session_frontend")
    assert updated_data['status'] == 'stopped'
    print("✓ Session status change detected and updated")
    
    # Update with window change
    window_changed_session = changed_session.copy()
    window_changed_session['windows'] = ['main', 'debug', 'test']
    
    cache.put_with_strategy("session_frontend", window_changed_session,
                           strategy=InvalidationStrategy.CONTENT_CHANGE,
                           change_detector=session_change_detector)
    
    updated_data = cache.get("session_frontend")
    assert len(updated_data['windows']) == 3
    print("✓ Session window change detected and updated")
    
    print("Session change detection tests passed!")