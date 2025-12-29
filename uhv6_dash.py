import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# =============================
# PAGE CONFIG
# =============================
st.set_page_config(
    page_title="Aging Readiness – Unplanned Hospital Visits",
    layout="wide"
)

# =============================
# DATA LOADING & CLEANING
# =============================
@st.cache_data
def load_data(path):
    df = pd.read_csv(path)

    na_vals = [
        "Not Available",
        "Not Applicable",
        "NA",
        "",
        "Too Few to Report",
        "Number of Cases Too Small",
        "Number of cases too small",
    ]
    df.replace(na_vals, np.nan, inplace=True)

    num_cols = [
        "Score",
        "Denominator",
        "Number of Patients",
        "Number of Patients Returned",
        "Lower Estimate",
        "Higher Estimate",
    ]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    return df

@st.cache_data
def load_state_level_data(path):
    df = pd.read_csv(path)

    num_cols = [
        "Number of Hospitals Worse",
        "Number of Hospitals Same",
        "Number of Hospitals Better",
        "Number of Hospitals Too Few",
        "Number of Hospitals Fewer",
        "Number of Hospitals Average",
        "Number of Hospitals More",
        "Number of Hospitals Too Small",
    ]

    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    return df


# =============================
# MEASURE GROUPS (CMS-ALIGNED)
# =============================
MEASURE_GROUPS = {
    "EDAC – Excess Hospital Return Days": [
        "Hospital return days for heart attack patients",
        "Hospital return days for heart failure patients",
        "Hospital return days for pneumonia patients",
    ],
    "Hospital-Wide Readmission Ratio": [
        "Hybrid Hospital-Wide All-Cause Readmission Measure (HWR)",
    ],
    "Procedure / Outpatient Visit Rates": [
        "Rate of unplanned hospital visits after colonoscopy (per 1,000 colonoscopies)",
        "Rate of inpatient admissions for patients receiving outpatient chemotherapy",
        "Rate of emergency department (ED) visits for patients receiving outpatient chemotherapy",
        "Ratio of unplanned hospital visits after hospital outpatient surgery",
    ],
    "Condition-Specific 30-Day Readmission Rates": [
        "Acute Myocardial Infarction (AMI) 30-Day Readmission Rate",
        "Heart failure (HF) 30-Day Readmission Rate",
        "Pneumonia (PN) 30-Day Readmission Rate",
        "Rate of readmission for CABG",
        "Rate of readmission for chronic obstructive pulmonary disease (COPD) patients",
        "Rate of readmission after hip/knee replacement",
    ],
}

PERF_ORDER = [
    "Better Than the National Rate",
    "Better than expected",
    "Fewer Days Than Average per 100 Discharges",

    "No Different Than the National Rate",
    "No Different than expected",
    "Average Days per 100 Discharges",

    "Worse Than the National Rate",
    "Worse than expected",
    "More Days Than Average per 100 Discharges",

    "Not Available"  
]


# =============================
# LOAD DATA
# =============================
data_path = "Unplanned_Hospital_Visits-Hospital.csv"
df_raw = load_data(data_path)
state_data_path = "Unplanned_Hospital_Visits-State.csv"
df_state = load_state_level_data(state_data_path)

# perf_color_map = {
#     "No Different Than the National Rate": "#1976D2",
#     "Average Days per 100 Discharges": "#1976D2",
#     "No Different than expected": "#1976D2",
#     "Number of Cases Too Small": "#9E9E9E",
#     "Number of cases too small": "#9E9E9E",
#     "More Days Than Average per 100 Discharges": "#F54927",
#     "Worse Than the National Rate": "#F54927",
#     "Worse than expected": "#F54927",
#     "Fewer Days Than Average per 100 Discharges": "#57F527",
#     "Better Than the National Rate": "#57F527",
#     "Better than expected": "#57F527"
# }
perf_color_map = {
    # NEUTRAL
    "No Different Than the National Rate": "rgba(100, 181, 246, 0.75)",   # soft blue
    "Average Days per 100 Discharges": "rgba(100, 181, 246, 0.75)",
    "No Different than expected": "rgba(100, 181, 246, 0.75)",

    # WORSE
    "More Days Than Average per 100 Discharges": "rgba(239, 83, 80, 0.75)",  # muted red
    "Worse Than the National Rate": "rgba(239, 83, 80, 0.75)",
    "Worse than expected": "rgba(239, 83, 80, 0.75)",

    # BETTER
    "Fewer Days Than Average per 100 Discharges": "rgba(102, 187, 106, 0.75)",  # soft green
    "Better Than the National Rate": "rgba(102, 187, 106, 0.75)",
    "Better than expected": "rgba(102, 187, 106, 0.75)",

    # NOT ENOUGH DATA
    "Number of Cases Too Small": "rgba(189, 189, 189, 0.6)",
    "Number of cases too small": "rgba(189, 189, 189, 0.6)",
}

# =============================
# SIDEBAR FILTERS
# =============================
st.sidebar.title("Filters")

selected_group = st.sidebar.selectbox(
    "Measure Group",
    list(MEASURE_GROUPS.keys())
)

available_measures = MEASURE_GROUPS[selected_group]

selected_measures = st.sidebar.multiselect(
    "Measure",
    options=available_measures,
    default=[available_measures[0]]
)

selected_states = st.sidebar.multiselect(
    "State",
    sorted(df_raw["State"].dropna().unique()),
    default=[]
)

# Apply filters
df = df_raw[df_raw["Measure Name"].isin(selected_measures)].copy()
if selected_states:
    df = df[df["State"].isin(selected_states)]

# =============================
# HEADER
# =============================
st.title("🏥 Unplanned Hospital Visits Dashboard")
st.caption(
    "Comparisons are shown only within methodologically comparable measure groups. Lower scores indicate better performance."
)

# =============================
# KPI ROW
# =============================
valid_score = df["Score"].notna()

k1, k2, k3, k4 = st.columns(4)

k1.metric("Hospitals", df["Facility ID"].nunique())
k2.metric("Measures", df["Measure Name"].nunique())
k3.metric("Data Coverage", f"{valid_score.mean():.0%}")

if valid_score.any():
    k4.metric("Average Score", f"{df.loc[valid_score, 'Score'].mean():.2f}")
else:
    k4.metric("Average Score", "N/A")

st.markdown("---")

# =============================
# TABS
# =============================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Performance",
    "📈 Volume",
    "🗺️ Geography",
    "🏆 Rankings",
    "🏛️ State Benchmark"
])

# =============================
# TAB 1 – PERFORMANCE
# =============================
with tab1:
    st.subheader("Score Distribution")
    # st.caption("Distribution shown only within comparable measures")

    # fig_hist = px.histogram(
    #         df[df["Score"].notna()],
    #         x="Score",
    #         color="Compared to National",
    #         color_discrete_map=perf_color_map,
    #         template="plotly_dark",
    #         barmode="overlay"
    #     )
    fig_hist = px.histogram(
        df[df["Score"].notna()],
        x="Score",
        color="Compared to National",
        facet_col="Measure Name",
        facet_col_wrap=2,
        color_discrete_map=perf_color_map,
        template="plotly_dark"
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    fig_box = px.box(
        df[df["Score"].notna()],
        x="Measure Name",
        y="Score",
        points="outliers",
        template="plotly_dark",
        color ="Measure Name"
    )
    fig_box.update_layout(showlegend=False)
    st.plotly_chart(fig_box, use_container_width=True)

    st.subheader("Performance vs National Benchmark")

    df_perf = df.copy()

    df_perf["Compared to National Display"] = (
        df_perf["Compared to National"]
        .fillna("Not Available")
)
    # perf = (
    #     df_perf.dropna(subset=["Compared to National"])
    #     .groupby(["Measure Name", "Compared to National"])
    #     .size()
    #     .reset_index(name="Hospitals")
    # )
    perf = (
        df_perf.groupby(["Measure Name", "Compared to National Display"])
        .size()
        .reset_index(name="Hospitals")
    )

    perf_color_map["Not Available"] = "rgba(189, 189, 189, 0.6)"

    fig_perf = px.bar(
        perf,
        x="Measure Name",
        y="Hospitals",
        color= "Compared to National Display",
        barmode="stack",
        template="plotly_dark",
        color_discrete_map=perf_color_map,
        category_orders={
        "Compared to National Display": PERF_ORDER
    }
    )
    st.plotly_chart(fig_perf, use_container_width=True)

# =============================
# TAB 2 – VOLUME & SYSTEM STRESS
# =============================
with tab2:
    if selected_group != "EDAC – Excess Hospital Return Days":
        st.info(
            "NOTE: Volume analysis is available only for EDAC measures "
            "(excess hospital return days)."
        )
    else:
        st.subheader("Patient Volume vs Outcome")
        st.caption("Highlights high-volume hospitals with disproportionate impact")

        df_scatter = df.dropna(subset=["Score", "Number of Patients"]).copy()

        df_scatter["bubble_size"] = (
            df_scatter["Number of Patients Returned"]
            .fillna(df_scatter["Number of Patients"])
        )

        fig_scatter = px.scatter(
            df_scatter,
            x="Number of Patients",
            y="Score",
            size="bubble_size",
            color="Compared to National",
            hover_name="Facility Name",
            template="plotly_dark",
            size_max=40,
            color_discrete_map=perf_color_map,
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

        st.subheader("High-Volume Contributors")
        top_vol = df_scatter.sort_values("Number of Patients", ascending=False).head(15)
        st.dataframe(
            top_vol[["Facility Name", "State", "Number of Patients", "Score"]],
            hide_index=True,
        )

# =============================
# TAB 3 – GEOGRAPHY
# =============================
with tab3:
    st.subheader("State-Level Average Performance")

    state_avg = (
        df[df["Score"].notna()]
        .groupby("State")["Score"]
        .mean()
        .reset_index()
    )

    fig_map = px.choropleth(
        state_avg,
        locations="State",
        locationmode="USA-states",
        color="Score",
        color_continuous_scale="RdYlGn_r",
        scope="usa",
        title="Average Score per State"
    )
    fig_map.add_scattergeo(
        locations= state_avg['State'],
        locationmode='USA-states',
        text=state_avg['State'],
        mode='text', 
        showlegend=False  
    )   
    fig_map.update_layout(
        geo=dict(bgcolor='rgba(0,0,0,0)'),
        width=1000,
        height=800
    ) 

    # fig_map = px.choropleth(
    #     state_avg,
    #     locations="State",
    #     locationmode="USA-states",
    #     color="Score",
    #     scope="usa",
    #     template="plotly_dark",
    #     color_continuous_scale="RdYlGn_r",
    # )
    # fig_map.update_layout(
    #     geo_bgcolor="rgba(0,0,0,0)",
    #     paper_bgcolor="rgba(0,0,0,0)",
    # )
    st.plotly_chart(fig_map, use_container_width=True)

    st.subheader("State-Level Scores (Table View)")

    state_table = (
        state_avg
        .sort_values("Score", ascending=False)  
        .rename(columns={"Score": "Average Score"})
    )

    # st.dataframe(
    #     state_table,
    #     hide_index=True
    # )
    with st.expander("View State Data Table"):
        st.dataframe(state_table.style.background_gradient(cmap="RdYlGn_r"))

# =============================
# TAB 4 – RANKINGS
# =============================
with tab4:
    st.subheader("Hospital Rankings")

    ranked = df[df["Score"].notna()].sort_values("Score", ascending=False)

    c1, c2 = st.columns(2)

    with c1:
        st.error("⚠️ Lowest Performing Hospitals (Highest Scores)")
        st.dataframe(
            ranked.head(10)[["Facility Name", "State", "Score"]],
            hide_index=True,
        )
    
    with c2:
        best_10 = (
            ranked
            .tail(10)              
            .sort_values("Score")  
        )

        st.success("🌟 Best Performing Hospitals (Lowest Scores)")
        st.dataframe(
            best_10[["Facility Name", "State", "Score"]],
            hide_index=True,
        )
        # st.success("🌟 Best Performing Hospitals (Lowest Scores)")
        # st.dataframe(
        #     ranked.tail(10)[["Facility Name", "State", "Score"]],
        #     hide_index=True,
        # )
# =============================
# TAB 5 – STATE-LEVEL BENCHMARK
# =============================

STATE_BENCHMARK_CONFIG = {
    "EDAC – Excess Hospital Return Days": {
        "columns": [
            "Number of Hospitals Fewer",
            "Number of Hospitals Average",
            "Number of Hospitals More",
            "Number of Hospitals Too Small",
        ],
        "colors": {
            "Number of Hospitals Fewer": "rgba(102, 187, 106, 0.75)",
            "Number of Hospitals Average": "rgba(100, 181, 246, 0.75)",
            "Number of Hospitals More": "rgba(239, 83, 80, 0.75)",
            "Number of Hospitals Too Small": "rgba(189, 189, 189, 0.6)",
        },
    },

    "Hospital-Wide Readmission Ratio": {
        "columns": [
            "Number of Hospitals Better",
            "Number of Hospitals Same",
            "Number of Hospitals Worse",
            "Number of Hospitals Too Small",
        ],
        "colors": {
            "Number of Hospitals Better": "rgba(102, 187, 106, 0.75)",
            "Number of Hospitals Same": "rgba(100, 181, 246, 0.75)",
            "Number of Hospitals Worse": "rgba(239, 83, 80, 0.75)",
            "Number of Hospitals Too Small": "rgba(189, 189, 189, 0.6)",
        },
    },

    "Procedure / Outpatient Visit Rates": {
        "columns": [
            "Number of Hospitals Better",
            "Number of Hospitals Same",
            "Number of Hospitals Worse",
            "Number of Hospitals Too Small",
        ],
        "colors": {
            "Number of Hospitals Better": "rgba(102, 187, 106, 0.75)",
            "Number of Hospitals Same": "rgba(100, 181, 246, 0.75)",
            "Number of Hospitals Worse": "rgba(239, 83, 80, 0.75)",
            "Number of Hospitals Too Small": "rgba(189, 189, 189, 0.6)",
        },
    },

    "Condition-Specific 30-Day Readmission Rates": {
        "columns": [
            "Number of Hospitals Better",
            "Number of Hospitals Same",
            "Number of Hospitals Worse",
            "Number of Hospitals Too Small",
        ],
        "colors": {
            "Number of Hospitals Better": "rgba(102, 187, 106, 0.75)",
            "Number of Hospitals Same": "rgba(100, 181, 246, 0.75)",
            "Number of Hospitals Worse": "rgba(239, 83, 80, 0.75)",
            "Number of Hospitals Too Small": "rgba(189, 189, 189, 0.6)",
        },
    },
}

PERF_ORDER_STATE = [
    "Number of Hospitals Fewer",
    "Number of Hospitals Better",

    "Number of Hospitals Average",
    "Number of Hospitals Same",

    "Number of Hospitals More",
    "Number of Hospitals Worse",

    "Number of Hospitals Too Small",
    "Not Available"  
]


with tab5:
    st.subheader("State-Level Hospital Performance vs National Benchmark")
    st.caption(
        "CMS-reported counts of hospitals by performance category, shown using the original CMS methodology."
    )

    if selected_group not in STATE_BENCHMARK_CONFIG:
        st.info("State-level benchmark is not available for this measure group.")
        st.stop()

    config = STATE_BENCHMARK_CONFIG[selected_group]
    value_cols = config["columns"]
    color_map = config["colors"]

    # Filter
    state_filtered = df_state[
        df_state["Measure Name"].isin(selected_measures)
    ].copy()

    if selected_states:
        state_filtered = state_filtered[
            state_filtered["State"].isin(selected_states)
        ]

    # Drop rows without any benchmark data
    state_filtered = state_filtered.dropna(subset=value_cols, how="all")

    # Melt
    state_long = state_filtered.melt(
        id_vars=["State", "Measure Name"],
        value_vars=value_cols,
        var_name="Performance",
        value_name="Hospitals"
    )

    # Plot
    fig_state_perf = px.bar(
        state_long,
        x="State",
        y="Hospitals",
        color="Performance",
        facet_col="Measure Name",
        facet_col_wrap=2,
        barmode="stack",
        template="plotly_dark",
        color_discrete_map=color_map,
        category_orders={
            "Performance": PERF_ORDER_STATE
        }
    )

    fig_state_perf.update_layout(
        legend_title_text="Performance Category",
        xaxis_title="State",
        yaxis_title="Number of Hospitals"
    )

    st.plotly_chart(fig_state_perf, use_container_width=True)

    # Table
    st.subheader("State-Level Summary Table")

    with st.expander("View State Benchmark Table"):
        st.dataframe(
            state_filtered[
                ["State", "Measure Name"] + value_cols
            ].sort_values(
                value_cols[-2], ascending=False
            ),
            hide_index=True
        )
