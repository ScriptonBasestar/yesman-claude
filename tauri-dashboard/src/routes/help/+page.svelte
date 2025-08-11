<script lang="ts">
    import { onMount } from 'svelte';
    import TroubleshootingWidget from '$lib/components/troubleshooting/TroubleshootingWidget.svelte';
    import OnboardingWizard from '$lib/components/help/OnboardingWizard.svelte';
    
    // State management
    let showOnboardingWizard = false;
    let showTroubleshooting = true;
    let systemStatus = {
        health_score: 100,
        active_alerts: 0,
        setup_complete: false
    };
    
    // Help sections
    let selectedSection = 'overview';
    
    const helpSections = [
        { id: 'overview', title: '📋 Overview', icon: '📋' },
        { id: 'troubleshooting', title: '🔧 Troubleshooting', icon: '🔧' },
        { id: 'setup', title: '⚙️ Setup & Configuration', icon: '⚙️' },
        { id: 'documentation', title: '📚 Documentation', icon: '📚' },
        { id: 'support', title: '💬 Support', icon: '💬' }
    ];
    
    onMount(async () => {
        // Check if first-time setup is needed
        try {
            // This would be replaced with actual system status check
            systemStatus = {
                health_score: 85,
                active_alerts: 2,
                setup_complete: true
            };
        } catch (error) {
            console.error('Failed to load system status:', error);
        }
    });
    
    function startOnboarding() {
        showOnboardingWizard = true;
    }
    
    function handleOnboardingComplete(event) {
        const results = event.detail;
        showOnboardingWizard = false;
        
        if (results.setup_successful) {
            systemStatus.setup_complete = true;
            selectedSection = 'overview';
        }
    }
    
    function handleOnboardingClose() {
        showOnboardingWizard = false;
    }
</script>

<svelte:head>
    <title>Help & Support - Yesman Claude Agent</title>
</svelte:head>

<div class="help-container">
    <!-- Header -->
    <div class="help-header">
        <div class="header-content">
            <h1>🆘 Help & Support Center</h1>
            <p>Get help with your Yesman Claude Agent setup, troubleshooting, and advanced features.</p>
        </div>
        
        <div class="system-status-card">
            <div class="status-header">
                <h3>System Status</h3>
                <div class="health-indicator" class:healthy={systemStatus.health_score > 80} 
                     class:warning={systemStatus.health_score > 50 && systemStatus.health_score <= 80}
                     class:critical={systemStatus.health_score <= 50}>
                    {systemStatus.health_score}%
                </div>
            </div>
            <div class="status-details">
                <div class="status-item">
                    <span>Active Alerts:</span>
                    <span class="alert-count" class:has-alerts={systemStatus.active_alerts > 0}>
                        {systemStatus.active_alerts}
                    </span>
                </div>
                <div class="status-item">
                    <span>Setup:</span>
                    <span class="setup-status" class:complete={systemStatus.setup_complete}>
                        {systemStatus.setup_complete ? '✅ Complete' : '⚠️ Incomplete'}
                    </span>
                </div>
            </div>
        </div>
    </div>

    <div class="help-content">
        <!-- Navigation Sidebar -->
        <nav class="help-nav">
            <div class="nav-header">
                <h3>Help Topics</h3>
            </div>
            <ul class="nav-list">
                {#each helpSections as section}
                    <li class="nav-item">
                        <button 
                            class="nav-button"
                            class:active={selectedSection === section.id}
                            on:click={() => selectedSection = section.id}
                        >
                            <span class="nav-icon">{section.icon}</span>
                            <span class="nav-title">{section.title}</span>
                        </button>
                    </li>
                {/each}
            </ul>
            
            <!-- Quick Actions -->
            <div class="quick-actions">
                <h4>Quick Actions</h4>
                <button class="action-button primary" on:click={startOnboarding}>
                    🚀 Run Setup Wizard
                </button>
                <button class="action-button secondary" on:click={() => selectedSection = 'troubleshooting'}>
                    🔧 Troubleshoot Issues
                </button>
            </div>
        </nav>

        <!-- Main Content -->
        <main class="help-main">
            {#if selectedSection === 'overview'}
                <div class="content-section">
                    <h2>📋 System Overview</h2>
                    
                    <!-- Welcome Message -->
                    <div class="welcome-card">
                        <div class="welcome-icon">👋</div>
                        <div class="welcome-content">
                            <h3>Welcome to Yesman Claude Agent!</h3>
                            <p>Your intelligent automation assistant is ready to help you streamline your workflow with Claude AI integration.</p>
                        </div>
                    </div>

                    <!-- Feature Highlights -->
                    <div class="features-grid">
                        <div class="feature-card">
                            <div class="feature-icon">🤖</div>
                            <h4>AI Automation</h4>
                            <p>Intelligent automation workflows with Claude AI integration for enhanced productivity.</p>
                        </div>
                        
                        <div class="feature-card">
                            <div class="feature-icon">📊</div>
                            <h4>Performance Monitoring</h4>
                            <p>Real-time system monitoring with automated performance optimization and alerts.</p>
                        </div>
                        
                        <div class="feature-card">
                            <div class="feature-icon">🔧</div>
                            <h4>Smart Troubleshooting</h4>
                            <p>Context-aware issue diagnosis with automated fixes for common problems.</p>
                        </div>
                        
                        <div class="feature-card">
                            <div class="feature-icon">🛡️</div>
                            <h4>Security & Compliance</h4>
                            <p>Built-in security validation and compliance monitoring for safe operation.</p>
                        </div>
                        
                        <div class="feature-card">
                            <div class="feature-icon">📚</div>
                            <h4>Live Documentation</h4>
                            <p>Automatically updated documentation with current system state and metrics.</p>
                        </div>
                        
                        <div class="feature-card">
                            <div class="feature-icon">⚙️</div>
                            <h4>Easy Configuration</h4>
                            <p>Intelligent setup assistant with guided configuration and validation.</p>
                        </div>
                    </div>

                    <!-- Getting Started -->
                    <div class="getting-started">
                        <h3>🚀 Getting Started</h3>
                        <div class="steps-list">
                            <div class="step-item" class:completed={systemStatus.setup_complete}>
                                <div class="step-number">1</div>
                                <div class="step-content">
                                    <h4>Complete Initial Setup</h4>
                                    <p>Run the setup wizard to configure your system with optimal settings.</p>
                                    {#if !systemStatus.setup_complete}
                                        <button class="step-action" on:click={startOnboarding}>
                                            Start Setup
                                        </button>
                                    {/if}
                                </div>
                            </div>
                            
                            <div class="step-item" class:completed={systemStatus.health_score > 90}>
                                <div class="step-number">2</div>
                                <div class="step-content">
                                    <h4>Verify System Health</h4>
                                    <p>Ensure all components are running optimally with our health monitoring.</p>
                                    <button class="step-action" on:click={() => selectedSection = 'troubleshooting'}>
                                        Check Health
                                    </button>
                                </div>
                            </div>
                            
                            <div class="step-item">
                                <div class="step-number">3</div>
                                <div class="step-content">
                                    <h4>Explore Features</h4>
                                    <p>Discover the full capabilities of your Yesman Claude Agent.</p>
                                    <button class="step-action" on:click={() => selectedSection = 'documentation'}>
                                        View Documentation
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

            {:else if selectedSection === 'troubleshooting'}
                <div class="content-section">
                    <h2>🔧 System Troubleshooting</h2>
                    
                    <div class="troubleshooting-intro">
                        <p>Our intelligent troubleshooting system can automatically detect and resolve common issues. 
                           Current issues are analyzed with context-aware suggestions and automated fixes when possible.</p>
                    </div>

                    {#if showTroubleshooting}
                        <TroubleshootingWidget />
                    {/if}

                    <!-- Manual Troubleshooting -->
                    <div class="manual-troubleshooting">
                        <h3>📖 Manual Troubleshooting Guide</h3>
                        
                        <div class="troubleshooting-categories">
                            <div class="trouble-category">
                                <h4>🚀 Performance Issues</h4>
                                <ul>
                                    <li><strong>Slow Response Times:</strong> Check system load and clear caches</li>
                                    <li><strong>High Memory Usage:</strong> Restart memory-intensive components</li>
                                    <li><strong>CPU Spikes:</strong> Review recent changes and optimize workflows</li>
                                </ul>
                                <button class="category-action">View Performance Guide</button>
                            </div>
                            
                            <div class="trouble-category">
                                <h4>🔒 Security Issues</h4>
                                <ul>
                                    <li><strong>Authentication Failures:</strong> Verify API keys and credentials</li>
                                    <li><strong>Access Denied:</strong> Check permissions and security settings</li>
                                    <li><strong>Security Violations:</strong> Review security logs and baselines</li>
                                </ul>
                                <button class="category-action">View Security Guide</button>
                            </div>
                            
                            <div class="trouble-category">
                                <h4>🌐 Network Problems</h4>
                                <ul>
                                    <li><strong>Connection Timeouts:</strong> Check network connectivity and firewall</li>
                                    <li><strong>API Failures:</strong> Verify endpoint availability and credentials</li>
                                    <li><strong>Rate Limiting:</strong> Implement exponential backoff strategies</li>
                                </ul>
                                <button class="category-action">View Network Guide</button>
                            </div>
                        </div>
                    </div>
                </div>

            {:else if selectedSection === 'setup'}
                <div class="content-section">
                    <h2>⚙️ Setup & Configuration</h2>
                    
                    <div class="setup-intro">
                        <p>Configure your Yesman Claude Agent with our intelligent setup assistant. 
                           The wizard guides you through environment setup, security configuration, and optimization.</p>
                    </div>

                    <!-- Setup Status -->
                    <div class="setup-status">
                        <h3>Current Setup Status</h3>
                        <div class="status-grid">
                            <div class="status-card" class:complete={systemStatus.setup_complete}>
                                <div class="status-icon">
                                    {systemStatus.setup_complete ? '✅' : '⚠️'}
                                </div>
                                <div class="status-info">
                                    <h4>Initial Setup</h4>
                                    <p>{systemStatus.setup_complete ? 'Completed' : 'Incomplete'}</p>
                                </div>
                            </div>
                            
                            <div class="status-card" class:complete={systemStatus.health_score > 90}>
                                <div class="status-icon">
                                    {systemStatus.health_score > 90 ? '✅' : '⚠️'}
                                </div>
                                <div class="status-info">
                                    <h4>System Health</h4>
                                    <p>{systemStatus.health_score}% Healthy</p>
                                </div>
                            </div>
                            
                            <div class="status-card" class:complete={systemStatus.active_alerts === 0}>
                                <div class="status-icon">
                                    {systemStatus.active_alerts === 0 ? '✅' : '⚠️'}
                                </div>
                                <div class="status-info">
                                    <h4>System Alerts</h4>
                                    <p>{systemStatus.active_alerts} Active</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Setup Actions -->
                    <div class="setup-actions">
                        <button class="setup-button primary" on:click={startOnboarding}>
                            🚀 Run Full Setup Wizard
                        </button>
                        
                        <div class="setup-options">
                            <button class="setup-button secondary">
                                ⚙️ Configure Security Settings
                            </button>
                            <button class="setup-button secondary">
                                📊 Setup Monitoring
                            </button>
                            <button class="setup-button secondary">
                                🔧 Development Tools
                            </button>
                        </div>
                    </div>

                    <!-- Configuration Guide -->
                    <div class="config-guide">
                        <h3>📚 Configuration Guide</h3>
                        <div class="config-sections">
                            <div class="config-section">
                                <h4>Environment Setup</h4>
                                <p>Python environment, dependencies, and system requirements validation.</p>
                                <code>python -m libs.onboarding.setup_assistant --steps python_environment</code>
                            </div>
                            
                            <div class="config-section">
                                <h4>Security Configuration</h4>
                                <p>API keys, authentication, and security baseline configuration.</p>
                                <code>make security-setup</code>
                            </div>
                            
                            <div class="config-section">
                                <h4>Performance Optimization</h4>
                                <p>Monitoring, caching, and performance tuning settings.</p>
                                <code>make performance-optimize</code>
                            </div>
                        </div>
                    </div>
                </div>

            {:else if selectedSection === 'documentation'}
                <div class="content-section">
                    <h2>📚 Documentation</h2>
                    
                    <div class="docs-intro">
                        <p>Access comprehensive documentation with live system data, troubleshooting guides, 
                           and development resources.</p>
                    </div>

                    <!-- Documentation Categories -->
                    <div class="docs-grid">
                        <div class="doc-card">
                            <div class="doc-icon">📖</div>
                            <h3>User Guide</h3>
                            <p>Complete user manual with feature overview and usage instructions.</p>
                            <div class="doc-actions">
                                <button class="doc-link">View User Guide</button>
                                <span class="doc-status">📄 Static</span>
                            </div>
                        </div>
                        
                        <div class="doc-card">
                            <div class="doc-icon">🔧</div>
                            <h3>Component Guide</h3>
                            <p>Component documentation with live performance metrics and optimization tips.</p>
                            <div class="doc-actions">
                                <button class="doc-link">View Components</button>
                                <span class="doc-status live">📊 Live Data</span>
                            </div>
                        </div>
                        
                        <div class="doc-card">
                            <div class="doc-icon">🔍</div>
                            <h3>Troubleshooting Guide</h3>
                            <p>Step-by-step troubleshooting with current system context and automated fixes.</p>
                            <div class="doc-actions">
                                <button class="doc-link">View Troubleshooting</button>
                                <span class="doc-status live">🔄 Auto-Updated</span>
                            </div>
                        </div>
                        
                        <div class="doc-card">
                            <div class="doc-icon">🚀</div>
                            <h3>Performance Guide</h3>
                            <p>Performance optimization recommendations with live metrics analysis.</p>
                            <div class="doc-actions">
                                <button class="doc-link">View Performance</button>
                                <span class="doc-status live">📈 Real-time</span>
                            </div>
                        </div>
                        
                        <div class="doc-card">
                            <div class="doc-icon">🛡️</div>
                            <h3>Security Documentation</h3>
                            <p>Security coding standards, audit procedures, and compliance guidelines.</p>
                            <div class="doc-actions">
                                <button class="doc-link">View Security</button>
                                <span class="doc-status">🔒 Standards</span>
                            </div>
                        </div>
                        
                        <div class="doc-card">
                            <div class="doc-icon">🔗</div>
                            <h3>API Reference</h3>
                            <p>Complete API documentation with live examples and current system status.</p>
                            <div class="doc-actions">
                                <button class="doc-link">View API Docs</button>
                                <span class="doc-status live">⚡ Interactive</span>
                            </div>
                        </div>
                    </div>

                    <!-- Documentation Tools -->
                    <div class="docs-tools">
                        <h3>📝 Documentation Tools</h3>
                        <div class="tools-list">
                            <button class="tool-button">
                                🔄 Generate Live Documentation
                            </button>
                            <button class="tool-button">
                                📊 Export System Report
                            </button>
                            <button class="tool-button">
                                🔍 Search Documentation
                            </button>
                        </div>
                    </div>
                </div>

            {:else if selectedSection === 'support'}
                <div class="content-section">
                    <h2>💬 Support & Community</h2>
                    
                    <div class="support-intro">
                        <p>Get help from the community, report issues, or contribute to the project development.</p>
                    </div>

                    <!-- Support Options -->
                    <div class="support-grid">
                        <div class="support-card">
                            <div class="support-icon">🐛</div>
                            <h3>Report a Bug</h3>
                            <p>Found an issue? Help us improve by reporting bugs with detailed information.</p>
                            <button class="support-action">Create Bug Report</button>
                        </div>
                        
                        <div class="support-card">
                            <div class="support-icon">💡</div>
                            <h3>Feature Request</h3>
                            <p>Have an idea for improvement? Submit feature requests and enhancement suggestions.</p>
                            <button class="support-action">Request Feature</button>
                        </div>
                        
                        <div class="support-card">
                            <div class="support-icon">❓</div>
                            <h3>Get Help</h3>
                            <p>Need assistance? Get help from the community or maintainers.</p>
                            <button class="support-action">Ask for Help</button>
                        </div>
                        
                        <div class="support-card">
                            <div class="support-icon">🤝</div>
                            <h3>Contribute</h3>
                            <p>Want to contribute? Learn how to help improve the project for everyone.</p>
                            <button class="support-action">Contributing Guide</button>
                        </div>
                    </div>

                    <!-- System Information -->
                    <div class="system-info">
                        <h3>🔧 System Information</h3>
                        <p>Include this information when reporting issues:</p>
                        <div class="info-block">
                            <code>
                                Yesman Claude Agent v1.0.0<br>
                                Platform: {navigator.platform}<br>
                                User Agent: {navigator.userAgent.split(' ').slice(0, 3).join(' ')}<br>
                                Health Score: {systemStatus.health_score}%<br>
                                Active Alerts: {systemStatus.active_alerts}<br>
                                Timestamp: {new Date().toISOString()}
                            </code>
                            <button class="copy-button">📋 Copy System Info</button>
                        </div>
                    </div>

                    <!-- Contact Information -->
                    <div class="contact-info">
                        <h3>📞 Contact Information</h3>
                        <div class="contact-methods">
                            <div class="contact-method">
                                <strong>GitHub Issues:</strong> 
                                <a href="https://github.com/your-org/yesman-agent/issues" target="_blank">
                                    Create Issue
                                </a>
                            </div>
                            <div class="contact-method">
                                <strong>Documentation:</strong> 
                                <a href="/docs" target="_blank">View Full Docs</a>
                            </div>
                            <div class="contact-method">
                                <strong>Community:</strong> 
                                <a href="https://discord.gg/your-discord" target="_blank">Join Discord</a>
                            </div>
                        </div>
                    </div>
                </div>
            {/if}
        </main>
    </div>
</div>

<!-- Onboarding Wizard -->
<OnboardingWizard 
    bind:visible={showOnboardingWizard}
    on:setupComplete={handleOnboardingComplete}
    on:close={handleOnboardingClose}
/>

<style>
    .help-container {
        min-height: 100vh;
        background: #f8fafc;
    }
    
    .help-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 2rem;
    }
    
    .header-content h1 {
        margin: 0 0 0.5rem 0;
        font-size: 2rem;
        font-weight: 600;
    }
    
    .header-content p {
        margin: 0;
        opacity: 0.9;
        font-size: 1.125rem;
    }
    
    .system-status-card {
        background: rgba(255, 255, 255, 0.15);
        border-radius: 0.75rem;
        padding: 1.5rem;
        min-width: 280px;
        backdrop-filter: blur(10px);
    }
    
    .status-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }
    
    .status-header h3 {
        margin: 0;
        font-size: 1.125rem;
    }
    
    .health-indicator {
        font-size: 1.5rem;
        font-weight: 700;
        padding: 0.25rem 0.75rem;
        border-radius: 0.5rem;
        background: rgba(255, 255, 255, 0.2);
    }
    
    .health-indicator.healthy {
        color: #10b981;
    }
    
    .health-indicator.warning {
        color: #f59e0b;
    }
    
    .health-indicator.critical {
        color: #ef4444;
    }
    
    .status-details {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }
    
    .status-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.875rem;
    }
    
    .alert-count.has-alerts {
        color: #fbbf24;
        font-weight: 600;
    }
    
    .setup-status.complete {
        color: #10b981;
        font-weight: 500;
    }
    
    .help-content {
        display: flex;
        min-height: calc(100vh - 200px);
    }
    
    .help-nav {
        width: 280px;
        background: white;
        border-right: 1px solid #e5e7eb;
        padding: 2rem 0;
    }
    
    .nav-header {
        padding: 0 2rem 1rem;
        border-bottom: 1px solid #e5e7eb;
        margin-bottom: 1rem;
    }
    
    .nav-header h3 {
        margin: 0;
        color: #374151;
        font-size: 1rem;
        font-weight: 600;
    }
    
    .nav-list {
        list-style: none;
        margin: 0;
        padding: 0;
    }
    
    .nav-item {
        margin-bottom: 0.25rem;
    }
    
    .nav-button {
        width: 100%;
        padding: 0.75rem 2rem;
        background: none;
        border: none;
        text-align: left;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        color: #6b7280;
        transition: all 0.2s;
        font-size: 0.875rem;
    }
    
    .nav-button:hover {
        background: #f3f4f6;
        color: #374151;
    }
    
    .nav-button.active {
        background: #eff6ff;
        color: #2563eb;
        border-right: 3px solid #2563eb;
    }
    
    .nav-icon {
        font-size: 1rem;
    }
    
    .nav-title {
        font-weight: 500;
    }
    
    .quick-actions {
        margin-top: 2rem;
        padding: 0 2rem;
        border-top: 1px solid #e5e7eb;
        padding-top: 2rem;
    }
    
    .quick-actions h4 {
        margin: 0 0 1rem 0;
        color: #374151;
        font-size: 0.875rem;
        font-weight: 600;
    }
    
    .action-button {
        width: 100%;
        padding: 0.75rem;
        border: none;
        border-radius: 0.5rem;
        font-size: 0.875rem;
        font-weight: 500;
        cursor: pointer;
        margin-bottom: 0.5rem;
        transition: all 0.2s;
    }
    
    .action-button.primary {
        background: #2563eb;
        color: white;
    }
    
    .action-button.primary:hover {
        background: #1d4ed8;
    }
    
    .action-button.secondary {
        background: #f3f4f6;
        color: #374151;
    }
    
    .action-button.secondary:hover {
        background: #e5e7eb;
    }
    
    .help-main {
        flex: 1;
        padding: 2rem;
        overflow-y: auto;
    }
    
    .content-section h2 {
        margin: 0 0 2rem 0;
        color: #1f2937;
        font-size: 1.75rem;
        font-weight: 600;
    }
    
    .welcome-card {
        display: flex;
        align-items: center;
        gap: 1.5rem;
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 0.75rem;
        padding: 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    
    .welcome-icon {
        font-size: 3rem;
    }
    
    .welcome-content h3 {
        margin: 0 0 0.5rem 0;
        color: #1f2937;
        font-size: 1.25rem;
    }
    
    .welcome-content p {
        margin: 0;
        color: #6b7280;
        line-height: 1.6;
    }
    
    .features-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 1.5rem;
        margin-bottom: 2rem;
    }
    
    .feature-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 0.5rem;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    
    .feature-icon {
        font-size: 2rem;
        margin-bottom: 1rem;
    }
    
    .feature-card h4 {
        margin: 0 0 0.5rem 0;
        color: #1f2937;
        font-size: 1.125rem;
        font-weight: 600;
    }
    
    .feature-card p {
        margin: 0;
        color: #6b7280;
        line-height: 1.5;
    }
    
    .getting-started {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 0.75rem;
        padding: 2rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    
    .getting-started h3 {
        margin: 0 0 1.5rem 0;
        color: #1f2937;
        font-size: 1.25rem;
        font-weight: 600;
    }
    
    .steps-list {
        display: flex;
        flex-direction: column;
        gap: 1.5rem;
    }
    
    .step-item {
        display: flex;
        gap: 1rem;
        align-items: flex-start;
    }
    
    .step-number {
        width: 2.5rem;
        height: 2.5rem;
        background: #f3f4f6;
        color: #6b7280;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        flex-shrink: 0;
    }
    
    .step-item.completed .step-number {
        background: #10b981;
        color: white;
    }
    
    .step-content {
        flex: 1;
    }
    
    .step-content h4 {
        margin: 0 0 0.5rem 0;
        color: #1f2937;
        font-size: 1rem;
        font-weight: 600;
    }
    
    .step-content p {
        margin: 0 0 0.75rem 0;
        color: #6b7280;
        line-height: 1.5;
    }
    
    .step-action {
        background: #2563eb;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 0.375rem;
        font-size: 0.875rem;
        font-weight: 500;
        cursor: pointer;
        transition: background 0.2s;
    }
    
    .step-action:hover {
        background: #1d4ed8;
    }
    
    .troubleshooting-intro {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin-bottom: 2rem;
        border-left-width: 4px;
        border-left-color: #3b82f6;
    }
    
    .troubleshooting-intro p {
        margin: 0;
        color: #4b5563;
        line-height: 1.6;
    }
    
    .manual-troubleshooting {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 0.75rem;
        padding: 2rem;
        margin-top: 2rem;
    }
    
    .manual-troubleshooting h3 {
        margin: 0 0 1.5rem 0;
        color: #1f2937;
        font-size: 1.25rem;
        font-weight: 600;
    }
    
    .troubleshooting-categories {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 1.5rem;
    }
    
    .trouble-category {
        border: 1px solid #e5e7eb;
        border-radius: 0.5rem;
        padding: 1.5rem;
        background: #fafafa;
    }
    
    .trouble-category h4 {
        margin: 0 0 1rem 0;
        color: #1f2937;
        font-size: 1rem;
        font-weight: 600;
    }
    
    .trouble-category ul {
        margin: 0 0 1.5rem 0;
        padding-left: 1.5rem;
        color: #4b5563;
        line-height: 1.6;
    }
    
    .trouble-category li {
        margin-bottom: 0.5rem;
    }
    
    .category-action {
        background: #6b7280;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 0.375rem;
        font-size: 0.875rem;
        cursor: pointer;
        transition: background 0.2s;
    }
    
    .category-action:hover {
        background: #4b5563;
    }
    
    .setup-intro {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin-bottom: 2rem;
        border-left-width: 4px;
        border-left-color: #10b981;
    }
    
    .setup-intro p {
        margin: 0;
        color: #4b5563;
        line-height: 1.6;
    }
    
    .setup-status {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 0.75rem;
        padding: 2rem;
        margin-bottom: 2rem;
    }
    
    .setup-status h3 {
        margin: 0 0 1.5rem 0;
        color: #1f2937;
        font-size: 1.25rem;
        font-weight: 600;
    }
    
    .status-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1.5rem;
    }
    
    .status-card {
        display: flex;
        align-items: center;
        gap: 1rem;
        border: 1px solid #e5e7eb;
        border-radius: 0.5rem;
        padding: 1.5rem;
        background: #fafafa;
    }
    
    .status-card.complete {
        border-color: #10b981;
        background: #f0fdf4;
    }
    
    .status-icon {
        font-size: 1.5rem;
    }
    
    .status-info h4 {
        margin: 0 0 0.25rem 0;
        color: #1f2937;
        font-size: 1rem;
        font-weight: 600;
    }
    
    .status-info p {
        margin: 0;
        color: #6b7280;
        font-size: 0.875rem;
    }
    
    .setup-actions {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 0.75rem;
        padding: 2rem;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .setup-button {
        border: none;
        padding: 1rem 2rem;
        border-radius: 0.5rem;
        font-size: 1rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
        margin: 0.5rem;
    }
    
    .setup-button.primary {
        background: #2563eb;
        color: white;
        font-size: 1.125rem;
        padding: 1.25rem 2.5rem;
    }
    
    .setup-button.primary:hover {
        background: #1d4ed8;
    }
    
    .setup-button.secondary {
        background: #f3f4f6;
        color: #374151;
    }
    
    .setup-button.secondary:hover {
        background: #e5e7eb;
    }
    
    .setup-options {
        margin-top: 1.5rem;
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 0.5rem;
    }
    
    .config-guide {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 0.75rem;
        padding: 2rem;
    }
    
    .config-guide h3 {
        margin: 0 0 1.5rem 0;
        color: #1f2937;
        font-size: 1.25rem;
        font-weight: 600;
    }
    
    .config-sections {
        display: flex;
        flex-direction: column;
        gap: 1.5rem;
    }
    
    .config-section {
        border: 1px solid #e5e7eb;
        border-radius: 0.5rem;
        padding: 1.5rem;
        background: #fafafa;
    }
    
    .config-section h4 {
        margin: 0 0 0.5rem 0;
        color: #1f2937;
        font-size: 1rem;
        font-weight: 600;
    }
    
    .config-section p {
        margin: 0 0 1rem 0;
        color: #6b7280;
        line-height: 1.5;
    }
    
    .config-section code {
        display: block;
        background: #1f2937;
        color: #f9fafb;
        padding: 0.75rem;
        border-radius: 0.375rem;
        font-family: 'Fira Code', monospace;
        font-size: 0.875rem;
    }
    
    .docs-intro {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin-bottom: 2rem;
        border-left-width: 4px;
        border-left-color: #8b5cf6;
    }
    
    .docs-intro p {
        margin: 0;
        color: #4b5563;
        line-height: 1.6;
    }
    
    .docs-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 1.5rem;
        margin-bottom: 2rem;
    }
    
    .doc-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 0.75rem;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    
    .doc-icon {
        font-size: 2rem;
        margin-bottom: 1rem;
    }
    
    .doc-card h3 {
        margin: 0 0 0.5rem 0;
        color: #1f2937;
        font-size: 1.125rem;
        font-weight: 600;
    }
    
    .doc-card p {
        margin: 0 0 1.5rem 0;
        color: #6b7280;
        line-height: 1.5;
    }
    
    .doc-actions {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .doc-link {
        background: #2563eb;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 0.375rem;
        font-size: 0.875rem;
        font-weight: 500;
        cursor: pointer;
        transition: background 0.2s;
    }
    
    .doc-link:hover {
        background: #1d4ed8;
    }
    
    .doc-status {
        font-size: 0.75rem;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        background: #f3f4f6;
        color: #6b7280;
        font-weight: 500;
    }
    
    .doc-status.live {
        background: #dcfce7;
        color: #166534;
    }
    
    .docs-tools {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 0.75rem;
        padding: 2rem;
    }
    
    .docs-tools h3 {
        margin: 0 0 1.5rem 0;
        color: #1f2937;
        font-size: 1.25rem;
        font-weight: 600;
    }
    
    .tools-list {
        display: flex;
        gap: 1rem;
        flex-wrap: wrap;
    }
    
    .tool-button {
        background: #f3f4f6;
        color: #374151;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 0.5rem;
        font-size: 0.875rem;
        font-weight: 500;
        cursor: pointer;
        transition: background 0.2s;
    }
    
    .tool-button:hover {
        background: #e5e7eb;
    }
    
    .support-intro {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin-bottom: 2rem;
        border-left-width: 4px;
        border-left-color: #f59e0b;
    }
    
    .support-intro p {
        margin: 0;
        color: #4b5563;
        line-height: 1.6;
    }
    
    .support-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1.5rem;
        margin-bottom: 2rem;
    }
    
    .support-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 0.75rem;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    
    .support-icon {
        font-size: 2.5rem;
        margin-bottom: 1rem;
    }
    
    .support-card h3 {
        margin: 0 0 0.5rem 0;
        color: #1f2937;
        font-size: 1.125rem;
        font-weight: 600;
    }
    
    .support-card p {
        margin: 0 0 1.5rem 0;
        color: #6b7280;
        line-height: 1.5;
    }
    
    .support-action {
        background: #2563eb;
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 0.5rem;
        font-size: 0.875rem;
        font-weight: 500;
        cursor: pointer;
        transition: background 0.2s;
    }
    
    .support-action:hover {
        background: #1d4ed8;
    }
    
    .system-info,
    .contact-info {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 0.75rem;
        padding: 2rem;
        margin-bottom: 1.5rem;
    }
    
    .system-info h3,
    .contact-info h3 {
        margin: 0 0 1rem 0;
        color: #1f2937;
        font-size: 1.25rem;
        font-weight: 600;
    }
    
    .info-block {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 0.5rem;
        padding: 1rem;
        position: relative;
    }
    
    .info-block code {
        display: block;
        font-family: 'Fira Code', monospace;
        font-size: 0.875rem;
        color: #1f2937;
        line-height: 1.5;
    }
    
    .copy-button {
        position: absolute;
        top: 0.5rem;
        right: 0.5rem;
        background: #e5e7eb;
        border: none;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.75rem;
        cursor: pointer;
    }
    
    .copy-button:hover {
        background: #d1d5db;
    }
    
    .contact-methods {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
    }
    
    .contact-method {
        display: flex;
        gap: 0.5rem;
        align-items: center;
    }
    
    .contact-method a {
        color: #2563eb;
        text-decoration: none;
        font-weight: 500;
    }
    
    .contact-method a:hover {
        text-decoration: underline;
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .help-header {
            flex-direction: column;
            gap: 1rem;
        }
        
        .system-status-card {
            min-width: auto;
            width: 100%;
        }
        
        .help-content {
            flex-direction: column;
        }
        
        .help-nav {
            width: 100%;
            border-right: none;
            border-bottom: 1px solid #e5e7eb;
        }
        
        .features-grid,
        .docs-grid,
        .support-grid {
            grid-template-columns: 1fr;
        }
        
        .troubleshooting-categories,
        .status-grid {
            grid-template-columns: 1fr;
        }
        
        .setup-options {
            flex-direction: column;
            align-items: center;
        }
        
        .tools-list {
            flex-direction: column;
        }
    }
</style>