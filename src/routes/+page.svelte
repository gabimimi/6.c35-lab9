<script>
	import { onMount } from 'svelte';
	import mapboxgl from 'mapbox-gl';
	import 'mapbox-gl/dist/mapbox-gl.css';

	// Prefer .env (see .env.example). You can also assign a string here for quick local tests.
	mapboxgl.accessToken =
		import.meta.env.PUBLIC_MAPBOX_ACCESS_TOKEN ?? 'your access token here';

	onMount(() => {
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

	#map {
		flex: 1;
		min-height: 12rem;
		background: #d4e4f4;
	}
</style>
