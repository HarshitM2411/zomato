"""Streamlit app for restaurant recommendations (deploy entrypoint)."""

import os

import streamlit as st
from dotenv import load_dotenv

from src.display import EMPTY_MESSAGE
from src.filter import filter_restaurants
from src.ingest import load_zomato_dataset
from src.llm_client import get_recommendations
from src.prompt_builder import NO_RESTAURANTS_MESSAGE, build_prompt
from src.ui import (
    display_st_html,
    estimate_html_height,
    render_footer,
    render_gallery,
    render_generic_error,
    render_header,
    render_hero,
    render_no_results,
    render_recommendations_list,
    render_status_banner,
    render_unavailable_recommendations,
    render_validation_error,
)

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


def inject_streamlit_chrome() -> None:
    """Hide default Streamlit chrome."""
    st.markdown(
        """
        <style>
        header[data-testid="stHeader"] { background: transparent; }
        .stApp > header { display: none; }
        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }
        .block-container { padding-top: 0.5rem; max-width: 960px; }
        iframe { border: none !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner="Loading restaurant dataset…")
def get_dataset():
    """Load and cache the Zomato dataset."""
    return load_zomato_dataset()


def build_results_html(recommendations: list[dict], candidate_count: int) -> str:
    """Build styled recommendations block."""
    return render_status_banner(candidate_count, len(recommendations)) + render_recommendations_list(
        recommendations
    )


def run_pipeline(
    location: str,
    budget: str,
    cuisine: str,
    min_rating: float,
    extra_preferences: str,
) -> tuple[str | None, int]:
    """Execute pipeline; return (results_html, recommendation_count)."""
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
            return render_no_results(location, cuisine, NO_RESTAURANTS_MESSAGE), 0

    with st.spinner("Getting AI recommendations from Groq…"):
        recommendations = get_recommendations(prompt)

    if recommendations:
        return build_results_html(recommendations, len(candidates)), len(recommendations)

    return render_unavailable_recommendations(EMPTY_MESSAGE), 0


def main() -> None:
    load_secrets()

    st.set_page_config(
        page_title="Restaurant Recommender",
        page_icon="🍽️",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    inject_streamlit_chrome()

    if "results_html" not in st.session_state:
        st.session_state.results_html = None
    if "alert_html" not in st.session_state:
        st.session_state.alert_html = None
    if "result_count" not in st.session_state:
        st.session_state.result_count = 0

    display_st_html(render_header(), height=72)
    display_st_html(render_hero(), height=140)

    if st.session_state.alert_html:
        display_st_html(st.session_state.alert_html, height=110)

    with st.form("preferences", border=False):
        location = st.text_input("Location *", placeholder="e.g. Bangalore")
        col1, col2 = st.columns(2)
        with col1:
            budget = st.selectbox(
                "Budget",
                options=BUDGET_OPTIONS,
                format_func=lambda b: BUDGET_LABELS[b],
                index=1,
            )
        with col2:
            cuisine = st.text_input(
                "Cuisine",
                placeholder="e.g. Italian (leave blank for any)",
            )
        min_rating = st.slider("Minimum Rating", 0.0, 5.0, 3.5, 0.1)
        st.caption("Scale: 0.0 · 2.5 · 5.0")
        extra_preferences = st.text_area(
            "Extra Preferences",
            placeholder="e.g. family-friendly, outdoor seating, pet-friendly, live music",
        )
        submitted = st.form_submit_button(
            "✨ Get Recommendations",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        location = (location or "").strip()
        cuisine = (cuisine or "").strip()
        extra_preferences = (extra_preferences or "").strip()
        st.session_state.alert_html = None
        st.session_state.results_html = None
        st.session_state.result_count = 0

        if not location:
            st.session_state.alert_html = render_validation_error()
        else:
            try:
                results_html, count = run_pipeline(
                    location=location,
                    budget=budget,
                    cuisine=cuisine,
                    min_rating=min_rating,
                    extra_preferences=extra_preferences,
                )
                st.session_state.results_html = results_html
                st.session_state.result_count = count
            except EnvironmentError as exc:
                st.session_state.results_html = render_generic_error(str(exc))
            except Exception:
                st.session_state.results_html = render_generic_error(
                    "We're having trouble connecting to our servers. "
                    "This might be a temporary issue."
                )

        st.rerun()

    if st.session_state.results_html:
        results_block = (
            f'<section class="results-section">{st.session_state.results_html}</section>'
        )
        display_st_html(
            results_block,
            height=estimate_html_height(
                results_block,
                card_count=st.session_state.result_count,
            ),
        )

    display_st_html(render_gallery(), height=220)
    display_st_html(render_footer(), height=90)


main()
