<script lang="ts">
  import { onMount } from 'svelte';
  import { scaleLinear } from 'd3-scale';
  import { select } from 'd3-selection';
  import { timeFormat } from 'd3-time-format';
  import { format } from 'd3-format';

  export let sessionName: string;
  export let days: number = 7;

  let heatmapData: any = null;
  let loading = true;
  let error: string | null = null;

  const fetchHeatmapData = async () => {
    loading = true;
    error = null;
    try {
      const response = await fetch(`/web/api/heatmap/${sessionName}?days=${days}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      heatmapData = data.heatmap;
    } catch (e: any) {
      error = e.message;
    } finally {
      loading = false;
    }
  };

  onMount(() => {
    fetchHeatmapData();
  });

  // D3.js rendering logic (simplified for brevity)
  // This would typically be more complex with proper SVG/Canvas rendering
  $: if (heatmapData && !loading) {
    // Basic rendering for demonstration
    // In a real app, use D3 to append SVG elements
    console.log("Rendering heatmap with data:", heatmapData);
    // Example: You would iterate over heatmapData to draw cells
    // For now, just a placeholder message
  }

  const daysOfWeek = ['월', '화', '수', '목', '금', '토', '일'];
  const hoursOfDay = Array.from({ length: 24 }, (_, i) => i);

  const colorScale = scaleLinear()
    .domain([0, 10, 20, 30]) // Example activity levels
    .range(['#ebedf0', '#9be9a8', '#40c463', '#30a14e', '#216e39']); // GitHub-like greens

  const tooltipFormat = (day: number, hour: number, count: number) => {
    return `요일: ${daysOfWeek[day]}, 시간: ${hour}시, 활동: ${count}`;
  };
</script>

<div class="heatmap-container">
  {#if loading}
    <p>히트맵 데이터를 불러오는 중...</p>
  {:else if error}
    <p class="error">오류: {error}</p>
  {:else if heatmapData}
    <h3 class="text-lg font-semibold mb-2">세션 활동 히트맵 ({sessionName})</h3>
    <div class="grid grid-cols-25 gap-1 p-2 bg-gray-100 rounded-lg dark:bg-gray-800">
      <div class="col-span-1"></div> {#each hoursOfDay as hour}
        <div class="text-center text-xs font-medium text-gray-500 dark:text-gray-400">{hour}</div>
      {/each}
      {#each daysOfWeek as dayName, dayIndex}
        <div class="text-right text-xs font-medium text-gray-500 dark:text-gray-400 pr-1">{dayName}</div>
        {#each hoursOfDay as hourIndex}
          {@const activityCount = heatmapData[dayIndex]?.[hourIndex] || 0}
          <div
            class="w-4 h-4 rounded-sm cursor-pointer transition-colors duration-100 ease-in-out"
            style="background-color: {colorScale(activityCount)};"
            title={tooltipFormat(dayIndex, hourIndex, activityCount)}
          ></div>
        {/each}
      {/each}
    </div>
  {:else}
    <p>히트맵 데이터를 불러올 수 없습니다.</p>
  {/if}
</div>

<style>
  .heatmap-container {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol";
    max-width: 100%;
    overflow-x: auto;
  }
  .grid-cols-25 {
    grid-template-columns: repeat(25, minmax(0, 1fr));
  }
  .error {
    color: #ef4444; /* Tailwind red-500 */
  }
</style>
