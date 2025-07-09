// Yesman Claude Web Dashboard - Main Entry Point

console.log('Yesman Claude Web Dashboard initializing...');

// Global dashboard object will be implemented in Task 1.4
window.dashboard = {
  version: '1.0.0',
  initialized: false,
  
  init() {
    console.log('Dashboard initialized');
    this.initialized = true;
  }
};

// Initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.dashboard.init();
  });
} else {
  window.dashboard.init();
}