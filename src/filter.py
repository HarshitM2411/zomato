"""Preference-based filtering for restaurant candidates."""

import pandas as pd

from src.ingest import BUDGET_BANDS

MAX_CANDIDATES = 10


def filter_restaurants(
    df: pd.DataFrame,
    location: str,
    budget: str,
    cuisine: str,
    min_rating: float,
    extra_preferences: str = "",
) -> pd.DataFrame:
    """Filter restaurants by user preferences and return up to MAX_CANDIDATES rows."""
    result = df.copy()

    if location:
        result = result[
            result["location"].str.contains(location, case=False, na=False)
        ]

    if cuisine and cuisine.strip():
        result = result[
            result["cuisines"].str.contains(cuisine, case=False, na=False)
        ]

    result = result[result["rating"] >= min_rating]

    if budget in BUDGET_BANDS:
        cost_min, cost_max = BUDGET_BANDS[budget]
        result = result[
            (result["cost"] >= cost_min) & (result["cost"] <= cost_max)
        ]

    result = result.sort_values(
        by=["rating", "votes"],
        ascending=[False, False],
        na_position="last",
    )

    return result.head(MAX_CANDIDATES).reset_index(drop=True)


if __name__ == "__main__":
    from src.ingest import load_zomato_dataset

    data = load_zomato_dataset()

    case1 = filter_restaurants(
        data,
        location="Bangalore",
        budget="medium",
        cuisine="Italian",
        min_rating=3.5,
        extra_preferences="",
    )
    print("Case 1 (Bangalore, medium, Italian, 3.5):", len(case1), "rows")
    assert len(case1) <= 10

    case2 = filter_restaurants(
        data,
        location="NonexistentCityXYZ",
        budget="medium",
        cuisine="Italian",
        min_rating=3.5,
        extra_preferences="",
    )
    print("Case 2 (non-existent location):", len(case2), "rows")
    assert case2.empty

    case3 = filter_restaurants(
        data,
        location="Bangalore",
        budget="medium",
        cuisine="",
        min_rating=3.5,
        extra_preferences="",
    )
    print("Case 3 (blank cuisine):", len(case3), "rows")
    assert len(case3) <= 10
    assert len(case3) >= len(case1)

    print("All verification cases passed.")
