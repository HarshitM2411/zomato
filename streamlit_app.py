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
    load_css,
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


def inject_styles() -> None:
    st.markdown(f"<style>{load_css()}</style>", unsafe_allow_html=True)
    st.markdown(
        """
        <style>
        header[data-testid="stHeader"] { background: transparent; }
        .stApp > header { display: none; }
        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }
        .block-container { padding-top: 1rem; max-width: 960px; }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner="Loading restaurant dataset…")
def get_dataset():
    """Load and cache the Zomato dataset."""
    return load_zomato_dataset()


def run_pipeline(
    location: str,
    budget: str,
    cuisine: str,
    min_rating: float,
    extra_preferences: str,
) -> tuple[str | None, int, int]:
    """Execute pipeline; return (error_html, candidate_count, recommendation_count)."""
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
            return (
                render_no_results(location, cuisine, NO_RESTAURANTS_MESSAGE),
                0,
                0,
            )

    with st.spinner("Getting AI recommendations from Groq…"):
        recommendations = get_recommendations(prompt)

    if recommendations:
        html = render_status_banner(len(candidates), len(recommendations))
        html += render_recommendations_list(recommendations)
        return html, len(candidates), len(recommendations)

    return render_unavailable_recommendations(EMPTY_MESSAGE), len(candidates), 0


def main() -> None:
    load_secrets()

    st.set_page_config(
        page_title="Restaurant Recommender",
        page_icon="🍽️",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    inject_styles()

    st.markdown(
        '<div class="app-shell">',
        unsafe_allow_html=True,
    )
    st.markdown(render_header(), unsafe_allow_html=True)
    st.markdown(render_hero(), unsafe_allow_html=True)

    if "results_html" not in st.session_state:
        st.session_state.results_html = None
    if "alert_html" not in st.session_state:
        st.session_state.alert_html = None

    with st.form("preferences", border=False):
        st.markdown('<div class="form-card" style="box-shadow:none;padding:0">', unsafe_allow_html=True)
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
        submitted = st.form_submit_button("✨ Get Recommendations", type="primary", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if submitted:
        location = (location or "").strip()
        cuisine = (cuisine or "").strip()
        extra_preferences = (extra_preferences or "").strip()
        st.session_state.alert_html = None
        st.session_state.results_html = None

        if not location:
            st.session_state.alert_html = render_validation_error()
        else:
            try:
                results_html, _, _ = run_pipeline(
                    location=location,
                    budget=budget,
                    cuisine=cuisine,
                    min_rating=min_rating,
                    extra_preferences=extra_preferences,
                )
                st.session_state.results_html = results_html
            except EnvironmentError as exc:
                st.session_state.results_html = render_generic_error(str(exc))
            except Exception:
                st.session_state.results_html = render_generic_error(
                    "We're having trouble connecting to our servers. "
                    "This might be a temporary issue."
                )

        st.rerun()

    if st.session_state.alert_html:
        st.markdown(st.session_state.alert_html, unsafe_allow_html=True)

    if st.session_state.results_html:
        st.markdown(
            f'<section class="results-section">{st.session_state.results_html}</section>',
            unsafe_allow_html=True,
        )

    st.markdown(render_gallery(), unsafe_allow_html=True)
    st.markdown(render_footer(), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


main()
