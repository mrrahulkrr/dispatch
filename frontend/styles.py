# Shared styles and region helpers for the Dispatch frontend

REGION_META = {
    "US": {"name": "United States", "flag": "🇺🇸", "accent": "#4facfe"},
    "UK": {"name": "United Kingdom", "flag": "🇬🇧", "accent": "#e63946"},
    # Future regions
    "EU": {"name": "European Union", "flag": "🇪🇺", "accent": "#003399"},
    "CA": {"name": "Canada", "flag": "🇨🇦", "accent": "#ff0000"},
    "IN": {"name": "India", "flag": "🇮🇳", "accent": "#ff9933"},
}

# Bounding boxes for geolocation → country mapping (lat_min, lat_max, lng_min, lng_max)
COUNTRY_BOUNDS = {
    "US": (24.5, 49.5, -125.0, -66.5),
    "UK": (49.5, 61.0, -8.0, 2.0),
    "EU": (35.0, 72.0, -10.0, 45.0),
    "CA": (41.0, 83.5, -141.0, -52.0),
    "IN": (6.5, 37.5, 68.0, 97.5),
}

def get_region_options():
    """Return list of region labels for selectbox."""
    return [f"{meta['flag']} {meta['name']}" for code, meta in REGION_META.items()]

def get_region_code_from_label(label: str) -> str:
    """Convert '🇺🇸 United States' back to 'US'."""
    for code, meta in REGION_META.items():
        if meta["name"] in label:
            return code
    return "US"

def detect_country_from_coords(lat: float, lng: float) -> str:
    """Map lat/lng to a region code using bounding boxes."""
    # Check specific countries first (UK before EU since UK is within EU bounds)
    for code in ["UK", "IN", "CA", "US", "EU"]:
        bounds = COUNTRY_BOUNDS[code]
        if bounds[0] <= lat <= bounds[1] and bounds[2] <= lng <= bounds[3]:
            return code
    return "US"  # Default fallback

def get_main_css(accent_color: str = "#4facfe") -> str:
    """Return the main CSS with dynamic accent color."""
    return f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        
        .stApp {{
            background-color: #0e1117;
            color: #fafafa;
            font-family: 'Inter', sans-serif;
        }}
        .main-header {{
            font-family: 'Inter', sans-serif;
            font-weight: 800;
            font-size: 2.5rem;
            background: -webkit-linear-gradient({accent_color}, #00f2fe);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0px;
        }}
        .sub-header {{
            font-size: 1.1rem;
            color: #a0aab2;
            margin-bottom: 2rem;
        }}
        .card {{
            background-color: #1e2530;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 16px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            border: 1px solid #2d3748;
            transition: border-color 0.2s ease;
        }}
        .card:hover {{
            border-color: {accent_color}40;
        }}
        .card-title {{
            font-size: 1.15rem;
            font-weight: 700;
            color: #fafafa;
            margin-bottom: 8px;
        }}
        .impact-note {{
            background-color: #2b3a4a;
            border-left: 4px solid {accent_color};
            padding: 16px;
            border-radius: 0 8px 8px 0;
            margin-top: 12px;
            font-style: italic;
            line-height: 1.6;
        }}
        .feed-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            margin-right: 8px;
        }}
        .badge-new {{
            background-color: #e63946;
            color: white;
        }}
        .badge-clear {{
            background-color: #2d6a4f;
            color: white;
        }}
        .region-indicator {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 0.8rem;
            background-color: #1a1a2e;
            border: 1px solid #2d3748;
            margin-bottom: 8px;
        }}
        .source-tag {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.75rem;
            background-color: {accent_color}20;
            color: {accent_color};
            margin-right: 6px;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #1e2530 0%, #2b3a4a 100%);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            border: 1px solid #2d3748;
        }}
        .stat-number {{
            font-size: 2rem;
            font-weight: 800;
            color: {accent_color};
        }}
        .stat-label {{
            font-size: 0.85rem;
            color: #a0aab2;
            margin-top: 4px;
        }}
    </style>
    """

GEOLOCATION_JS = """
<div id="geo-status" style="color: #a0aab2; font-size: 0.8rem;"></div>
<script>
function detectLocation() {
    const statusEl = document.getElementById('geo-status');
    statusEl.textContent = '📍 Detecting...';
    
    if (!navigator.geolocation) {
        statusEl.textContent = '❌ Geolocation not supported';
        return;
    }
    
    navigator.geolocation.getCurrentPosition(
        (pos) => {
            const lat = pos.coords.latitude;
            const lng = pos.coords.longitude;
            statusEl.textContent = '✅ Location detected';
            
            // Send coordinates to Streamlit via query params
            const url = new URL(window.location);
            url.searchParams.set('detected_lat', lat.toFixed(4));
            url.searchParams.set('detected_lng', lng.toFixed(4));
            window.location.href = url.toString();
        },
        (err) => {
            statusEl.textContent = '❌ ' + err.message;
        },
        { timeout: 10000 }
    );
}
detectLocation();
</script>
"""
