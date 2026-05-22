"""Data ingestion and cleaning for the Zomato restaurant dataset."""

import re

import pandas as pd
from datasets import load_dataset

DATASET_NAME = "ManikaSaini/zomato-restaurant-recommendation"

BUDGET_BANDS = {
    "low": (0, 300),
    "medium": (301, 700),
    "high": (701, float("inf")),
}

COLUMN_RENAMES = {
    "restaurant_name": "name",
    "city": "location",
    "locality": "location",
    "approx_cost_for_two_people": "cost",
    "approx_cost_for_two": "cost",
    "average_cost_for_two": "cost",
    "aggregate_rating": "rating",
    "rate": "rating",
}

CANONICAL_COLUMNS = ("name", "location", "cuisines", "cost", "rating", "votes")


def _normalize_column_names(columns: pd.Index) -> list[str]:
    """Lowercase column names and replace non-alphanumeric characters with underscores."""
    normalized = []
    for col in columns:
        name = str(col).lower().strip()
        name = re.sub(r"[^\w]+", "_", name)
        name = re.sub(r"_+", "_", name).strip("_")
        normalized.append(name)
    return normalized


def _coerce_cost(series: pd.Series) -> pd.Series:
    """Strip commas and non-numeric characters, returning float values."""

    def parse(value) -> float:
        if pd.isna(value):
            return float("nan")
        text = str(value).replace(",", "").strip()
        match = re.search(r"[\d.]+", text)
        return float(match.group()) if match else float("nan")

    return series.apply(parse).astype("float64")


def _coerce_rating(series: pd.Series) -> pd.Series:
    """Extract numeric rating from values like '4.1/5' or 'NEW'."""

    def parse(value) -> float:
        if pd.isna(value):
            return float("nan")
        text = str(value).strip()
        if "/" in text:
            text = text.split("/", 1)[0]
        match = re.search(r"[\d.]+", text)
        return float(match.group()) if match else float("nan")

    return series.apply(parse).astype("float64")


def load_zomato_dataset() -> pd.DataFrame:
    """Load the Zomato dataset from HuggingFace and return a cleaned DataFrame."""
    dataset = load_dataset(DATASET_NAME)
    df = dataset["train"].to_pandas()

    df.columns = _normalize_column_names(df.columns)
    df = df.rename(
        columns={src: dst for src, dst in COLUMN_RENAMES.items() if src in df.columns}
    )

    if "cost" in df.columns:
        df["cost"] = _coerce_cost(df["cost"])
    if "rating" in df.columns:
        df["rating"] = _coerce_rating(df["rating"])
    if "votes" in df.columns:
        df["votes"] = pd.to_numeric(df["votes"], errors="coerce")

    df = df.dropna(subset=["name", "location"])
    df = df[df["name"].astype(str).str.strip() != ""]
    df = df[df["location"].astype(str).str.strip() != ""]

    return df.reset_index(drop=True)


if __name__ == "__main__":
    frame = load_zomato_dataset()
    print("Columns:", frame.columns.tolist())
    print(frame[list(CANONICAL_COLUMNS)].head(5))
    print("cost dtype:", frame["cost"].dtype)
    print("rating dtype:", frame["rating"].dtype)
    print("row count:", len(frame))
