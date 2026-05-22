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
from src.ui import (
    render_generic_error,
    render_no_results,
    render_unavailable_recommendations,
    render_validation_error,
)

load_dotenv()

app = Flask(__name__)
_dataset = None


def get_dataset():
    """Load and cache the Zomato dataset."""
    global _dataset
    if _dataset is None:
        _dataset = load_zomato_dataset()
    return _dataset


def _render(form, alert_html=None, results_html=None):
    return render_template(
        "index.html",
        form=form,
        alert_html=alert_html,
        results_html=results_html,
    )


@app.route("/", methods=["GET"])
def index():
    return _render(
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
        return _render(
            form=form,
            alert_html=render_validation_error(),
        )

    if budget not in ("low", "medium", "high"):
        return _render(
            form=form,
            alert_html=render_validation_error("Budget must be low, medium, or high."),
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
            return _render(
                form=form,
                results_html=render_no_results(location, cuisine, NO_RESTAURANTS_MESSAGE),
            )

        recommendations = get_recommendations(prompt)

        if recommendations:
            results_html = format_recommendations_html(
                recommendations,
                candidate_count=len(candidates),
            )
        else:
            results_html = render_unavailable_recommendations(EMPTY_MESSAGE)

        return _render(form=form, results_html=results_html)

    except EnvironmentError as exc:
        return _render(
            form=form,
            results_html=render_generic_error(str(exc)),
        )
    except Exception as exc:
        return _render(
            form=form,
            results_html=render_generic_error(
                "We're having trouble connecting to our servers. This might be a temporary issue."
            ),
        )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, port=port)
