"""
Sample Project Generator for WebPulse Demo Mode.
Generates realistic static website projects with real analyzable issues:
- v1 (Before Optimization): Large images, missing alt/dimensions, render blocking script, broken asset ref.
- v2 (After Optimization): Optimized assets, deferred script, fixed assets, high performance score.
"""

import io
import zipfile
from PIL import Image, ImageDraw

def create_synthetic_image(width=1200, height=800, color=(56, 189, 248), text="WebPulse Sample Image"):
    img = Image.new('RGB', (width, height), color=color)
    draw = ImageDraw.Draw(img)
    # Draw geometric patterns to add realistic weight
    for i in range(0, width, 40):
        draw.line([(i, 0), (width - i, height)], fill=(30, 41, 59), width=2)
    buffer = io.BytesIO()
    # Save as uncompressed heavy PNG or JPEG
    img.save(buffer, format='PNG', optimize=False)
    return buffer.getvalue()

def create_sample_project_v1_zip() -> io.BytesIO:
    """Generates Version 1.0 (Unoptimized Static Project)"""
    zip_buffer = io.BytesIO()

    index_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Aura Modern Living — Sustainable Architecture</title>
    <!-- Issue 1: Blocking script in head without defer or async -->
    <script src="js/analytics-tracker.js"></script>
    <link rel="stylesheet" href="css/main.css">
    <!-- Issue 2: Broken stylesheet reference -->
    <link rel="stylesheet" href="css/missing-custom-theme.css">
    <!-- Issue 3: Duplicate stylesheet -->
    <link rel="stylesheet" href="css/main.css">
</head>
<body>
    <header class="navbar">
        <div class="logo">AURA ARCHITECTURE</div>
        <nav>
            <a href="index.html">Home</a>
            <a href="gallery.html">Portfolio</a>
            <a href="contact.html">Contact</a>
        </nav>
    </header>

    <main>
        <section class="hero">
            <h1>Sustainable Design For The Modern Era</h1>
            <p>Crafting eco-conscious residential and commercial architecture.</p>
            <!-- Issue 4: Heavy uncompressed image missing alt and explicit width/height (CLS Risk) -->
            <img src="images/hero-heavy.png" class="hero-img">
        </section>

        <section class="features">
            <div class="card">
                <!-- Issue 5: Missing alt attribute -->
                <img src="images/feature-solar.png">
                <h3>Solar Efficiency</h3>
                <p>Passive solar orientation maximizing natural heat retention.</p>
            </div>
            <div class="card">
                <img src="images/feature-timber.png" alt="Sustainably harvested timber beams">
                <h3>Mass Timber</h3>
                <p>Low carbon footprint utilizing locally sourced cross-laminated timber.</p>
            </div>
        </section>
    </main>

    <footer>
        <p>&copy; 2026 Aura Architecture Studio. All rights reserved.</p>
    </footer>

    <script src="js/app.js"></script>
</body>
</html>
"""

    gallery_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <!-- Issue 6: Missing viewport meta tag on this subpage -->
    <title>Project Gallery — Aura Studio</title>
    <link rel="stylesheet" href="css/main.css">
</head>
<body>
    <h1>Architecture Portfolio</h1>
    <p>Explore our recent award-winning sustainable pavilions.</p>
    <img src="images/feature-solar.png" alt="Solar pavilion canopy">
    <p><a href="index.html">Back to Home</a></p>
</body>
</html>
"""

    main_css = """/* Aura Modern Living Global Stylesheet */
@import "sub-theme.css"; /* Issue 7: CSS @import causing serial network request */

body {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    color: #333333;
    background-color: #f8fafc;
    line-height: 1.6;
}

.navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 2rem;
    background: #0f172a;
    color: #ffffff;
}

.navbar a {
    color: #94a3b8;
    text-decoration: none;
    margin-left: 1.5rem;
}

.hero {
    padding: 4rem 2rem;
    text-align: center;
    background: #ffffff;
    /* Issue 8: Broken background url asset reference */
    background-image: url('../images/missing-pattern-bg.png');
}

.hero-img {
    max-width: 100%;
    border-radius: 8px;
    margin-top: 2rem;
}

.features {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 2rem;
    padding: 3rem 2rem;
    max-width: 1200px;
    margin: 0 auto;
}

.card {
    background: #ffffff;
    padding: 1.5rem;
    border-radius: 8px;
    border: 1px solid #e2e8f0;
}

/* Issue 9: Duplicate CSS selector block */
.navbar {
    padding: 1rem 2rem;
    background: #0f172a;
}
"""

    sub_theme_css = """/* Sub-theme styles */
.hero h1 {
    font-size: 2.5rem;
    color: #0f172a;
}
"""

    app_js = """// Main Application Logic
document.addEventListener('DOMContentLoaded', () => {
    console.log("Aura App Initialized");
    console.log("Running in development mode...");
    
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', () => {
            card.style.transform = 'translateY(-4px)';
            card.style.transition = 'transform 0.2s ease';
        });
        card.addEventListener('mouseleave', () => {
            card.style.transform = 'translateY(0)';
        });
    });
});
"""

    tracker_js = """// Blocking Analytics Tracker
console.log("Tracker module loaded in head");
// Simulate lightweight sync operations
window.__aura_analytics = { active: true, session: Date.now() };
"""

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('index.html', index_html)
        zf.writestr('gallery.html', gallery_html)
        zf.writestr('css/main.css', main_css)
        zf.writestr('css/sub-theme.css', sub_theme_css)
        zf.writestr('js/app.js', app_js)
        zf.writestr('js/analytics-tracker.js', tracker_js)
        
        # Heavy uncompressed images
        zf.writestr('images/hero-heavy.png', create_synthetic_image(1600, 1000, (30, 41, 59)))
        zf.writestr('images/feature-solar.png', create_synthetic_image(600, 400, (16, 185, 129)))
        zf.writestr('images/feature-timber.png', create_synthetic_image(600, 400, (245, 158, 11)))

    zip_buffer.seek(0)
    return zip_buffer


def create_sample_project_v2_zip() -> io.BytesIO:
    """Generates Version 2.0 (Optimized Revision for Comparison)"""
    zip_buffer = io.BytesIO()

    index_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aura Modern Living — Sustainable Architecture</title>
    <!-- Optimized: Added defer attribute to script -->
    <script src="js/analytics-tracker.js" defer></script>
    <link rel="stylesheet" href="css/main.css">
</head>
<body>
    <header class="navbar">
        <div class="logo">AURA ARCHITECTURE</div>
        <nav>
            <a href="index.html">Home</a>
            <a href="gallery.html">Portfolio</a>
            <a href="contact.html">Contact</a>
        </nav>
    </header>

    <main>
        <section class="hero">
            <h1>Sustainable Design For The Modern Era</h1>
            <p>Crafting eco-conscious residential and commercial architecture.</p>
            <!-- Optimized: Explicit dimensions and descriptive alt text -->
            <img src="images/hero-optimized.png" width="1200" height="700" alt="Modern eco-residence with solar canopy" class="hero-img">
        </section>

        <section class="features">
            <div class="card">
                <!-- Optimized: Added width, height, and alt -->
                <img src="images/feature-solar.png" width="600" height="400" alt="Rooftop solar panel installation">
                <h3>Solar Efficiency</h3>
                <p>Passive solar orientation maximizing natural heat retention.</p>
            </div>
            <div class="card">
                <img src="images/feature-timber.png" width="600" height="400" alt="Sustainably harvested timber beams">
                <h3>Mass Timber</h3>
                <p>Low carbon footprint utilizing locally sourced cross-laminated timber.</p>
            </div>
        </section>
    </main>

    <footer>
        <p>&copy; 2026 Aura Architecture Studio. All rights reserved.</p>
    </footer>

    <script src="js/app.js" defer></script>
</body>
</html>
"""

    gallery_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Project Gallery — Aura Studio</title>
    <link rel="stylesheet" href="css/main.css">
</head>
<body>
    <h1>Architecture Portfolio</h1>
    <p>Explore our recent award-winning sustainable pavilions.</p>
    <img src="images/feature-solar.png" width="600" height="400" alt="Solar pavilion canopy">
    <p><a href="index.html">Back to Home</a></p>
</body>
</html>
"""

    main_css = """/* Aura Modern Living Optimized Stylesheet */
body {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    color: #333333;
    background-color: #f8fafc;
    line-height: 1.6;
}

.navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 2rem;
    background: #0f172a;
    color: #ffffff;
}

.navbar a {
    color: #94a3b8;
    text-decoration: none;
    margin-left: 1.5rem;
}

.hero {
    padding: 4rem 2rem;
    text-align: center;
    background: #ffffff;
}

.hero h1 {
    font-size: 2.5rem;
    color: #0f172a;
}

.hero-img {
    max-width: 100%;
    height: auto;
    border-radius: 8px;
    margin-top: 2rem;
}

.features {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 2rem;
    padding: 3rem 2rem;
    max-width: 1200px;
    margin: 0 auto;
}

.card {
    background: #ffffff;
    padding: 1.5rem;
    border-radius: 8px;
    border: 1px solid #e2e8f0;
}
.card img {
    max-width: 100%;
    height: auto;
    border-radius: 4px;
}
"""

    app_js = """// Main Application Logic
document.addEventListener('DOMContentLoaded', () => {
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', () => {
            card.style.transform = 'translateY(-4px)';
            card.style.transition = 'transform 0.2s ease';
        });
        card.addEventListener('mouseleave', () => {
            card.style.transform = 'translateY(0)';
        });
    });
});
"""

    tracker_js = """window.__aura_analytics = { active: true, session: Date.now() };"""

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('index.html', index_html)
        zf.writestr('gallery.html', gallery_html)
        zf.writestr('css/main.css', main_css)
        zf.writestr('js/app.js', app_js)
        zf.writestr('js/analytics-tracker.js', tracker_js)
        
        # Optimized resized images
        zf.writestr('images/hero-optimized.png', create_synthetic_image(1200, 700, (30, 41, 59)))
        zf.writestr('images/feature-solar.png', create_synthetic_image(600, 400, (16, 185, 129)))
        zf.writestr('images/feature-timber.png', create_synthetic_image(600, 400, (245, 158, 11)))

    zip_buffer.seek(0)
    return zip_buffer
