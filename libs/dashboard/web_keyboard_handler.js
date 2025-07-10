/**
 * Web Keyboard Navigation Handler
 * 
 * JavaScript implementation of keyboard navigation for web dashboard interfaces
 * Provides consistent keyboard shortcuts and focus management across browsers
 */

class KeyModifier {
    static CTRL = 'ctrl';
    static SHIFT = 'shift';
    static ALT = 'alt';
    static META = 'meta';
}

class NavigationContext {
    static GLOBAL = 'global';
    static DASHBOARD = 'dashboard';
    static MODAL = 'modal';
    static FORM = 'form';
    static LIST = 'list';
    static TREE = 'tree';
    static TABLE = 'table';
    static VIM_NORMAL = 'vim_normal';
    static VIM_INSERT = 'vim_insert';
    static VIM_VISUAL = 'vim_visual';
}

class KeyBinding {
    constructor(key, modifiers = [], action = '', description = '', context = null, enabled = true, priority = 0) {
        this.key = key.toLowerCase();
        this.modifiers = modifiers.map(mod => typeof mod === 'string' ? mod.toLowerCase() : mod);
        this.action = action;
        this.description = description;
        this.context = context;
        this.enabled = enabled;
        this.priority = priority;
    }

    get keyCombination() {
        const parts = [];
        
        // Add modifiers in standard order
        const modOrder = [KeyModifier.CTRL, KeyModifier.SHIFT, KeyModifier.ALT, KeyModifier.META];
        for (const mod of modOrder) {
            if (this.modifiers.includes(mod)) {
                parts.push(mod);
            }
        }
        
        parts.push(this.key);
        return parts.join('+');
    }

    matches(key, modifiers) {
        return (
            this.key === key.toLowerCase() &&
            this.modifiers.length === modifiers.length &&
            this.modifiers.every(mod => modifiers.includes(mod)) &&
            this.enabled
        );
    }

    toObject() {
        return {
            key: this.key,
            modifiers: this.modifiers,
            action: this.action,
            description: this.description,
            context: this.context,
            enabled: this.enabled,
            priority: this.priority
        };
    }

    static fromObject(data) {
        return new KeyBinding(
            data.key,
            data.modifiers || [],
            data.action || '',
            data.description || '',
            data.context || null,
            data.enabled !== false,
            data.priority || 0
        );
    }
}

class FocusableElement {
    constructor(elementId, elementType = 'generic', tabIndex = 0, enabled = true, context = null) {
        this.elementId = elementId;
        this.elementType = elementType;
        this.tabIndex = tabIndex;
        this.enabled = enabled;
        this.context = context;
    }

    get element() {
        return document.getElementById(this.elementId);
    }

    toObject() {
        return {
            elementId: this.elementId,
            elementType: this.elementType,
            tabIndex: this.tabIndex,
            enabled: this.enabled,
            context: this.context
        };
    }
}

class WebKeyboardNavigationManager {
    constructor() {
        this.bindings = new Map();
        this.actions = new Map();
        this.focusableElements = [];
        this.currentFocusIndex = -1;
        this.currentContext = NavigationContext.GLOBAL;
        this.vimModeEnabled = false;
        this.vimMode = NavigationContext.VIM_NORMAL;
        this.debugMode = false;
        
        // Bind event listeners
        this.handleKeyDown = this.handleKeyDown.bind(this);
        this.handleFocus = this.handleFocus.bind(this);
        this.handleBlur = this.handleBlur.bind(this);
        
        this.setupEventListeners();
        this.setupDefaultBindings();
    }

    setupEventListeners() {
        document.addEventListener('keydown', this.handleKeyDown, true);
        document.addEventListener('focus', this.handleFocus, true);
        document.addEventListener('blur', this.handleBlur, true);
        
        // Prevent default browser shortcuts for our custom ones
        document.addEventListener('keydown', (event) => {
            const key = event.key.toLowerCase();
            const modifiers = this.getModifiersFromEvent(event);
            const keyCombo = this.getKeyCombination(key, modifiers);
            
            if (this.bindings.has(keyCombo)) {
                const bindings = this.bindings.get(keyCombo);
                for (const binding of bindings) {
                    if (this.isBindingActive(binding)) {
                        event.preventDefault();
                        event.stopPropagation();
                        break;
                    }
                }
            }
        }, true);
    }

    setupDefaultBindings() {
        // Global navigation
        this.registerBinding('Tab', [], 'focus_next', 'Next element', NavigationContext.GLOBAL);
        this.registerBinding('Tab', [KeyModifier.SHIFT], 'focus_prev', 'Previous element', NavigationContext.GLOBAL);
        this.registerBinding('Enter', [], 'activate', 'Activate element', NavigationContext.GLOBAL);
        this.registerBinding('Escape', [], 'cancel', 'Cancel/Close', NavigationContext.GLOBAL);
        
        // Common shortcuts
        this.registerBinding('r', [KeyModifier.CTRL], 'refresh', 'Refresh', NavigationContext.GLOBAL);
        this.registerBinding('f', [KeyModifier.CTRL], 'find', 'Find', NavigationContext.GLOBAL);
        this.registerBinding('s', [KeyModifier.CTRL], 'save', 'Save', NavigationContext.GLOBAL);
        this.registerBinding('z', [KeyModifier.CTRL], 'undo', 'Undo', NavigationContext.GLOBAL);
        this.registerBinding('y', [KeyModifier.CTRL], 'redo', 'Redo', NavigationContext.GLOBAL);
        
        // Dashboard navigation
        this.registerBinding('1', [], 'switch_view_1', 'View 1', NavigationContext.DASHBOARD);
        this.registerBinding('2', [], 'switch_view_2', 'View 2', NavigationContext.DASHBOARD);
        this.registerBinding('3', [], 'switch_view_3', 'View 3', NavigationContext.DASHBOARD);
        this.registerBinding('4', [], 'switch_view_4', 'View 4', NavigationContext.DASHBOARD);
        this.registerBinding('5', [], 'switch_view_5', 'View 5', NavigationContext.DASHBOARD);
        
        // Arrow key navigation
        this.registerBinding('ArrowUp', [], 'navigate_up', 'Navigate up', NavigationContext.GLOBAL);
        this.registerBinding('ArrowDown', [], 'navigate_down', 'Navigate down', NavigationContext.GLOBAL);
        this.registerBinding('ArrowLeft', [], 'navigate_left', 'Navigate left', NavigationContext.GLOBAL);
        this.registerBinding('ArrowRight', [], 'navigate_right', 'Navigate right', NavigationContext.GLOBAL);
        
        // Vim mode bindings
        this.registerBinding(':', [], 'vim_command_mode', 'Command mode', NavigationContext.VIM_NORMAL);
        this.registerBinding('i', [], 'vim_insert_mode', 'Insert mode', NavigationContext.VIM_NORMAL);
        this.registerBinding('v', [], 'vim_visual_mode', 'Visual mode', NavigationContext.VIM_NORMAL);
        this.registerBinding('h', [], 'vim_left', 'Left', NavigationContext.VIM_NORMAL);
        this.registerBinding('j', [], 'vim_down', 'Down', NavigationContext.VIM_NORMAL);
        this.registerBinding('k', [], 'vim_up', 'Up', NavigationContext.VIM_NORMAL);
        this.registerBinding('l', [], 'vim_right', 'Right', NavigationContext.VIM_NORMAL);
        this.registerBinding('Escape', [], 'vim_normal_mode', 'Normal mode', NavigationContext.VIM_INSERT);
        
        this.setupDefaultActions();
    }

    setupDefaultActions() {
        this.registerAction('focus_next', () => this.focusNext());
        this.registerAction('focus_prev', () => this.focusPrev());
        this.registerAction('activate', () => this.activateElement());
        this.registerAction('cancel', () => this.cancelAction());
        this.registerAction('refresh', () => this.refreshAction());
        this.registerAction('find', () => this.findAction());
        this.registerAction('navigate_up', () => this.navigateDirection('up'));
        this.registerAction('navigate_down', () => this.navigateDirection('down'));
        this.registerAction('navigate_left', () => this.navigateDirection('left'));
        this.registerAction('navigate_right', () => this.navigateDirection('right'));
        
        // Vim mode actions
        this.registerAction('vim_command_mode', () => this.vimCommandMode());
        this.registerAction('vim_insert_mode', () => this.vimInsertMode());
        this.registerAction('vim_visual_mode', () => this.vimVisualMode());
        this.registerAction('vim_normal_mode', () => this.vimNormalMode());
        this.registerAction('vim_left', () => this.navigateDirection('left'));
        this.registerAction('vim_down', () => this.navigateDirection('down'));
        this.registerAction('vim_up', () => this.navigateDirection('up'));
        this.registerAction('vim_right', () => this.navigateDirection('right'));
    }

    registerBinding(key, modifiers = [], action = '', description = '', context = null, priority = 0) {
        const binding = new KeyBinding(key, modifiers, action, description, context, true, priority);
        const keyCombo = binding.keyCombination;
        
        if (!this.bindings.has(keyCombo)) {
            this.bindings.set(keyCombo, []);
        }
        
        const bindings = this.bindings.get(keyCombo);
        bindings.push(binding);
        bindings.sort((a, b) => b.priority - a.priority);
        
        if (this.debugMode) {
            console.log(`Registered key binding: ${keyCombo} -> ${action}`);
        }
    }

    unregisterBinding(key, modifiers = [], context = null) {
        const keyCombo = this.getKeyCombination(key.toLowerCase(), modifiers);
        
        if (!this.bindings.has(keyCombo)) {
            return false;
        }
        
        const bindings = this.bindings.get(keyCombo);
        const originalLength = bindings.length;
        
        if (context === null) {
            this.bindings.delete(keyCombo);
        } else {
            const filtered = bindings.filter(binding => binding.context !== context);
            if (filtered.length === 0) {
                this.bindings.delete(keyCombo);
            } else {
                this.bindings.set(keyCombo, filtered);
            }
        }
        
        const removedCount = originalLength - (this.bindings.get(keyCombo)?.length || 0);
        if (this.debugMode) {
            console.log(`Removed ${removedCount} bindings for ${keyCombo}`);
        }
        return removedCount > 0;
    }

    registerAction(actionName, handler) {
        this.actions.set(actionName, handler);
        if (this.debugMode) {
            console.log(`Registered action: ${actionName}`);
        }
    }

    unregisterAction(actionName) {
        const existed = this.actions.has(actionName);
        this.actions.delete(actionName);
        if (this.debugMode && existed) {
            console.log(`Unregistered action: ${actionName}`);
        }
        return existed;
    }

    handleKeyDown(event) {
        const key = event.key;
        const modifiers = this.getModifiersFromEvent(event);
        
        if (this.debugMode) {
            console.log(`Key event: ${key} with modifiers: ${modifiers.join(', ')}`);
        }
        
        return this.handleKeyEvent(key, modifiers);
    }

    handleKeyEvent(key, modifiers = [], context = null) {
        if (context === null) {
            context = this.currentContext;
        }
        
        // Special handling for Vim mode
        if (this.vimModeEnabled && [NavigationContext.VIM_NORMAL, NavigationContext.VIM_INSERT, NavigationContext.VIM_VISUAL].includes(context)) {
            context = this.vimMode;
        }
        
        const keyCombo = this.getKeyCombination(key.toLowerCase(), modifiers);
        
        if (!this.bindings.has(keyCombo)) {
            if (this.debugMode) {
                console.log(`No bindings found for ${keyCombo}`);
            }
            return false;
        }
        
        const bindings = this.bindings.get(keyCombo);
        let bestBinding = null;
        
        for (const binding of bindings) {
            if (!binding.enabled) continue;
            
            if (this.isBindingActive(binding, context)) {
                if (bestBinding === null || binding.priority > bestBinding.priority) {
                    bestBinding = binding;
                }
            }
        }
        
        if (bestBinding === null) {
            if (this.debugMode) {
                console.log(`No matching binding for ${keyCombo} in context ${context}`);
            }
            return false;
        }
        
        return this.executeAction(bestBinding.action);
    }

    isBindingActive(binding, context = null) {
        if (context === null) {
            context = this.currentContext;
        }
        
        return (
            binding.context === null ||
            binding.context === context ||
            binding.context === NavigationContext.GLOBAL
        );
    }

    executeAction(actionName, ...args) {
        if (!this.actions.has(actionName)) {
            console.warn(`Unknown action: ${actionName}`);
            return false;
        }
        
        try {
            const handler = this.actions.get(actionName);
            handler(...args);
            
            if (this.debugMode) {
                console.log(`Executed action: ${actionName}`);
            }
            return true;
        } catch (error) {
            console.error(`Error executing action ${actionName}:`, error);
            return false;
        }
    }

    getModifiersFromEvent(event) {
        const modifiers = [];
        if (event.ctrlKey) modifiers.push(KeyModifier.CTRL);
        if (event.shiftKey) modifiers.push(KeyModifier.SHIFT);
        if (event.altKey) modifiers.push(KeyModifier.ALT);
        if (event.metaKey) modifiers.push(KeyModifier.META);
        return modifiers;
    }

    getKeyCombination(key, modifiers) {
        const parts = [];
        
        const modOrder = [KeyModifier.CTRL, KeyModifier.SHIFT, KeyModifier.ALT, KeyModifier.META];
        for (const mod of modOrder) {
            if (modifiers.includes(mod)) {
                parts.push(mod);
            }
        }
        
        parts.push(key.toLowerCase());
        return parts.join('+');
    }

    setContext(context) {
        this.currentContext = context;
        if (this.debugMode) {
            console.log(`Navigation context changed to: ${context}`);
        }
    }

    // Focus management
    addFocusableElement(elementId, elementType = 'generic', tabIndex = 0, context = null) {
        const element = new FocusableElement(elementId, elementType, tabIndex, true, context);
        
        // Insert in tab order
        let insertIndex = this.focusableElements.length;
        for (let i = 0; i < this.focusableElements.length; i++) {
            if (this.focusableElements[i].tabIndex > tabIndex) {
                insertIndex = i;
                break;
            }
        }
        
        this.focusableElements.splice(insertIndex, 0, element);
        if (this.debugMode) {
            console.log(`Added focusable element: ${elementId}`);
        }
    }

    removeFocusableElement(elementId) {
        const index = this.focusableElements.findIndex(el => el.elementId === elementId);
        if (index !== -1) {
            this.focusableElements.splice(index, 1);
            
            if (index <= this.currentFocusIndex) {
                this.currentFocusIndex--;
            }
            
            if (this.debugMode) {
                console.log(`Removed focusable element: ${elementId}`);
            }
            return true;
        }
        return false;
    }

    focusNext() {
        if (this.focusableElements.length === 0) return false;
        
        const startIndex = this.currentFocusIndex;
        let nextIndex = (startIndex + 1) % this.focusableElements.length;
        let attempts = 0;
        
        while (attempts < this.focusableElements.length) {
            const element = this.focusableElements[nextIndex];
            
            if (element.enabled && this.isElementInContext(element)) {
                this.currentFocusIndex = nextIndex;
                this.focusElementByObject(element);
                return true;
            }
            
            nextIndex = (nextIndex + 1) % this.focusableElements.length;
            attempts++;
        }
        
        return false;
    }

    focusPrev() {
        if (this.focusableElements.length === 0) return false;
        
        const startIndex = this.currentFocusIndex;
        let prevIndex = startIndex === -1 ? this.focusableElements.length - 1 : (startIndex - 1 + this.focusableElements.length) % this.focusableElements.length;
        let attempts = 0;
        
        while (attempts < this.focusableElements.length) {
            const element = this.focusableElements[prevIndex];
            
            if (element.enabled && this.isElementInContext(element)) {
                this.currentFocusIndex = prevIndex;
                this.focusElementByObject(element);
                return true;
            }
            
            prevIndex = (prevIndex - 1 + this.focusableElements.length) % this.focusableElements.length;
            attempts++;
        }
        
        return false;
    }

    focusElement(elementId) {
        const index = this.focusableElements.findIndex(el => el.elementId === elementId);
        if (index !== -1 && this.focusableElements[index].enabled) {
            this.currentFocusIndex = index;
            this.focusElementByObject(this.focusableElements[index]);
            return true;
        }
        return false;
    }

    focusElementByObject(elementObj) {
        const domElement = elementObj.element;
        if (domElement) {
            domElement.focus();
            if (this.debugMode) {
                console.log(`Focused element: ${elementObj.elementId}`);
            }
        }
    }

    isElementInContext(element) {
        return element.context === null || element.context === this.currentContext;
    }

    getCurrentFocus() {
        if (this.currentFocusIndex >= 0 && this.currentFocusIndex < this.focusableElements.length) {
            return this.focusableElements[this.currentFocusIndex];
        }
        return null;
    }

    handleFocus(event) {
        const elementId = event.target.id;
        if (elementId) {
            const index = this.focusableElements.findIndex(el => el.elementId === elementId);
            if (index !== -1) {
                this.currentFocusIndex = index;
            }
        }
    }

    handleBlur(event) {
        // Handle blur events if needed
    }

    // Default action implementations
    activateElement() {
        const element = this.getCurrentFocus();
        if (element) {
            const domElement = element.element;
            if (domElement) {
                domElement.click();
                if (this.debugMode) {
                    console.log(`Activated element: ${element.elementId}`);
                }
            }
        }
    }

    cancelAction() {
        if (this.debugMode) {
            console.log('Cancel action triggered');
        }
        // Close modals, cancel forms, etc.
        const event = new CustomEvent('keyboard-cancel');
        document.dispatchEvent(event);
    }

    refreshAction() {
        if (this.debugMode) {
            console.log('Refresh action triggered');
        }
        const event = new CustomEvent('keyboard-refresh');
        document.dispatchEvent(event);
    }

    findAction() {
        if (this.debugMode) {
            console.log('Find action triggered');
        }
        const event = new CustomEvent('keyboard-find');
        document.dispatchEvent(event);
    }

    navigateDirection(direction) {
        if (this.debugMode) {
            console.log(`Navigate ${direction}`);
        }
        const event = new CustomEvent('keyboard-navigate', { detail: { direction } });
        document.dispatchEvent(event);
    }

    // Vim mode methods
    enableVimMode() {
        this.vimModeEnabled = true;
        this.vimMode = NavigationContext.VIM_NORMAL;
        if (this.debugMode) {
            console.log('Vim mode enabled');
        }
    }

    disableVimMode() {
        this.vimModeEnabled = false;
        if (this.debugMode) {
            console.log('Vim mode disabled');
        }
    }

    vimCommandMode() {
        if (this.vimModeEnabled) {
            if (this.debugMode) {
                console.log('Vim command mode');
            }
        }
    }

    vimInsertMode() {
        if (this.vimModeEnabled) {
            this.vimMode = NavigationContext.VIM_INSERT;
            if (this.debugMode) {
                console.log('Vim insert mode');
            }
        }
    }

    vimVisualMode() {
        if (this.vimModeEnabled) {
            this.vimMode = NavigationContext.VIM_VISUAL;
            if (this.debugMode) {
                console.log('Vim visual mode');
            }
        }
    }

    vimNormalMode() {
        if (this.vimModeEnabled) {
            this.vimMode = NavigationContext.VIM_NORMAL;
            if (this.debugMode) {
                console.log('Vim normal mode');
            }
        }
    }

    // Utility methods
    exportBindings() {
        const exported = {};
        for (const [keyCombo, bindings] of this.bindings) {
            exported[keyCombo] = bindings.map(binding => binding.toObject());
        }
        return exported;
    }

    importBindings(bindingsData) {
        this.bindings.clear();
        
        for (const [keyCombo, bindingList] of Object.entries(bindingsData)) {
            const bindings = bindingList.map(data => KeyBinding.fromObject(data));
            this.bindings.set(keyCombo, bindings);
        }
    }

    getHelpText(context = null) {
        if (context === null) {
            context = this.currentContext;
        }
        
        const helpLines = [];
        const seenActions = new Set();
        
        for (const [keyCombo, bindings] of this.bindings) {
            for (const binding of bindings) {
                if (!binding.enabled || seenActions.has(binding.action)) {
                    continue;
                }
                
                if (this.isBindingActive(binding, context)) {
                    helpLines.push(`${keyCombo.padEnd(20)} ${binding.description}`);
                    seenActions.add(binding.action);
                }
            }
        }
        
        return helpLines.sort();
    }

    setDebugMode(enabled) {
        this.debugMode = enabled;
        console.log(`Keyboard navigation debug mode: ${enabled ? 'enabled' : 'disabled'}`);
    }

    destroy() {
        document.removeEventListener('keydown', this.handleKeyDown, true);
        document.removeEventListener('focus', this.handleFocus, true);
        document.removeEventListener('blur', this.handleBlur, true);
        
        this.bindings.clear();
        this.actions.clear();
        this.focusableElements = [];
    }
}

// Global instance management
let globalKeyboardManager = null;

function getKeyboardManager() {
    if (globalKeyboardManager === null) {
        globalKeyboardManager = new WebKeyboardNavigationManager();
    }
    return globalKeyboardManager;
}

function resetKeyboardManager() {
    if (globalKeyboardManager) {
        globalKeyboardManager.destroy();
    }
    globalKeyboardManager = null;
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        WebKeyboardNavigationManager,
        KeyBinding,
        FocusableElement,
        KeyModifier,
        NavigationContext,
        getKeyboardManager,
        resetKeyboardManager
    };
}

// Export for AMD
if (typeof define === 'function' && define.amd) {
    define([], function() {
        return {
            WebKeyboardNavigationManager,
            KeyBinding,
            FocusableElement,
            KeyModifier,
            NavigationContext,
            getKeyboardManager,
            resetKeyboardManager
        };
    });
}

// Global export for browser
if (typeof window !== 'undefined') {
    window.WebKeyboardNavigationManager = WebKeyboardNavigationManager;
    window.KeyBinding = KeyBinding;
    window.FocusableElement = FocusableElement;
    window.KeyModifier = KeyModifier;
    window.NavigationContext = NavigationContext;
    window.getKeyboardManager = getKeyboardManager;
    window.resetKeyboardManager = resetKeyboardManager;
}