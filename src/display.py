"""Format restaurant recommendations for terminal and web output."""

import html

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


def format_recommendations_html(recommendations: list[dict]) -> str:
    """Render recommendations as HTML for the web frontend."""
    if not recommendations:
        return f'<p class="empty-message">{EMPTY_MESSAGE}</p>'

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


if __name__ == "__main__":
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    mock = [
        {
            "rank": 1,
            "name": "Truffles",
            "cuisine": "Italian",
            "rating": 4.5,
            "cost_for_two": 600,
            "explanation": "Excellent Italian with high ratings.",
        },
        {
            "rank": 2,
            "name": "Megha Upahar",
            "cuisine": "South Indian",
            "rating": 4.2,
            "cost_for_two": 450,
            "explanation": "Great value South Indian food.",
        },
        {
            "rank": 3,
            "name": "Pizza Hut",
            "cuisine": "Pizza",
            "rating": 3.8,
            "cost_for_two": 500,
            "explanation": "Reliable pizza option for groups.",
        },
    ]

    print("=== Populated list ===")
    display_recommendations(mock)

    print("\n=== Empty list ===")
    display_recommendations([])

    html = format_recommendations_html(mock)
    assert "Truffles" in html and "card" in html
    print("\nAll display verification checks passed.")
