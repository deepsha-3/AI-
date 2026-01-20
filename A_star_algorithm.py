import osmnx as ox
import networkx as nx
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import matplotlib.pyplot as plt
import folium
from colorama import Fore, Style, init as colorama_init

CITY = "Pokhara, Nepal"  # Change to "Waling, Nepal" if needed
geolocator = Nominatim(user_agent="route_finder")

def geocode(address):
    location = geolocator.geocode(address)
    if not location:
        raise ValueError(f"Location not found: {address}")
    return (location.latitude, location.longitude)

def get_osm_graph(city):
    print(f"Downloading road network for {city} (this may take a minute)...")
    G = ox.graph_from_place(city, network_type='drive')
    return G


def heuristic(u, v, G):
    # u, v are node IDs in the graph
    a = (G.nodes[u]['y'], G.nodes[u]['x'])
    b = (G.nodes[v]['y'], G.nodes[v]['x'])
    return geodesic(a, b).meters


def main():
    colorama_init(autoreset=True)
    print(Fore.CYAN + Style.BRIGHT + f"\n=== Master: Shortest Route Finder for {CITY} ===\n")
    print(Fore.YELLOW + "Enter source and destination addresses (or place names) in Pokhara, Waling, or Syangja.")
    print(Fore.LIGHTBLACK_EX + "(Examples: 'Pokhara Lakeside', 'Waling Bazar', 'Syangja Hospital')")
    src_addr = input(Fore.GREEN + "Source address: ")
    dst_addr = input(Fore.GREEN + "Destination address: ")
    print(Fore.CYAN + "\nGeocoding addresses...")

    def normalize_nepal_query(q: str) -> str:
        q = q.strip()
        return q if "nepal" in q.lower() else f"{q}, Nepal"

    # Use a bounding box to include Pokhara, Waling, Syangja
    # OSMnx graph_from_bbox expects bbox=(west, south, east, north)
    bbox = (83.750, 27.870, 83.950, 28.016)  # (west, south, east, north)
    print(Fore.CYAN + "Downloading road network for Pokhara, Waling, Syangja...")
    G = ox.graph_from_bbox(bbox=bbox, network_type='drive')
    src_point = geocode(normalize_nepal_query(src_addr))
    dst_point = geocode(normalize_nepal_query(dst_addr))
    src_node = ox.nearest_nodes(G, src_point[1], src_point[0])
    dst_node = ox.nearest_nodes(G, dst_point[1], dst_point[0])
    print(Fore.CYAN + "\nFinding shortest path using A* search algorithm...")
    path = nx.astar_path(G, src_node, dst_node, heuristic=lambda u, v: heuristic(u, v, G), weight='length')
    # Always get the first edge's length for MultiDiGraph
    def get_edge_length(u, v):
        edge_data = G.get_edge_data(u, v)
        if isinstance(edge_data, dict):
            # MultiDiGraph: dict of dicts, get the first key
            first_key = list(edge_data.keys())[0]
            return edge_data[first_key].get('length', 0)
        return 0
    total_dist = sum(get_edge_length(u, v) for u, v in zip(path[:-1], path[1:]))
    print(Fore.MAGENTA + Style.BRIGHT + f"\n{'='*40}\nShortest path found! Total distance: {total_dist/1000:.2f} km\n{'='*40}\n")
    # Step-by-step directions
    print(Fore.BLUE + Style.BRIGHT + "\nStep-by-step directions:")
    for i, (u, v) in enumerate(zip(path[:-1], path[1:]), 1):
        edge_data = G.get_edge_data(u, v)
        if isinstance(edge_data, dict):
            first_key = list(edge_data.keys())[0]
            edge = edge_data[first_key]
        else:
            edge = {}
        street = edge.get('name', 'Unnamed Road')
        length = edge.get('length', 0)
        turn = ''
        if i > 1:
            prev = G.nodes[path[i-1]]
            curr = G.nodes[u]
            next_ = G.nodes[v]
            import math
            def bearing(a, b):
                lat1, lon1 = math.radians(a['y']), math.radians(a['x'])
                lat2, lon2 = math.radians(b['y']), math.radians(b['x'])
                dlon = lon2 - lon1
                x = math.sin(dlon) * math.cos(lat2)
                y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
                brng = math.atan2(x, y)
                return (math.degrees(brng) + 360) % 360
            prev_bearing = bearing(prev, curr)
            next_bearing = bearing(curr, next_)
            diff = (next_bearing - prev_bearing + 360) % 360
            if diff < 45 or diff > 315:
                turn = Fore.GREEN + "Go straight"
            elif diff < 135:
                turn = Fore.YELLOW + "Turn right"
            elif diff < 225:
                turn = Fore.RED + "Turn back"
            else:
                turn = Fore.CYAN + "Turn left"
        else:
            turn = Fore.GREEN + "Start"
        print(f"{Fore.LIGHTWHITE_EX}Step {i}: {turn} on {Fore.LIGHTMAGENTA_EX}{street}{Fore.LIGHTWHITE_EX} for {Fore.LIGHTYELLOW_EX}{length:.0f} meters")

    print(Fore.CYAN + Style.BRIGHT + f"\n{'-'*40}\nRoute coordinates (for robot navigation):")
    coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in path]
    for lat, lon in coords:
        print(Fore.LIGHTBLACK_EX + f"({lat:.6f}, {lon:.6f})")

    print(Fore.YELLOW + Style.BRIGHT + f"\n{'='*40}\nExplanation:")
    print(Fore.LIGHTWHITE_EX + "This route is calculated using the " + Fore.CYAN + "A* search algorithm" + Fore.LIGHTWHITE_EX + " on real road network data from " + Fore.GREEN + "OpenStreetMap" + Fore.LIGHTWHITE_EX + ".\n"
        "Each step shows the " + Fore.LIGHTMAGENTA_EX + "street name" + Fore.LIGHTWHITE_EX + " and approximate " + Fore.LIGHTYELLOW_EX + "turn direction" + Fore.LIGHTWHITE_EX + ". The robot or app can follow the coordinates in order.\n"
        + Fore.LIGHTCYAN_EX + "A* uses a cost function f(n) = g(n) + h(n), where g(n) is the distance so far and h(n) is the straight-line (heuristic) distance to the goal." + Fore.LIGHTWHITE_EX)

    # Enhanced Visualization with Folium
    print(Fore.LIGHTGREEN_EX + "\nRendering interactive web map with Folium...")
    import branca
    import json
    coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in path]
    mid_idx = len(coords) // 2
    # Use a modern tile style for a Google Maps-like look
    m = folium.Map(location=coords[mid_idx], zoom_start=12, tiles='CartoDB positron', control_scale=True, scrollWheelZoom=True)
    # Add all roads in light gray
    # OSMnx returns either a GeoDataFrame or (gdf_nodes, gdf_edges) depending on args
    gdfs = ox.graph_to_gdfs(G, nodes=False, edges=True)
    gdf_edges = gdfs[1] if isinstance(gdfs, tuple) else gdfs
    folium.GeoJson(gdf_edges.to_json(),
                   name='All Roads',
                   style_function=lambda x: {'color': '#cccccc', 'weight': 2, 'opacity': 0.5}).add_to(m)
    # Add the shortest path in green
    folium.PolyLine(coords, color='green', weight=8, opacity=0.9, tooltip='Shortest Path').add_to(m)

    # Add start and end markers (show entered place names)
    folium.Marker(
        coords[0],
        popup=f"Source: {src_addr}",
        tooltip=f"Source: {src_addr}",
        icon=folium.Icon(color='green', icon='play')
    ).add_to(m)
    folium.Marker(
        coords[-1],
        popup=f"Destination: {dst_addr}",
        tooltip=f"Destination: {dst_addr}",
        icon=folium.Icon(color='red', icon='flag')
    ).add_to(m)
    # Add step markers
    for i, (lat, lon) in enumerate(coords[1:-1], 1):
        folium.CircleMarker((lat, lon), radius=4, color='blue', fill=True, fill_opacity=0.7, popup=f'Step {i}').add_to(m)

    # -------------------------
    # Extra map context (rivers + important places)
    # -------------------------
    def _safe_to_geojson(obj) -> str | None:
        try:
            return obj.to_json()
        except Exception:
            try:
                return json.dumps(obj._geo_interface_)
            except Exception:
                return None

    def _features_from_bbox_compat(bbox_tuple, tags_dict):
        # bbox order: (west, south, east, north)
        if hasattr(ox, "features_from_bbox"):
            return ox.features_from_bbox(bbox_tuple, tags_dict)
        if hasattr(ox, "geometries_from_bbox"):
            west, south, east, north = bbox_tuple
            return ox.geometries_from_bbox(north, south, east, west, tags_dict)
        if hasattr(ox, "features") and hasattr(ox.features, "features_from_bbox"):
            return ox.features.features_from_bbox(bbox_tuple, tags_dict)
        raise RuntimeError("This OSMnx version does not support downloading features from bbox.")

    # Rivers / streams
    try:
        water_tags = {"waterway": ["river", "stream", "canal"]}
        gdf_water = _features_from_bbox_compat(bbox, water_tags)
        if hasattr(gdf_water, "empty") and not gdf_water.empty:
            water_geojson = _safe_to_geojson(gdf_water)
            if water_geojson:
                folium.GeoJson(
                    water_geojson,
                    name="Rivers & Streams",
                    style_function=lambda x: {"color": "#1e88e5", "weight": 3, "opacity": 0.8},
                ).add_to(m)
    except Exception:
        pass

    # Important named places (and anything with Chowk in the name)
    try:
        poi_tags = {
            "amenity": ["hospital", "school", "university", "bus_station", "marketplace"],
            "tourism": True,
            "place": True,
        }
        gdf_poi = _features_from_bbox_compat(bbox, poi_tags)
        if hasattr(gdf_poi, "empty") and not gdf_poi.empty:
            if "name" in getattr(gdf_poi, "columns", []):
                gdf_named = gdf_poi[gdf_poi["name"].notna()].copy()
            else:
                gdf_named = gdf_poi

            # Prefer Chowk-like names, then other named POIs.
            if "name" in getattr(gdf_named, "columns", []):
                name_series = gdf_named["name"].astype(str)
                gdf_chowk = gdf_named[name_series.str.contains("chowk", case=False, na=False)]
                gdf_other = gdf_named.drop(index=getattr(gdf_chowk, "index", []), errors="ignore")
                import pandas as pd
                gdf_named = pd.concat([gdf_chowk.head(25), gdf_other.head(25)], axis=0)
            else:
                gdf_named = gdf_named.head(30)

            poi_group = folium.FeatureGroup(name="Important Places", show=True)

            def _centroid_latlon(geom):
                try:
                    c = geom.centroid
                    return (c.y, c.x)
                except Exception:
                    return None

            for _, row in getattr(gdf_named, "iterrows", lambda: [])():
                geom = row.get("geometry", None)
                if geom is None:
                    continue
                pt = _centroid_latlon(geom)
                if not pt:
                    continue
                nm = row.get("name", "")
                nm = str(nm) if nm is not None else ""
                if not nm:
                    continue
                label = nm[:45] + ("…" if len(nm) > 45 else "")
                folium.Marker(
                    location=pt,
                    tooltip=label,
                    icon=folium.DivIcon(
                        html=(
                            '<div style="font-family:system-ui,Segoe UI,Arial; font-size:12px; '
                            'color:#111; background:rgba(255,255,255,0.85); padding:2px 6px; '
                            'border:1px solid rgba(0,0,0,0.25); border-radius:8px; '
                            'box-shadow:0 2px 6px rgba(0,0,0,0.2); white-space:nowrap;">'
                            + label
                            + "</div>"
                        )
                    ),
                ).add_to(poi_group)

            poi_group.add_to(m)
    except Exception:
        pass

    # -------------------------
    # HTML overlays (title + searched places + right-side distance panel)
    # -------------------------
    overlays_html = f"""
    <style>
      .master369-title {{
        position: fixed;
        top: 10px;
        left: 50%;
        transform: translateX(-50%);
        z-index: 9999;
        background: rgba(255,255,255,0.92);
        padding: 10px 26px;
        border-radius: 14px;
        border: 1px solid rgba(0,0,0,0.25);
        font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
        font-size: 22px;
        font-weight: 800;
        color: #111;
        box-shadow: 0 6px 18px rgba(0,0,0,0.18);
      }}
      .master369-subtitle {{
        position: fixed;
        top: 1.5in;
        left: 50%;
        transform: translateX(-50%);
        z-index: 9999;
        background: rgba(255,255,255,0.88);
        padding: 8px 18px;
        border-radius: 12px;
        border: 1px solid rgba(0,0,0,0.18);
        font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
        font-size: 14px;
        font-weight: 600;
        color: #222;
        box-shadow: 0 6px 16px rgba(0,0,0,0.14);
      }}
            .master369-searchpanel {{
                position: fixed;
                top: 110px;
                left: 16px;
                z-index: 9999;
                width: 320px;
                background: rgba(255,255,255,0.92);
                padding: 12px 14px;
                border-radius: 14px;
                border: 1px solid rgba(0,0,0,0.22);
                font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
                color: #111;
                box-shadow: 0 10px 22px rgba(0,0,0,0.18);
            }}
            .master369-searchpanel label {{
                display: block;
                font-size: 12px;
                font-weight: 800;
                color: #444;
                margin: 8px 0 4px;
                letter-spacing: 0.2px;
            }}
            .master369-searchpanel input {{
                width: 100%;
                box-sizing: border-box;
                padding: 10px 10px;
                border-radius: 10px;
                border: 1px solid rgba(0,0,0,0.25);
                font-size: 14px;
                outline: none;
            }}
            .master369-searchpanel .row {{
                display: flex;
                gap: 10px;
                margin-top: 10px;
            }}
            .master369-searchpanel button {{
                flex: 1;
                padding: 10px 10px;
                border-radius: 10px;
                border: 1px solid rgba(0,0,0,0.25);
                background: #111;
                color: #fff;
                font-weight: 800;
                cursor: pointer;
            }}
            .master369-searchpanel button.secondary {{
                background: #fff;
                color: #111;
            }}
            .master369-searchpanel .hint {{
                font-size: 12px;
                color: #555;
                margin-top: 10px;
                line-height: 1.35;
            }}
      .master369-sidepanel {{
        position: fixed;
        top: 110px;
        right: 16px;
        z-index: 9999;
        width: 260px;
        background: rgba(255,255,255,0.92);
        padding: 12px 14px;
        border-radius: 14px;
        border: 1px solid rgba(0,0,0,0.22);
        font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
        color: #111;
        box-shadow: 0 10px 22px rgba(0,0,0,0.18);
      }}
      .master369-sidepanel .k {{ font-size: 12px; color: #555; font-weight: 700; letter-spacing: 0.2px; }}
      .master369-sidepanel .v {{ font-size: 18px; font-weight: 800; margin-top: 4px; }}
      .master369-sidepanel .route {{ font-size: 12px; color: #333; margin-top: 8px; line-height: 1.35; }}
    </style>

    <div class="master369-title">Master</div>
        <div id="master369-subtitle" class="master369-subtitle">From: {src_addr} &nbsp;&nbsp;→&nbsp;&nbsp; To: {dst_addr}</div>

        <div class="master369-searchpanel">
            <label for="srcInput">SOURCE</label>
            <input id="srcInput" type="text" value="{src_addr}" placeholder="e.g., Waling Chowk" />
            <label for="dstInput">DESTINATION</label>
            <input id="dstInput" type="text" value="{dst_addr}" placeholder="e.g., Pokhara Lakeside" />
            <div class="row">
                <button type="button" onclick="updateHeader()">Update</button>
                <button class="secondary" type="button" onclick="openGoogleMaps()">Google Maps</button>
            </div>
            <div class="hint">
                Tip: Use these fields to type the place names you are searching for. To recalculate the shortest path, run the Python script again.
            </div>
        </div>

    <div class="master369-sidepanel">
      <div class="k">DISTANCE</div>
      <div class="v">{total_dist/1000:.2f} km</div>
      <div class="route"><b>Source:</b> {src_addr}<br/><b>Destination:</b> {dst_addr}</div>
    </div>

        <script>
            function esc(s) {{
                return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
            }}
            function updateHeader() {{
                var s = document.getElementById('srcInput').value;
                var d = document.getElementById('dstInput').value;
                document.getElementById('master369-subtitle').innerHTML = 'From: ' + esc(s) + ' &nbsp;&nbsp;→&nbsp;&nbsp; To: ' + esc(d);
            }}
            function openGoogleMaps() {{
                var s = document.getElementById('srcInput').value;
                var d = document.getElementById('dstInput').value;
                var url = 'https://www.google.com/maps/dir/?api=1&origin=' + encodeURIComponent(s) + '&destination=' + encodeURIComponent(d);
                window.open(url, '_blank');
            }}
        </script>
    """
    m.get_root().html.add_child(branca.element.Element(overlays_html))
    # Layer control for toggling
    folium.LayerControl().add_to(m)
    # Save map to HTML and inform user
    map_file = 'route_map.html'
    m.save(map_file)
    print(Fore.LIGHTCYAN_EX + f"\nInteractive map saved as {map_file}. Open it in your browser to explore the route in detail, including all streets and the highlighted shortest path.")

if __name__ == "__main__":
    main()