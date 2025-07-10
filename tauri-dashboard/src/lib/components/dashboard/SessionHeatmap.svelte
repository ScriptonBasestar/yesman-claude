<script lang="ts">
  import { onMount } from 'svelte';
  import type { SessionData } from '$lib/types/session';
  
  // Props
  export let sessions: SessionData[] = [];
  export let selectedSession: string | null = null;
  export let timeRange: number = 7; // days
  export let updateInterval: number = 5000; // ms
  
  // Heatmap data structure
  interface HeatmapCell {
    day: number;
    hour: number;
    activity: number;
    date: Date;
    sessionName?: string;
  }
  
  // State
  let heatmapData: HeatmapCell[][] = [];
  let isLoading = true;
  let lastUpdate: Date = new Date();
  let hoveredCell: HeatmapCell | null = null;
  let tooltipPosition = { x: 0, y: 0 };
  
  // GitHub-style color intensity levels
  const intensityLevels = [
    'bg-base-200',           // 0: No activity
    'bg-success/20',         // 1: Low activity
    'bg-success/40',         // 2: Medium activity  
    'bg-success/60',         // 3: High activity
    'bg-success/80',         // 4: Very high activity
    'bg-success'             // 5: Maximum activity
  ];
  
  // Day labels
  const dayLabels = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  
  // Hour labels (every 4 hours)
  const hourLabels = ['12am', '4am', '8am', '12pm', '4pm', '8pm'];
  
  /**
   * Generate mock heatmap data
   * TODO: Replace with real tmux session activity data
   */
  function generateHeatmapData(): HeatmapCell[][] {
    const data: HeatmapCell[][] = [];
    const now = new Date();
    
    // Generate 7 days × 24 hours grid
    for (let day = 0; day < timeRange; day++) {
      const dayData: HeatmapCell[] = [];
      const currentDate = new Date(now);
      currentDate.setDate(now.getDate() - (timeRange - 1 - day));
      
      for (let hour = 0; hour < 24; hour++) {
        const cellDate = new Date(currentDate);
        cellDate.setHours(hour, 0, 0, 0);
        
        // Mock activity calculation
        const activity = calculateMockActivity(day, hour);
        
        dayData.push({
          day,
          hour,
          activity,
          date: cellDate,
          sessionName: selectedSession || undefined
        });
      }
      data.push(dayData);
    }
    
    return data;
  }
  
  /**
   * Calculate mock activity level (0-5)
   * TODO: Replace with real session activity calculation
   */
  function calculateMockActivity(day: number, hour: number): number {
    // Simulate realistic work patterns
    if (hour >= 9 && hour <= 17) {
      // Work hours: higher activity
      return Math.floor(Math.random() * 4) + 2; // 2-5
    } else if (hour >= 7 && hour <= 9 || hour >= 17 && hour <= 22) {
      // Morning/evening: medium activity
      return Math.floor(Math.random() * 3) + 1; // 1-3
    } else {
      // Night: low activity
      return Math.floor(Math.random() * 2); // 0-1
    }
  }
  
  /**
   * Get activity color class based on intensity
   */
  function getActivityColor(activity: number): string {
    return intensityLevels[Math.min(activity, intensityLevels.length - 1)];
  }
  
  /**
   * Handle cell hover for tooltip
   */
  function handleCellHover(event: MouseEvent, cell: HeatmapCell) {
    hoveredCell = cell;
    tooltipPosition = {
      x: event.clientX + 10,
      y: event.clientY - 10
    };
  }
  
  /**
   * Handle cell click for detailed view
   */
  function handleCellClick(cell: HeatmapCell) {
    console.log('Clicked cell:', cell);
    // TODO: Implement detailed activity view
  }
  
  /**
   * Update heatmap data
   */
  function updateHeatmapData() {
    isLoading = true;
    // Simulate API call delay
    setTimeout(() => {
      heatmapData = generateHeatmapData();
      lastUpdate = new Date();
      isLoading = false;
    }, 500);
  }
  
  /**
   * Get activity summary for tooltip
   */
  function getActivitySummary(cell: HeatmapCell): string {
    const activityLabels = ['No activity', 'Low', 'Medium', 'High', 'Very high', 'Maximum'];
    return activityLabels[cell.activity] || 'Unknown';
  }
  
  // Initialize and setup auto-update
  onMount(() => {
    updateHeatmapData();
    
    const interval = setInterval(() => {
      if (!isLoading) {
        updateHeatmapData();
      }
    }, updateInterval);
    
    return () => clearInterval(interval);
  });
  
  // Reactive updates when sessions or selectedSession changes
  $: if (sessions || selectedSession) {
    updateHeatmapData();
  }
</script>

<div class="session-heatmap">
  <!-- Header -->
  <div class="heatmap-header flex items-center justify-between mb-6">
    <div class="header-info">
      <h3 class="text-lg font-semibold flex items-center gap-2">
        🔥 Session Activity Heatmap
      </h3>
      <p class="text-sm text-base-content/70 mt-1">
        {#if selectedSession}
          Activity for session: <span class="font-medium">{selectedSession}</span>
        {:else}
          Combined activity across all sessions
        {/if}
      </p>
    </div>
    
    <div class="header-controls flex items-center gap-3">
      <!-- Last update indicator -->
      <div class="text-xs text-base-content/60">
        Last updated: {lastUpdate.toLocaleTimeString()}
      </div>
      
      <!-- Loading indicator -->
      {#if isLoading}
        <span class="loading loading-spinner loading-sm"></span>
      {/if}
      
      <!-- Refresh button -->
      <button 
        class="btn btn-ghost btn-sm"
        on:click={updateHeatmapData}
        disabled={isLoading}
      >
        🔄
      </button>
    </div>
  </div>
  
  <!-- Heatmap Container -->
  <div class="heatmap-container bg-base-100 border border-base-content/10 rounded-xl p-6">
    {#if isLoading && heatmapData.length === 0}
      <!-- Initial loading state -->
      <div class="loading-state flex items-center justify-center h-48">
        <div class="text-center">
          <span class="loading loading-spinner loading-lg mb-3"></span>
          <p class="text-base-content/70">Loading activity data...</p>
        </div>
      </div>
    {:else}
      <!-- Heatmap Grid -->
      <div class="heatmap-grid">
        <!-- Hour labels -->
        <div class="hour-labels grid grid-cols-6 gap-1 mb-2 ml-12">
          {#each hourLabels as label}
            <div class="text-xs text-base-content/60 text-center">{label}</div>
          {/each}
        </div>
        
        <!-- Days and cells -->
        <div class="days-container space-y-1">
          {#each heatmapData as dayData, dayIndex}
            <div class="day-row flex items-center gap-1">
              <!-- Day label -->
              <div class="day-label w-10 text-xs text-base-content/60">
                {dayLabels[dayData[0]?.date.getDay()] || ''}
              </div>
              
              <!-- Activity cells -->
              <div class="activity-cells grid grid-cols-24 gap-1">
                {#each dayData as cell}
                  <div
                    class="activity-cell w-3 h-3 rounded-sm cursor-pointer transition-all duration-200 hover:scale-125 hover:ring-2 hover:ring-primary/50 {getActivityColor(cell.activity)}"
                    role="button"
                    tabindex="0"
                    on:mouseenter={(e) => handleCellHover(e, cell)}
                    on:mouseleave={() => hoveredCell = null}
                    on:click={() => handleCellClick(cell)}
                    on:keydown={(e) => e.key === 'Enter' && handleCellClick(cell)}
                    title="{getActivitySummary(cell)} activity on {cell.date.toLocaleDateString()} at {cell.date.getHours()}:00"
                  ></div>
                {/each}
              </div>
            </div>
          {/each}
        </div>
        
        <!-- Legend -->
        <div class="heatmap-legend flex items-center justify-between mt-4 pt-4 border-t border-base-content/10">
          <div class="legend-left text-xs text-base-content/60">
            Less activity
          </div>
          
          <div class="legend-scale flex items-center gap-1">
            {#each intensityLevels as colorClass}
              <div class="w-3 h-3 rounded-sm {colorClass}"></div>
            {/each}
          </div>
          
          <div class="legend-right text-xs text-base-content/60">
            More activity
          </div>
        </div>
      </div>
    {/if}
  </div>
  
  <!-- Tooltip -->
  {#if hoveredCell}
    <div 
      class="heatmap-tooltip fixed z-50 bg-base-100 border border-base-content/20 rounded-lg p-3 shadow-lg pointer-events-none"
      style="left: {tooltipPosition.x}px; top: {tooltipPosition.y}px;"
    >
      <div class="tooltip-content text-sm">
        <div class="font-semibold">{getActivitySummary(hoveredCell)}</div>
        <div class="text-base-content/70">
          {hoveredCell.date.toLocaleDateString()}
        </div>
        <div class="text-base-content/70">
          {hoveredCell.date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
        {#if hoveredCell.sessionName}
          <div class="text-xs text-primary mt-1">
            Session: {hoveredCell.sessionName}
          </div>
        {/if}
      </div>
    </div>
  {/if}
</div>

<style>
  .session-heatmap {
    @apply w-full;
  }
  
  .heatmap-container {
    @apply relative;
  }
  
  .activity-cells {
    grid-template-columns: repeat(24, minmax(0, 1fr));
  }
  
  .activity-cell {
    @apply transition-all duration-200;
  }
  
  .activity-cell:hover {
    @apply transform scale-125 ring-2 ring-primary/50;
  }
  
  .day-label {
    @apply text-right pr-2;
  }
  
  .heatmap-tooltip {
    @apply transform -translate-x-1/2 -translate-y-full;
    animation: fadeIn 0.2s ease-out;
  }
  
  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateX(-50%) translateY(-100%) scale(0.9);
    }
    to {
      opacity: 1;
      transform: translateX(-50%) translateY(-100%) scale(1);
    }
  }
  
  /* Loading animation */
  .loading-state {
    animation: pulse 2s infinite;
  }
  
  /* Responsive adjustments */
  @media (max-width: 768px) {
    .hour-labels {
      @apply grid-cols-3;
    }
    
    .activity-cell {
      @apply w-2 h-2;
    }
    
    .day-label {
      @apply w-8 text-xs;
    }
  }
  
  /* Accessibility */
  .activity-cell:focus {
    @apply outline-2 outline-primary outline-offset-1;
  }
  
  /* Print styles */
  @media print {
    .heatmap-tooltip {
      @apply hidden;
    }
    
    .header-controls {
      @apply hidden;
    }
  }
</style>