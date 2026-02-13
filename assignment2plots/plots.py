import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("mapc_region_towns_w_population.csv")


'''pop_cols = ["pop1990", "pop2000", "pop2010", "pop2020"]
name_col = "namelsad20" if "namelsad20" in df.columns else "town20"

long = df[[name_col] + pop_cols].melt(
    id_vars=[name_col],
    value_vars=pop_cols,
    var_name="year",
    value_name="population"
)
long["year"] = long["year"].str.extract(r"(\d{4})").astype(int)
long = long.sort_values(["year", name_col])

plt.figure(figsize=(12, 7))
for place, g in long.groupby(name_col):
    plt.plot(g["year"], g["population"], linewidth=1, alpha=0.6)

plt.yscale("log")
plt.title("Population by municipality (1990–2020) — log scale")
plt.xlabel("Year")
plt.ylabel("Population (log scale)")
plt.xticks(sorted(long["year"].unique()))
plt.tight_layout()
plt.show()'''
'''pop_cols = ["pop1990", "pop2000", "pop2010", "pop2020"]
county_col = "county20"

# Sum population by county (wide)
county_wide = df.groupby(county_col)[pop_cols].sum()

# Rename columns to just years for cleaner plotting
county_wide.columns = [int(c.replace("pop", "")) for c in county_wide.columns]

# ---- Plot A: grouped bars (one group per year, bars = counties) ----
ax = county_wide.T.plot(kind="bar", figsize=(11, 6))
ax.set_title("Total population by county — grouped bars")
ax.set_xlabel("Year")
ax.set_ylabel("Total population")
ax.legend(title="County", bbox_to_anchor=(1.02, 1), loc="upper left")
plt.tight_layout()
plt.show()

# ---- Plot B: stacked bars (each year totals; colored segments = counties) ----
ax = county_wide.T.plot(kind="bar", stacked=True, figsize=(11, 6))
ax.set_title("Total population by county — stacked bars")
ax.set_xlabel("Year")
ax.set_ylabel("Total population")
ax.legend(title="County", bbox_to_anchor=(1.02, 1), loc="upper left")
plt.tight_layout()
plt.show()

# ---- Plot C: total population across all counties (single bar per year) ----
overall = county_wide.sum(axis=0)  # sums counties -> total per year

plt.figure(figsize=(8, 5))
plt.bar(overall.index.astype(int), overall.values)
plt.title("Total population across all counties — bars")
plt.xlabel("Year")
plt.ylabel("Total population")
plt.xticks(overall.index.astype(int))
plt.tight_layout()
plt.show()'''

'''import json
import pandas as pd
import matplotlib.pyplot as plt

from shapely.geometry import shape
from shapely.ops import transform
from pyproj import Transformer

# -----------------------
# 1) Load data
# -----------------------
geo_path = "mapping_inequality_redlining.geojson"
towns_path = "mapc_region_towns_w_population.csv"

with open(geo_path, "r") as f:
    gj = json.load(f)

towns = pd.read_csv(towns_path)

# -----------------------
# 2) Helper: normalize city/town names so we can join to population
# -----------------------
def clean_place_name(x: str) -> str:
    if pd.isna(x):
        return ""
    x = str(x).strip().lower()
    # towns file uses "Malden city", "Hudson town", etc. -> strip suffix
    for suffix in [" city", " town", " township", " borough"]:
        if x.endswith(suffix):
            x = x[: -len(suffix)]
    return x.strip()

# Build population map from towns dataset (most recent = pop2020)
# Use namelsad20 (e.g. "Malden city") when available; else town20.
name_col = "namelsad20" if "namelsad20" in towns.columns else "town20"
towns["place_clean"] = towns[name_col].apply(clean_place_name)
pop_map = towns.set_index("place_clean")["pop2020"].to_dict()

# -----------------------
# 3) Compute area for each GeoJSON feature (km^2) and collect props
# -----------------------
# Project from lon/lat (EPSG:4326) -> MA Mainland meters (EPSG:26986)
transformer = Transformer.from_crs("EPSG:4326", "EPSG:26986", always_xy=True)
project = lambda geom: transform(transformer.transform, geom)

rows = []
for feat in gj["features"]:
    props = feat.get("properties", {})
    city = props.get("city", None)
    grade = props.get("grade", None)

    if city is None or grade is None:
        continue
    if grade not in ["A", "B", "C", "D"]:
        continue

    geom = shape(feat["geometry"])
    geom_m = project(geom)
    area_km2 = geom_m.area / 1e6  # m^2 -> km^2

    rows.append({
        "city": city,
        "city_clean": clean_place_name(city),
        "grade": grade,
        "area_km2": area_km2
    })

red = pd.DataFrame(rows)

# Attach 2020 population (may be missing for some cities if names don't match)
red["pop2020"] = red["city_clean"].map(pop_map)

# -----------------------
# 4) Aggregate: total area by city and grade
# -----------------------
area_by_city_grade = (
    red.groupby(["city", "grade"], as_index=False)["area_km2"].sum()
)

pivot_area = area_by_city_grade.pivot(index="city", columns="grade", values="area_km2").fillna(0)

# Optional: limit to top N cities by total redlined area so plot is readable
TOP_N = 20
pivot_area = pivot_area.loc[pivot_area.sum(axis=1).sort_values(ascending=False).head(TOP_N).index]

# -----------------------
# 5) Plot 1: Total area by grade (stacked bars)
# -----------------------
ax = pivot_area[["A", "B", "C", "D"]].plot(kind="bar", stacked=True, figsize=(12, 6))
ax.set_title(f"Total redlined area by grade (km²) — top {TOP_N} cities")
ax.set_xlabel("City")
ax.set_ylabel("Area (km²)")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.show()

# -----------------------
# 6) Plot 2: Area scaled by most recent population (area per 100k residents)
# -----------------------
# Get population for these plotted cities
pop_for_city = pd.Series({c: pop_map.get(clean_place_name(c), None) for c in pivot_area.index})
pivot_area_per100k = pivot_area.div(pop_for_city, axis=0) * 100_000

# Drop cities we couldn't match to population
pivot_area_per100k = pivot_area_per100k.dropna()

ax = pivot_area_per100k[["A", "B", "C", "D"]].plot(kind="bar", stacked=True, figsize=(12, 6))
ax.set_title(f"Redlined area by grade per 100k residents — top {len(pivot_area_per100k)} cities matched")
ax.set_xlabel("City")
ax.set_ylabel("Area (km²) per 100k residents")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.show()'''


import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from shapely.geometry import shape
from shapely.ops import transform
from pyproj import Transformer

towns_path = "mapc_region_towns_w_population.csv"
geo_path = "mapping_inequality_redlining.geojson"

towns = pd.read_csv(towns_path)
name_col = "namelsad20" if "namelsad20" in towns.columns else "town20"

def clean_place_name(x) -> str:
    if pd.isna(x):
        return ""
    x = str(x).strip().lower()
    for suffix in [" city", " town", " township", " borough"]:
        if x.endswith(suffix):
            x = x[: -len(suffix)]
    return x.strip()

towns["city_clean"] = towns[name_col].apply(clean_place_name)

with open(geo_path, "r") as f:
    gj = json.load(f)

transformer = Transformer.from_crs("EPSG:4326", "EPSG:26986", always_xy=True)
project = lambda geom: transform(transformer.transform, geom)

rows = []
for feat in gj["features"]:
    props = feat.get("properties", {})
    city = props.get("city", None)
    grade = props.get("grade", None)
    if city is None or grade not in ["A", "B", "C", "D"]:
        continue
    geom = shape(feat["geometry"])
    area_km2 = project(geom).area / 1e6
    rows.append({"city_clean": clean_place_name(city), "grade": grade, "area_km2": area_km2})

red = pd.DataFrame(rows)

pivot = red.groupby(["city_clean", "grade"])["area_km2"].sum().unstack(fill_value=0)
for g in ["A", "B", "C", "D"]:
    if g not in pivot.columns:
        pivot[g] = 0.0
pivot = pivot[["A", "B", "C", "D"]]
pivot["total_km2"] = pivot.sum(axis=1)

pivot["pct_D"] = np.where(pivot["total_km2"] > 0, pivot["D"] / pivot["total_km2"] * 100, np.nan)
pivot["pct_CD"] = np.where(pivot["total_km2"] > 0, (pivot["C"] + pivot["D"]) / pivot["total_km2"] * 100, np.nan)

m = towns.merge(pivot.reset_index()[["city_clean", "pct_D", "pct_CD"]], on="city_clean", how="inner")
m = m.dropna(subset=["pop2020", "pct_D", "pct_CD"]).copy()

# Use log(pop) because pop is highly skewed
m["log_pop2020"] = np.log10(m["pop2020"])

corr_D = np.corrcoef(m["log_pop2020"], m["pct_D"])[0, 1]
corr_CD = np.corrcoef(m["log_pop2020"], m["pct_CD"])[0, 1]

# Plot 1
plt.figure(figsize=(8, 5))
plt.scatter(m["log_pop2020"], m["pct_D"])
plt.title(f"log10(pop2020) vs %D area (corr = {corr_D:.2f})")
plt.xlabel("log10(Population 2020)")
plt.ylabel("% of graded area that is D")
plt.tight_layout()
plt.show()

# Plot 2
plt.figure(figsize=(8, 5))
plt.scatter(m["log_pop2020"], m["pct_CD"])
plt.title(f"log10(pop2020) vs %(C+D) area (corr = {corr_CD:.2f})")
plt.xlabel("log10(Population 2020)")
plt.ylabel("% of graded area that is C or D")
plt.tight_layout()
plt.show()

# Plot 3 (overlay)
plt.figure(figsize=(8, 5))
plt.scatter(m["log_pop2020"], m["pct_D"], label="%D")
plt.scatter(m["log_pop2020"], m["pct_CD"], label="%(C+D)")
plt.title("Population vs grade shares (log10 population)")
plt.xlabel("log10(Population 2020)")
plt.ylabel("Percent of graded area")
plt.legend()
plt.tight_layout()
plt.show()

corr_D, corr_CD, len(m)
