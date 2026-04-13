<script>
	import { onMount } from 'svelte';
	import mapboxgl from 'mapbox-gl';
	import 'mapbox-gl/dist/mapbox-gl.css';

	// Inlined at build time: .env locally, or GitHub Actions secret PUBLIC_MAPBOX_ACCESS_TOKEN.
	const token = import.meta.env.PUBLIC_MAPBOX_ACCESS_TOKEN ?? '';
	mapboxgl.accessToken = token;

	onMount(() => {
		if (!token) return;

		const map = new mapboxgl.Map({
			container: 'map',
			style: 'mapbox://styles/mapbox/streets-v12',
			center: [-71.1097, 42.3736],
			zoom: 12,
			minZoom: 8,
			maxZoom: 18,
		});

		return () => map.remove();
	});
</script>

<div class="page">
	<h1>🚴Bikewatching</h1>
	{#if !token}
		<p class="token-warning">
			Map is disabled: no Mapbox token was available when this site was built. Add a repository
			secret named <code>PUBLIC_MAPBOX_ACCESS_TOKEN</code> (same value as in your local
			<code>.env</code>), then push again or re-run the deploy workflow.
		</p>
	{/if}
	<div id="map"></div>
</div>

<style>
	@import url('$lib/global.css');

	.page {
		display: flex;
		flex-direction: column;
		flex: 1;
		min-height: 0;
		width: 100%;
	}

	h1 {
		flex-shrink: 0;
	}

	.token-warning {
		flex-shrink: 0;
		margin: 0 0 0.75rem;
		padding: 0.75rem 1rem;
		background: #fff3cd;
		border: 1px solid #e6d89c;
		border-radius: 6px;
		font-size: 0.95rem;
	}

	.token-warning code {
		font-size: 0.88em;
	}

	#map {
		flex: 1;
		min-height: 12rem;
		background: #d4e4f4;
	}
</style>
