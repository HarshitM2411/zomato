"""Shared HTML UI components (Stitch design)."""

import html
from pathlib import Path

GALLERY_IMAGES = [
    "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=400&h=400&fit=crop",
    "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=400&h=400&fit=crop",
    "https://images.unsplash.com/photo-1559339352-11d035aa65de?w=400&h=400&fit=crop",
    "https://images.unsplash.com/photo-1550966841-190eda8ff6e8?w=400&h=400&fit=crop",
]

CARD_IMAGES = [
    "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=560&h=400&fit=crop",
    "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=560&h=400&fit=crop",
    "https://images.unsplash.com/photo-1559339352-11d035aa65de?w=560&h=400&fit=crop",
    "https://images.unsplash.com/photo-1466978913421-dad2ebd01d4b?w=560&h=400&fit=crop",
    "https://images.unsplash.com/photo-1550966841-190eda8ff6e8?w=560&h=400&fit=crop",
]

UNAVAILABLE_IMAGE = (
    "https://images.unsplash.com/photo-1550966841-190eda8ff6e8?w=400&h=300&fit=crop"
)


def load_css() -> str:
    """Read app.css for injection into Streamlit."""
    css_path = Path(__file__).resolve().parent.parent / "static" / "app.css"
    return css_path.read_text(encoding="utf-8")


def render_header(active: str = "discover") -> str:
    discover_cls = "active" if active == "discover" else ""
    return f"""
    <header class="site-header">
      <a class="brand" href="/">
        <span class="brand-icon">🍴</span>
        Restaurant Recommender
      </a>
      <nav class="nav-links">
        <a class="{discover_cls}" href="/">Discover</a>
        <a href="#">Saved</a>
      </nav>
      <div class="nav-icons">
        <span aria-hidden="true">🔔</span>
        <span class="nav-avatar" aria-hidden="true"></span>
      </div>
    </header>
    """


def render_hero() -> str:
    return """
    <section class="hero">
      <h1>Discover Your Next Favorite Meal</h1>
      <p>Get AI-ranked recommendations from the Zomato dataset based on your preferences.</p>
    </section>
    """


def render_gallery() -> str:
    imgs = "".join(
        f'<img src="{html.escape(url)}" alt="Restaurant dining" loading="lazy" />'
        for url in GALLERY_IMAGES
    )
    return f'<div class="gallery">{imgs}</div>'


def render_footer() -> str:
    return """
    <footer class="site-footer">
      <div>
        <span class="footer-brand">Restaurant Recommender</span>
        <span> · Powered by Zomato data &amp; Groq AI</span>
      </div>
      <div class="footer-links">
        <a href="#">Privacy Policy</a>
        <a href="#">Terms of Service</a>
        <a href="#">Contact Support</a>
      </div>
      <div>© 2024 Restaurant Recommender</div>
    </footer>
    """


def render_status_banner(candidate_count: int, recommendation_count: int) -> str:
    return f"""
    <div class="status-banner">
      <span class="check">✓</span>
      <span>Found {candidate_count} candidates; showing {recommendation_count} recommendations.</span>
    </div>
    """


def render_results_header() -> str:
    return """
    <div class="results-header">
      <h2>Recommendations</h2>
      <span class="badge-ai">✨ AI Personalized</span>
    </div>
    """


def render_recommendation_card(item: dict, index: int = 0) -> str:
    rank = html.escape(str(item.get("rank", index + 1)))
    name = html.escape(str(item.get("name", "Unknown")))
    cuisine = html.escape(str(item.get("cuisine", "N/A")))
    rating = html.escape(str(item.get("rating", "N/A")))
    cost = html.escape(str(item.get("cost_for_two", "N/A")))
    explanation = html.escape(str(item.get("explanation", "")))
    img_url = CARD_IMAGES[index % len(CARD_IMAGES)]

    return f"""
    <article class="rec-card">
      <div class="rec-image">
        <span class="rank-badge">#{rank}</span>
        <img src="{img_url}" alt="{name}" loading="lazy" />
      </div>
      <div class="rec-body">
        <div class="rec-title-row">
          <h3>{name}</h3>
          <span title="Save (demo)">🔖</span>
        </div>
        <div class="rec-meta">
          <span>🍴 {cuisine}</span>
          <span>⭐ {rating}/5</span>
          <span>₹{cost} for two</span>
        </div>
        <div class="why-box">
          <strong>✨ Why this?</strong>
          <p>{explanation}</p>
        </div>
        <div class="rec-actions">
          <button type="button" class="btn-primary" style="width:auto">View Menu</button>
          <button type="button" class="btn-outline">Book Table</button>
        </div>
      </div>
    </article>
    """


def render_recommendations_list(recommendations: list[dict]) -> str:
    cards = "".join(
        render_recommendation_card(item, i) for i, item in enumerate(recommendations)
    )
    refine = """
    <p class="refine-link">
      <a href="#">🔍 Refine your preferences for better results</a>
    </p>
    """
    return render_results_header() + cards + refine


def render_validation_error(message: str = "Location is required.") -> str:
    msg = html.escape(message)
    return f"""
    <div class="alert-panel error">
      <div class="alert-icon">📍</div>
      <div class="alert-content">
        <h4 class="alert-title">Validation Error</h4>
        <p>{msg} Please enter a city or area to find the best dining spots near you.</p>
      </div>
      <a class="alert-retry" href="#">Retry</a>
    </div>
    """


def render_no_results(
    location: str = "",
    cuisine: str = "",
    message: str | None = None,
) -> str:
    search_parts = [p for p in (cuisine, location) if p]
    search_term = " ".join(search_parts) if search_parts else "your criteria"
    if message:
        desc = html.escape(message)
    else:
        desc = (
            f"We couldn't find any results for '{html.escape(search_term)}'. "
            "Try widening your search or removing some filters."
        )
    return f"""
    <div class="empty-card">
      <div class="empty-icon">🔍</div>
      <h3>No restaurants found matching your criteria</h3>
      <p>{desc}</p>
      <div class="empty-actions">
        <a href="/" class="btn-primary" style="text-decoration:none;display:inline-block;width:auto;padding:0.65rem 1.25rem">Clear all filters</a>
        <a href="/" class="btn-outline" style="text-decoration:none;display:inline-block">Edit Search</a>
      </div>
    </div>
    """


def render_unavailable_recommendations(message: str) -> str:
    msg = html.escape(message)
    return f"""
    <div class="unavailable-card">
      <img src="{UNAVAILABLE_IMAGE}" alt="Restaurant" loading="lazy" />
      <div class="unavailable-body">
        <div class="unavailable-label">✨ AI INSIGHTS UNAVAILABLE</div>
        <h3>No recommendations could be generated…</h3>
        <p>{msg}</p>
        <a href="/">See nearby popular spots →</a>
      </div>
    </div>
    """


def render_generic_error(message: str) -> str:
    msg = html.escape(message)
    return f"""
    <div class="error-card">
      <div class="error-icon">☁️</div>
      <h3>Something went wrong…</h3>
      <p>{msg}</p>
      <a href="/" class="btn-primary" style="text-decoration:none;display:inline-block;width:auto;padding:0.65rem 1.5rem">↻ Try again</a>
      <p style="margin-top:1rem"><a href="#" style="color:var(--text-muted)">Contact Support</a></p>
    </div>
    """


def wrap_page(content: str, active: str = "discover") -> str:
    """Full page shell for Flask."""
    return (
        render_header(active)
        + render_hero()
        + content
        + render_gallery()
        + render_footer()
    )
