import os
import gdown
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, callback

# Download CSV if not already present
if not os.path.exists("mtual_fund_data.csv"):
    gdown.download(
        "https://drive.google.com/uc?id=15kV9YfMGfjaEwiXyq1dQL1RSBLbCd1ro",
        "mutual_fund_data.csv",
        quiet=False
    )

# ── Data prep ────────────────────────────────────────────────────────────────

df = pd.read_csv("mutual_fund_data.csv")

def categorize(cat):
    cat = str(cat)
    if cat.startswith("Equity") or cat in ["Growth", "ELSS"]:
        return "Equity"
    elif cat.startswith("Debt") or cat in ["Income", "Liquid", "Gilt", "Money Market", "Assured Return"]:
        return "Debt"
    elif cat.startswith("Hybrid") or cat == "Balanced":
        return "Hybrid"
    elif cat.startswith("Other"):
        return "Other / Index & ETF"
    elif cat.startswith("Solution"):
        return "Solution Oriented"
    else:
        return "Uncategorized"

df["Broad_Category"] = df["Scheme_Category"].apply(categorize)
df["Launch_Date"] = pd.to_datetime(df["Launch_Date"], errors="coerce")
df["Launch_Year"] = df["Launch_Date"].dt.year
active = df[df["Average_AUM_Cr"].notna()].copy()

# ── KPI numbers ──────────────────────────────────────────────────────────────

total_funds = len(active)
total_amcs = active["AMC"].nunique()
total_aum = active["Average_AUM_Cr"].sum()

# ── Charts ────────────────────────────────────────────────────────────────────

# Chart 1 - AUM by AMC
amc_aum = (active.groupby("AMC")["Average_AUM_Cr"]
           .sum().reset_index()
           .sort_values("Average_AUM_Cr", ascending=False).head(15))
amc_aum["Average_AUM_Cr"] = amc_aum["Average_AUM_Cr"].round(0)

amc_aum["AMC"] = (amc_aum["AMC"]
    .str.replace(r"\bLimited\b", "Ltd.", regex=True)
    .str.replace(r"\bManagement\b", "Mgmt.", regex=True)
    .str.replace(r"\bCompany\b", "Co.", regex=True)
    .str.replace(r"\bPrivate\b", "Pvt.", regex=True)
)

fig1 = px.bar(amc_aum, x="Average_AUM_Cr", y="AMC", orientation="h",
              title="Top 15 AMCs by Total AUM (₹ Cr)",
              labels={"Average_AUM_Cr": "AUM (₹ Cr)", "AMC": ""},
              text="Average_AUM_Cr",
              color_discrete_sequence=["#2D61FF"])
fig1.update_traces(texttemplate="%{text:,.0f}", textposition="inside")
fig1.update_layout(
    yaxis={"categoryorder": "total ascending"},
    xaxis={"tickformat": ","},
    margin={"r": 50, "l": 10},
    height=450
)

# Chart 2 - Funds by Category
category_counts = (active.groupby("Broad_Category")["Scheme_Code"]
                   .count().reset_index()
                   .rename(columns={"Scheme_Code": "Fund_Count"})
                   .sort_values("Fund_Count", ascending=False))

fig2 = px.bar(category_counts, x="Broad_Category", y="Fund_Count",
              title="Number of Active Funds by Category",
              labels={"Broad_Category": "", "Fund_Count": "Number of Funds"},
              text="Fund_Count", color="Broad_Category",
              color_discrete_sequence=px.colors.qualitative.Pastel)
fig2.update_traces(textposition="inside")
fig2.update_layout(showlegend=False, height=450)

# Chart 3 - Scheme Type donut
scheme_type_counts = (active.groupby("Scheme_Type")["Scheme_Code"]
                      .count().reset_index()
                      .rename(columns={"Scheme_Code": "Fund_Count"}))

fig3 = px.pie(scheme_type_counts, names="Scheme_Type", values="Fund_Count",
              title="Funds by Scheme Type", hole=0.35,
              color_discrete_sequence=px.colors.qualitative.Pastel)
fig3.update_traces(
    textinfo="percent",
    textposition="inside",
    pull=[0, 0.08, 0.08]
    )
fig3.update_layout(height=420)

# Chart 4 - Launches by year
launches = (active.groupby("Launch_Year")["Scheme_Code"]
            .count().reset_index()
            .rename(columns={"Scheme_Code": "Funds_Launched"}))
launches = launches[launches["Launch_Year"] >= 2000]

fig4 = px.line(launches, x="Launch_Year", y="Funds_Launched",
               title="New Fund Launches per Year (2000 onwards)",
               labels={"Launch_Year": "Year", "Funds_Launched": "Funds Launched"},
               markers=True)
fig4.update_traces(line_color="#2D61FF", line_width=2.5)
fig4.update_layout(height=420)

# ── Styles ────────────────────────────────────────────────────────────────────

CARD_STYLE = {
    "background": "white",
    "padding": "20px 40px",
    "borderRadius": "10px",
    "textAlign": "center",
    "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
    "fontFamily": "Arial",
    "minWidth": "160px"
}

ROW_STYLE = {
    "display": "flex",
    "flexDirection": "row",
    "gap": "20px",
    "padding": "0 20px",
    "alignItems": "flex-start"
}

# ── Dash Layout ───────────────────────────────────────────────────────────────

app = Dash(__name__)

app.layout = html.Div([

    # Header
    html.H1("Indian Mutual Funds Dashboard",
            style={"textAlign": "center", "fontFamily": "Arial",
                   "padding": "24px 0 8px 0", "margin": 0}),

    # KPI Cards
    html.Div([
        html.Div([
            html.H3("Active Funds", style={"margin": "0 0 8px 0", "fontSize": "14px", "color": "#666"}),
            html.H2(f"{total_funds:,}", style={"margin": 0, "fontSize": "28px"})
        ], style=CARD_STYLE),
        html.Div([
            html.H3("Fund Houses (AMCs)", style={"margin": "0 0 8px 0", "fontSize": "14px", "color": "#666"}),
            html.H2(f"{total_amcs}", style={"margin": 0, "fontSize": "28px"})
        ], style=CARD_STYLE),
        html.Div([
            html.H3("Total AUM", style={"margin": "0 0 8px 0", "fontSize": "14px", "color": "#666"}),
            html.H2(f"₹{total_aum/1e5:.1f}L Cr", style={"margin": 0, "fontSize": "28px"})
        ], style=CARD_STYLE),
    ], style={
        "display": "flex",
        "flexDirection": "row",
        "justifyContent": "center",
        "gap": "32px",
        "padding": "24px 20px"
    }),

# Dropdown filter
html.Div([
    html.Label("Filter by Category:",
               style={"fontFamily": "Arial", "fontWeight": "bold", "marginRight": "10px"}),
    dcc.Dropdown(
        id="category-filter",
        options=[{"label": "All Categories", "value": "All"}] +
                [{"label": c, "value": c} for c in sorted(active["Broad_Category"].unique())],
        value="All",                # default selection
        clearable=False,
        style={"width": "300px"}
    )
], style={"display": "flex", "alignItems": "center",
          "padding": "0 20px 20px 20px", "fontFamily": "Arial"}),

    # Row 1 - AMC bar + Category bar
    html.Div([
        dcc.Graph(figure=fig1, id="amc-chart", style={"flex": "55%", "minWidth": 0}),
        dcc.Graph(figure=fig2, id= "category-chart", style={"flex": "45%", "minWidth": 0}),
    ], style=ROW_STYLE),

    # Row 2 - Donut + Line
    html.Div([
        dcc.Graph(figure=fig3, id="scheme-chart", style={"flex": "40%", "minWidth": 0}),
        dcc.Graph(figure=fig4, id="launch-chart", style={"flex": "60%", "minWidth": 0}),
   ], style={**ROW_STYLE, "marginTop": "20px"}),

], style={"backgroundColor": "#f4f6f9", "minHeight": "100vh", "paddingBottom": "40px"})

@callback(
    Output("amc-chart", "figure"),
    Output("category-chart", "figure"),
    Output("scheme-chart", "figure"),
    Output("launch-chart", "figure"),
    Input("category-filter", "value")
)
def update_charts(selected_category):
    # Filter data based on selection
    if selected_category == "All":
        filtered = active.copy()
    else:
        filtered = active[active["Broad_Category"] == selected_category].copy()

    # Rebuild fig1
    amc_aum = (filtered.groupby("AMC")["Average_AUM_Cr"]
               .sum().reset_index()
               .sort_values("Average_AUM_Cr", ascending=False).head(15))
    amc_aum["Average_AUM_Cr"] = amc_aum["Average_AUM_Cr"].round(0)
    amc_aum["AMC"] = (amc_aum["AMC"]
        .str.replace(r"\bLimited\b", "Ltd.", regex=True)
        .str.replace(r"\bManagement\b", "Mgmt.", regex=True)
        .str.replace(r"\bCompany\b", "Co.", regex=True)
        .str.replace(r"\bPrivate\b", "Pvt.", regex=True))
    f1 = px.bar(amc_aum, x="Average_AUM_Cr", y="AMC", orientation="h",
                title="Top 15 AMCs by Total AUM (₹ Cr)",
                labels={"Average_AUM_Cr": "AUM (₹ Cr)", "AMC": ""},
                text="Average_AUM_Cr", color_discrete_sequence=["#636EFA"])
    f1.update_traces(texttemplate="%{text:,.0f}", textposition="inside")
    f1.update_layout(yaxis={"categoryorder": "total ascending"},
                     xaxis={"tickformat": ","}, margin={"r": 150, "l": 10}, height=450)

    # Rebuild fig2
    cat_counts = (filtered.groupby("Broad_Category")["Scheme_Code"]
                  .count().reset_index()
                  .rename(columns={"Scheme_Code": "Fund_Count"})
                  .sort_values("Fund_Count", ascending=False))
    f2 = px.bar(cat_counts, x="Broad_Category", y="Fund_Count",
                title="Number of Active Funds by Category",
                labels={"Broad_Category": "", "Fund_Count": "Number of Funds"},
                text="Fund_Count", color="Broad_Category",
                color_discrete_sequence=px.colors.qualitative.Pastel)
    f2.update_traces(textposition="outside")
    f2.update_layout(showlegend=False, height=450)

    # Rebuild fig3
    scheme_counts = (filtered.groupby("Scheme_Type")["Scheme_Code"]
                     .count().reset_index()
                     .rename(columns={"Scheme_Code": "Fund_Count"}))
    f3 = px.pie(scheme_counts, names="Scheme_Type", values="Fund_Count",
                title="Funds by Scheme Type", hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Pastel)
    f3.update_traces(textinfo="percent", textposition="inside", pull=[0, 0.08, 0.08])
    f3.update_layout(height=420)

    # Rebuild fig4
    launches = (filtered.groupby("Launch_Year")["Scheme_Code"]
                .count().reset_index()
                .rename(columns={"Scheme_Code": "Funds_Launched"}))
    launches = launches[launches["Launch_Year"] >= 2000]
    f4 = px.line(launches, x="Launch_Year", y="Funds_Launched",
                 title="New Fund Launches per Year (2000 onwards)",
                 labels={"Launch_Year": "Year", "Funds_Launched": "Funds Launched"},
                 markers=True)
    f4.update_traces(line_color="#636EFA", line_width=2.5)
    f4.update_layout(height=420)

    return f1, f2, f3, f4

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8050)), debug=False)
