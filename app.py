"""Flask web app for local development (optional).

For Streamlit deployment, use: streamlit run streamlit_app.py
"""

import os

from dotenv import load_dotenv
from flask import Flask, render_template, request

from src.display import EMPTY_MESSAGE, format_recommendations_html
from src.filter import filter_restaurants
from src.ingest import load_zomato_dataset
from src.llm_client import get_recommendations
from src.prompt_builder import NO_RESTAURANTS_MESSAGE, build_prompt

load_dotenv()

app = Flask(__name__)
_dataset = None


def get_dataset():
    """Load and cache the Zomato dataset."""
    global _dataset
    if _dataset is None:
        _dataset = load_zomato_dataset()
    return _dataset


@app.route("/", methods=["GET"])
def index():
    return render_template(
        "index.html",
        results_html=None,
        error=None,
        status=None,
        form={
            "location": "",
            "budget": "medium",
            "cuisine": "",
            "min_rating": "3.5",
            "extra_preferences": "",
        },
    )


@app.route("/recommend", methods=["POST"])
def recommend():
    location = request.form.get("location", "").strip()
    budget = request.form.get("budget", "medium").strip().lower()
    cuisine = request.form.get("cuisine", "").strip()
    extra_preferences = request.form.get("extra_preferences", "").strip()

    try:
        min_rating = float(request.form.get("min_rating", "3.5"))
        min_rating = max(0.0, min(5.0, min_rating))
    except ValueError:
        min_rating = 3.5

    form = {
        "location": location,
        "budget": budget,
        "cuisine": cuisine,
        "min_rating": str(min_rating),
        "extra_preferences": extra_preferences,
    }

    if not location:
        return render_template(
            "index.html",
            results_html=None,
            error="Location is required.",
            status=None,
            form=form,
        )

    if budget not in ("low", "medium", "high"):
        return render_template(
            "index.html",
            results_html=None,
            error="Budget must be low, medium, or high.",
            status=None,
            form=form,
        )

    try:
        data = get_dataset()
        candidates = filter_restaurants(
            data,
            location=location,
            budget=budget,
            cuisine=cuisine,
            min_rating=min_rating,
            extra_preferences=extra_preferences,
        )

        prompt = build_prompt(
            candidates,
            location=location,
            budget=budget,
            cuisine=cuisine,
            min_rating=min_rating,
            extra_preferences=extra_preferences,
        )

        if prompt.strip() == NO_RESTAURANTS_MESSAGE:
            return render_template(
                "index.html",
                results_html=f'<p class="empty-message">{NO_RESTAURANTS_MESSAGE}</p>',
                error=None,
                status="No matching restaurants in dataset.",
                form=form,
            )

        recommendations = get_recommendations(prompt)
        results_html = format_recommendations_html(recommendations)
        status = (
            f"Found {len(candidates)} candidate(s); "
            f"showing {len(recommendations)} recommendation(s)."
            if recommendations
            else EMPTY_MESSAGE
        )

        return render_template(
            "index.html",
            results_html=results_html,
            error=None,
            status=status,
            form=form,
        )

    except EnvironmentError as exc:
        return render_template(
            "index.html",
            results_html=None,
            error=str(exc),
            status=None,
            form=form,
        )
    except Exception as exc:
        return render_template(
            "index.html",
            results_html=None,
            error=f"Something went wrong: {exc}",
            status=None,
            form=form,
        )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, port=port)
