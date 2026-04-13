<script>
	import { onMount } from 'svelte';
	import mapboxgl from "mapbox-gl";
	import * as d3 from "d3";
	import { PUBLIC_MAPBOX_ACCESS_TOKEN } from '$env/static/public';

	mapboxgl.accessToken = PUBLIC_MAPBOX_ACCESS_TOKEN;

	let map;
	let stations = [];
	let trips = [];
	let departures;
	let arrivals;
	let timeFilter = -1;

	$: timeFilterLabel = new Date(0, 0, 0, 0, timeFilter)
		.toLocaleString("en", { timeStyle: "short" });

	function minutesSinceMidnight(date) {
		return date.getHours() * 60 + date.getMinutes();
	}

	$: filteredTrips = timeFilter === -1
		? trips
		: trips.filter(trip => {
			let startedMinutes = minutesSinceMidnight(trip.started_at);
			let endedMinutes = minutesSinceMidnight(trip.ended_at);
			return Math.abs(startedMinutes - timeFilter) <= 60
				|| Math.abs(endedMinutes - timeFilter) <= 60;
		});

	$: filteredDepartures = d3.rollup(filteredTrips, v => v.length, d => d.start_station_id);
	$: filteredArrivals = d3.rollup(filteredTrips, v => v.length, d => d.end_station_id);

	$: filteredStations = stations.map(station => {
		const id = station.Number;
		const arr = filteredArrivals.get(id) ?? 0;
		const dep = filteredDepartures.get(id) ?? 0;
		return {
			...station,
			arrivals: arr,
			departures: dep,
			totalTraffic: arr + dep,
		};
	});

	$: radiusScale = d3.scaleSqrt()
		.domain([0, d3.max(stations, d => d.totalTraffic) || 0])
		.range(timeFilter === -1 ? [0, 35] : [5, 40]);

	let stationFlow = d3.scaleQuantize()
		.domain([0, 1])
		.range([0, 0.5, 1]);

	let selectedStation = null;
	let isochrone = null;
	let mapViewChanged = 0;

	const urlBase = 'https://api.mapbox.com/isochrone/v1/mapbox/';
	const profile = 'cycling';
	const minutes = [5, 10, 15, 20];
	const contourColors = [
		"03045e",
		"0077b6",
		"00b4d8",
		"90e0ef"
	];

	async function getIso(lon, lat) {
		const base = `${urlBase}${profile}/${lon},${lat}`;
		const params = new URLSearchParams({
			contours_minutes: minutes.join(','),
			contours_colors: contourColors.join(','),
			polygons: 'true',
			access_token: mapboxgl.accessToken
		});
		const url = `${base}?${params.toString()}`;
		const query = await fetch(url, { method: 'GET' });
		isochrone = await query.json();
	}

	$: if (selectedStation) {
		getIso(+selectedStation.Long, +selectedStation.Lat);
	} else {
		isochrone = null;
	}

	function geoJSONPolygonToPath(feature) {
		const path = d3.path();
		const rings = feature.geometry.coordinates;
		for (const ring of rings) {
			for (let i = 0; i < ring.length; i++) {
				const [lng, lat] = ring[i];
				const { x, y } = map.project([lng, lat]);
				if (i === 0) path.moveTo(x, y);
				else path.lineTo(x, y);
			}
			path.closePath();
		}
		return path.toString();
	}

	async function initMap() {
		map = new mapboxgl.Map({
			container: 'map',
			style: 'mapbox://styles/mapbox/streets-v12',
			center: [-71.09415, 42.36027],
			zoom: 12,
			minZoom: 8,
			maxZoom: 18,
		});

		await new Promise(resolve => map.on("load", resolve));

		map.addSource("boston_route", {
			type: "geojson",
			data: "https://bostonopendata-boston.opendata.arcgis.com/datasets/boston::existing-bike-network-2022.geojson?outSR=%7B%22latestWkid%22%3A3857%2C%22wkid%22%3A102100%7D",
		});

		map.addLayer({
			id: "bike-lanes",
			type: "line",
			source: "boston_route",
			paint: {
				"line-color": "#4a6fa5",
				"line-width": 3,
				"line-opacity": 0.4,
			},
		});

		map.addSource("cambridge_route", {
			type: "geojson",
			data: "https://raw.githubusercontent.com/cambridgegis/cambridgegis_data/main/Recreation/Bike_Facilities/RECREATION_BikeFacilities.geojson",
		});

		map.addLayer({
			id: "cambridge-bike-lanes",
			type: "line",
			source: "cambridge_route",
			paint: {
				"line-color": "#4a6fa5",
				"line-width": 3,
				"line-opacity": 0.4,
			},
		});

		stations = await d3.csv("https://vis-society.github.io/labs/9/data/bluebikes-stations.csv");

		trips = await d3.csv("https://vis-society.github.io/labs/9/data/bluebikes-traffic-2024-03.csv").then(trips => {
			for (let trip of trips) {
				trip.started_at = new Date(trip.started_at);
				trip.ended_at = new Date(trip.ended_at);
			}
			return trips;
		});

		departures = d3.rollup(trips, v => v.length, d => d.start_station_id);
		arrivals = d3.rollup(trips, v => v.length, d => d.end_station_id);

		stations = stations.map(station => {
			let id = station.Number;
			station.arrivals = arrivals.get(id) ?? 0;
			station.departures = departures.get(id) ?? 0;
			station.totalTraffic = station.arrivals + station.departures;
			return station;
		});

		map.on("move", () => {
			stations = stations;
			mapViewChanged++;
		});
	}

	function getCoords(station) {
		let point = new mapboxgl.LngLat(+station.Long, +station.Lat);
		let { x, y } = map.project(point);
		return { cx: x, cy: y };
	}

	onMount(() => {
		initMap();
		return () => map?.remove();
	});
</script>

<div class="page">
	<header>
		<h1>🚴Bikewatching</h1>
		<label>
			Filter by time:
			<input type="range" min="-1" max="1440" bind:value={timeFilter} />
			{#if timeFilter !== -1}
				<time>{timeFilterLabel}</time>
			{:else}
				<em>(any time)</em>
			{/if}
		</label>
	</header>
	<div class="map-container">
		<div id="map"></div>
		<svg>
			{#key mapViewChanged}
				{#if isochrone}
					{#each isochrone.features as feature}
						<path
							d={geoJSONPolygonToPath(feature)}
							fill={"#" + feature.properties.fillColor}
							fill-opacity="0.15"
							stroke={"#" + feature.properties.fillColor}
							stroke-opacity="0.3"
							stroke-width="0.5"
						>
							<title>{feature.properties.contour} minutes of biking</title>
						</path>
					{/each}
				{/if}
				{#each filteredStations as station}
					{@const { cx, cy } = getCoords(station)}
					<!-- svelte-ignore a11y_no_static_element_interactions -->
					<circle
						{cx} {cy}
						r={radiusScale(station.totalTraffic)}
						style="--departure-ratio: {stationFlow(station.departures / station.totalTraffic)}"
						class={station?.Number === selectedStation?.Number ? "selected" : ""}
						on:mousedown={() => selectedStation = selectedStation?.Number !== station?.Number ? station : null}
					>
						<title>{station.totalTraffic} trips ({station.departures} departures, {station.arrivals} arrivals)</title>
					</circle>
				{/each}
			{/key}
		</svg>
	</div>
	<div class="legend">
		<div style="--departure-ratio: 1">More departures</div>
		<div style="--departure-ratio: 0.5">Balanced</div>
		<div style="--departure-ratio: 0">More arrivals</div>
	</div>
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

	header {
		display: flex;
		gap: 1em;
		align-items: baseline;
		flex-shrink: 0;
	}

	h1 {
		flex-shrink: 0;
		margin: 0;
	}

	label {
		margin-left: auto;
		white-space: nowrap;
	}

	time, em {
		display: block;
	}

	em {
		color: #888;
		font-style: italic;
	}

	.map-container {
		flex: 1;
		min-height: 12rem;
		position: relative;
	}

	#map {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		background: #d4e4f4;
	}

	svg {
		position: absolute;
		top: 0;
		left: 0;
		z-index: 1;
		width: 100%;
		height: 100%;
		pointer-events: none;
	}

	circle, .legend > div {
		--color-departures: steelblue;
		--color-arrivals: darkorange;
		--color: color-mix(
			in oklch,
			var(--color-departures) calc(100% * var(--departure-ratio)),
			var(--color-arrivals)
		);
	}

	.map-container svg circle {
		pointer-events: auto;
		fill: var(--color);
		fill-opacity: 0.6;
		stroke: white;
		stroke-width: 1;
		transition: opacity 0.2s ease;
		cursor: pointer;
	}

	.map-container svg:has(circle.selected) circle:not(.selected) {
		opacity: 0.3;
	}

	.map-container svg path {
		pointer-events: auto;
	}

	.legend {
		display: flex;
		gap: 1px;
		margin-block: 0.75em;
	}

	.legend > div {
		flex: 1;
		padding: 0.4em 1.5em;
		background: var(--color);
		color: white;
		font-size: 0.85rem;
	}

	.legend > div:first-child {
		text-align: left;
	}

	.legend > div:nth-child(2) {
		text-align: center;
	}

	.legend > div:last-child {
		text-align: right;
	}
</style>
