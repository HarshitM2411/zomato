"""Format restaurant recommendations for terminal and web output."""

import html

from src.ui import render_recommendations_list, render_unavailable_recommendations

EMPTY_MESSAGE = (
    "No recommendations could be generated. Try broadening your preferences."
)
DIVIDER = "-" * 60


def display_recommendations(recommendations: list[dict]) -> None:
    """Print recommendations to the terminal in a readable layout."""
    if not recommendations:
        print(EMPTY_MESSAGE)
        return

    for item in recommendations:
        rank = item.get("rank", "?")
        name = item.get("name", "Unknown")
        cuisine = item.get("cuisine", "N/A")
        rating = item.get("rating", "N/A")
        cost = item.get("cost_for_two", "N/A")
        explanation = item.get("explanation", "")

        print(f"\n#{rank}  {name}")
        print(DIVIDER)
        print(f"  Cuisine   : {cuisine}")
        print(f"  Rating    : {rating} / 5")
        print(f"  Cost/Two  : Rs. {cost}")
        print(f"\n  Why this? : {explanation}")


def format_recommendations_html(
    recommendations: list[dict],
    candidate_count: int | None = None,
) -> str:
    """Render recommendations as HTML (Stitch design)."""
    if not recommendations:
        return render_unavailable_recommendations(EMPTY_MESSAGE)

    count = candidate_count if candidate_count is not None else len(recommendations)
    from src.ui import render_status_banner

    return render_status_banner(count, len(recommendations)) + render_recommendations_list(
        recommendations
    )


def format_legacy_cards(recommendations: list[dict]) -> str:
    """Simple card HTML fallback."""
    if not recommendations:
        return f'<p class="empty-message">{html.escape(EMPTY_MESSAGE)}</p>'

    cards = []
    for item in recommendations:
        rank = html.escape(str(item.get("rank", "?")))
        name = html.escape(str(item.get("name", "Unknown")))
        cuisine = html.escape(str(item.get("cuisine", "N/A")))
        rating = html.escape(str(item.get("rating", "N/A")))
        cost = html.escape(str(item.get("cost_for_two", "N/A")))
        explanation = html.escape(str(item.get("explanation", "")))

        cards.append(
            f"""
            <article class="card">
              <header>
                <span class="rank">#{rank}</span>
                <h3>{name}</h3>
              </header>
              <dl>
                <div><dt>Cuisine</dt><dd>{cuisine}</dd></div>
                <div><dt>Rating</dt><dd>{rating} / 5</dd></div>
                <div><dt>Cost for two</dt><dd>Rs. {cost}</dd></div>
              </dl>
              <p class="explanation"><strong>Why this?</strong> {explanation}</p>
            </article>
            """
        )

    return "\n".join(cards)
