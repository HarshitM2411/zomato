"""Streamlit app for restaurant recommendations (deploy entrypoint)."""

import os

import streamlit as st
from dotenv import load_dotenv

from src.display import EMPTY_MESSAGE
from src.filter import filter_restaurants
from src.ingest import load_zomato_dataset
from src.llm_client import get_recommendations
from src.prompt_builder import NO_RESTAURANTS_MESSAGE, build_prompt

BUDGET_OPTIONS = ("low", "medium", "high")
BUDGET_LABELS = {
    "low": "Low (up to Rs. 300)",
    "medium": "Medium (Rs. 301–700)",
    "high": "High (above Rs. 700)",
}


def load_secrets() -> None:
    """Load Groq credentials from .env (local) or Streamlit secrets (cloud)."""
    load_dotenv()
    try:
        secrets = st.secrets
        if "GROQ_API_KEY" in secrets:
            os.environ["GROQ_API_KEY"] = secrets["GROQ_API_KEY"]
        if "GROQ_MODEL" in secrets:
            os.environ["GROQ_MODEL"] = secrets["GROQ_MODEL"]
        if "GROQ_BASE_URL" in secrets:
            os.environ["GROQ_BASE_URL"] = secrets["GROQ_BASE_URL"]
        if "HF_TOKEN" in secrets:
            os.environ["HF_TOKEN"] = secrets["HF_TOKEN"]
    except Exception:
        pass


@st.cache_data(show_spinner="Loading restaurant dataset…")
def get_dataset():
    """Load and cache the Zomato dataset."""
    return load_zomato_dataset()


def render_recommendations(recommendations: list[dict]) -> None:
    """Display recommendation cards in Streamlit."""
    if not recommendations:
        st.warning(EMPTY_MESSAGE)
        return

    for item in recommendations:
        rank = item.get("rank", "?")
        name = item.get("name", "Unknown")
        with st.container(border=True):
            st.subheader(f"#{rank}  {name}")
            col1, col2, col3 = st.columns(3)
            col1.metric("Cuisine", item.get("cuisine", "N/A"))
            col2.metric("Rating", f"{item.get('rating', 'N/A')} / 5")
            col3.metric("Cost for two", f"Rs. {item.get('cost_for_two', 'N/A')}")
            st.markdown(f"**Why this?** {item.get('explanation', '')}")


def run_pipeline(
    location: str,
    budget: str,
    cuisine: str,
    min_rating: float,
    extra_preferences: str,
) -> None:
    """Execute filter → prompt → LLM → display."""
    with st.spinner("Finding matching restaurants…"):
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
            st.info(NO_RESTAURANTS_MESSAGE)
            return

    with st.spinner("Getting AI recommendations from Groq…"):
        recommendations = get_recommendations(prompt)

    if recommendations:
        st.success(
            f"Found {len(candidates)} candidate(s); "
            f"showing {len(recommendations)} recommendation(s)."
        )
        render_recommendations(recommendations)
    else:
        st.warning(EMPTY_MESSAGE)


def main() -> None:
    load_secrets()

    st.set_page_config(
        page_title="Restaurant Recommender",
        page_icon="🍽️",
        layout="wide",
    )

    st.title("Restaurant Recommender")
    st.caption(
        "Enter your preferences to get AI-ranked recommendations from the Zomato dataset."
    )

    with st.form("preferences"):
        location = st.text_input("Location *", placeholder="e.g. Bangalore")
        budget = st.selectbox(
            "Budget",
            options=BUDGET_OPTIONS,
            format_func=lambda b: BUDGET_LABELS[b],
            index=1,
        )
        cuisine = st.text_input(
            "Cuisine",
            placeholder="e.g. Italian (leave blank for any)",
        )
        min_rating = st.slider("Minimum rating", 0.0, 5.0, 3.5, 0.1)
        extra_preferences = st.text_area(
            "Extra preferences",
            placeholder="e.g. family-friendly, outdoor seating",
        )
        submitted = st.form_submit_button("Get Recommendations", type="primary")

    if submitted:
        location = location.strip()
        cuisine = cuisine.strip()
        extra_preferences = extra_preferences.strip()

        if not location:
            st.error("Location is required.")
            return

        try:
            run_pipeline(
                location=location,
                budget=budget,
                cuisine=cuisine,
                min_rating=min_rating,
                extra_preferences=extra_preferences,
            )
        except EnvironmentError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"Something went wrong: {exc}")


main()
