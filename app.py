from io import BytesIO
from matplotlib.ticker import MaxNLocator
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import qrcode
import streamlit as st

st.set_page_config(
    page_title="Holt & Laury Risk Survey & Class Analytics", layout="wide"
)


# ---------------------------------------------------------
# SHARED CLASSROOM DATABASE (ALL PHONES WRITE TO THIS)
# ---------------------------------------------------------
@st.cache_resource
def get_global_class_data():
  return []


# Global list shared across all connected phones and laptops
global_class_data = get_global_class_data()

# ---------------------------------------------------------
# SIDEBAR: DYNAMIC QR CODE & INSTRUCTOR CONTROLS
# ---------------------------------------------------------
st.sidebar.title("Student Access QR Code")
app_url = st.sidebar.text_input(
    "App URL / Network IP:",
    value="",
    placeholder="Paste http://10.24.61.119:8501 here...",
    help="Paste your terminal Network URL here so students can scan.",
)

if app_url.strip():
  qr_img = qrcode.make(app_url.strip())
  buf = BytesIO()
  qr_img.save(buf)
  st.sidebar.image(
      buf.getvalue(), caption="Scan to open survey", use_container_width=True
  )
  st.sidebar.caption(f"Direct Link: [{app_url}]({app_url})")
else:
  st.sidebar.info("Paste your terminal Network URL above to generate QR.")

st.sidebar.markdown("---")

with st.sidebar.expander("Instructor Controls"):
  if st.button("Refresh Laptop Dashboard", type="primary"):
    st.rerun()

  if st.button("Clear All Saved Class Responses", type="secondary"):
    global_class_data.clear()
    st.success("All class responses cleared!")
    st.rerun()

# ---------------------------------------------------------
# DATA STRUCTURES & LOOKUPS
# ---------------------------------------------------------
r_map = {
    0: -1.20,
    1: -1.20,
    2: -0.72,
    3: -0.32,
    4: 0.00,
    5: 0.28,
    6: 0.545,
    7: 0.825,
    8: 1.00,
    9: 1.70,
    10: 1.70,
}

label_map = {
    0: "Highly Risk Loving",
    1: "Highly Risk Loving",
    2: "Very Risk Loving",
    3: "Risk Loving",
    4: "Risk Neutral",
    5: "Slightly Risk Averse",
    6: "Risk Averse",
    7: "Very Risk Averse",
    8: "Highly Risk Averse (Log Utility)",
    9: "Extremely Risk Averse",
    10: "Extremely Risk Averse",
}

lotteries = [
    {
        "Question": 1,
        "A": r"A: 10% chance of \$2.00, 90% chance of \$1.60",
        "B": r"B: 10% chance of \$3.85, 90% chance of \$0.10",
    },
    {
        "Question": 2,
        "A": r"A: 20% chance of \$2.00, 80% chance of \$1.60",
        "B": r"B: 20% chance of \$3.85, 80% chance of \$0.10",
    },
    {
        "Question": 3,
        "A": r"A: 30% chance of \$2.00, 70% chance of \$1.60",
        "B": r"B: 30% chance of \$3.85, 70% chance of \$0.10",
    },
    {
        "Question": 4,
        "A": r"A: 40% chance of \$2.00, 60% chance of \$1.60",
        "B": r"B: 40% chance of \$3.85, 60% chance of \$0.10",
    },
    {
        "Question": 5,
        "A": r"A: 50% chance of \$2.00, 50% chance of \$1.60",
        "B": r"B: 50% chance of \$3.85, 50% chance of \$0.10",
    },
    {
        "Question": 6,
        "A": r"A: 60% chance of \$2.00, 40% chance of \$1.60",
        "B": r"B: 60% chance of \$3.85, 40% chance of \$0.10",
    },
    {
        "Question": 7,
        "A": r"A: 70% chance of \$2.00, 30% chance of \$1.60",
        "B": r"B: 70% chance of \$3.85, 30% chance of \$0.10",
    },
    {
        "Question": 8,
        "A": r"A: 80% chance of \$2.00, 20% chance of \$1.60",
        "B": r"B: 80% chance of \$3.85, 20% chance of \$0.10",
    },
    {
        "Question": 9,
        "A": r"A: 90% chance of \$2.00, 10% chance of \$1.60",
        "B": r"B: 90% chance of \$3.85, 10% chance of \$0.10",
    },
    {
        "Question": 10,
        "A": r"A: 100% chance of \$2.00, 0% chance of \$1.60",
        "B": r"B: 100% chance of \$3.85, 0% chance of \$0.10",
    },
]


def calc_kelly(r):
  if r <= 0:
    return 1.0
  ratio = (0.60 / 0.40) ** (1.0 / r)
  return (ratio - 1.0) / (ratio + 1.0)


def get_norm_utility(r_val, W_array):
  if abs(r_val - 1.0) < 1e-4:
    U = np.log(W_array)
  elif abs(r_val) < 1e-4:
    U = W_array
  else:
    U = (W_array ** (1.0 - r_val)) / (1.0 - r_val)
  return (U - U[0]) / (U[-1] - U[0]) * 100


tab1, tab2 = st.tabs(["Student Survey", "Live Class Analytics"])

# ---------------------------------------------------------
# TAB 1: STUDENT SURVEY FORM (PHONES SUBMIT HERE)
# ---------------------------------------------------------
with tab1:
  st.title("Holt & Laury Risk Preference Survey")
  st.markdown(
      "For each row, choose either A or B. The percentages are the chances of receiving each amount. You receive one amount, not both. Treat every row as a separate decision; your choices do not accumulate across rows."
  )

  with st.form("student_form"):
    student_name = st.text_input("First Name / Student ID (Optional):", "")
    st.markdown("---")

    user_choices = []
    for item in lotteries:
      c1, c2, c3, c4 = st.columns([1.8, 4.3, 4.3, 1.6])
      c1.write(f"**Question {item['Question']}**")
      c2.write(item["A"])
      c3.write(item["B"])
      choice = c4.radio(
          f"Question {item['Question']}",
          options=["A", "B"],
          key=f"choice_Question_{item['Question']}",
          horizontal=True,
          label_visibility="collapsed",
      )
      user_choices.append(choice)

    st.markdown("---")
    submitted = st.form_submit_button(
        "Submit Choices & View My Utility Curve", type="primary"
    )

  if submitted:
    safe_choices = user_choices.count("A")

    # Irrationality Checks
    first_b = user_choices.index("B") if "B" in user_choices else -1
    inconsistent_switch = (
        True if (first_b != -1 and "A" in user_choices[first_b:]) else False
    )
    violated_dominance = True if user_choices[9] == "A" else False
    is_irrational = inconsistent_switch or violated_dominance

    r = r_map[safe_choices]
    label = label_map[safe_choices]
    f_star = calc_kelly(r)

    # Save to global central database
    global_class_data.append({
        "Student": (
            student_name
            if student_name
            else f"Student #{len(global_class_data)+1}"
        ),
        "Safe_Choices": safe_choices,
        "Risk_Classification": label,
        "CRRA_r": r,
        "Optimal_Kelly_f": f_star,
        "Inconsistent_Switch": inconsistent_switch,
        "Violated_Dominance": violated_dominance,
        "Irrational": is_irrational,
    })

    st.success("Survey submitted successfully!")

    # Student's individual breakdown
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Safe Choices", f"{safe_choices} / 10")
    c2.metric("Classification", label)
    c3.metric("CRRA Index (r)", f"{r:.2f}")
    c4.metric("Optimal Bet Fraction", f"{f_star:.1%}")

    if is_irrational:
      st.warning(
          " **Note on Choice Pattern:** Standard expected utility theory"
          " predicts choosing B for Question 10 and switching at most once."
      )

    W = np.linspace(1, 100, 500)
    U_norm = get_norm_utility(r, W)
    fig, ax = plt.subplots(figsize=(8, 3.5))
    ax.plot(
        W, U_norm, label=f"Your Utility (r={r:.2f})", color="blue", lw=2.5
    )
    ax.plot(
        W,
        (W - 1) / 99 * 100,
        label="Risk Neutral (r=0)",
        color="gray",
        linestyle="--",
    )
    ax.set_xlabel("Wealth ($W$)")
    ax.set_ylabel("Normalized Utility")
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.legend()
    st.pyplot(fig)

# ---------------------------------------------------------
# TAB 2: LIVE CLASS ANALYTICS DASHBOARD (LAPTOP DISPLAYS THIS)
# ---------------------------------------------------------
with tab2:
    st.title("Class-Wide Risk Preference Analytics")

    if len(global_class_data) > 0:
        df = pd.DataFrame(global_class_data)

        st.subheader(f"Summary Metrics ({len(df)} Student Submissions)")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Avg Safe Choices", f"{df['Safe_Choices'].mean():.1f} / 10")
        m2.metric("Avg Risk Coeff (r)", f"{df['CRRA_r'].mean():.2f}")
        m3.metric("Avg Optimal Bet (f*)", f"{df['Optimal_Kelly_f'].mean():.1%}")

        irrational_count = df["Irrational"].sum()
        irrational_pct = (irrational_count / len(df)) * 100
        m4.metric(
            "Non-Standard / 'Irrational'",
            f"{irrational_count} / {len(df)} ({irrational_pct:.0f}%)",
        )

        st.markdown("---")

        # Utility Overlay Curve
        st.markdown(
            "### Class Utility Curves (Individual Overlays & Class Aggregate)"
        )
        W = np.linspace(1, 100, 500)
        fig_u, ax_u = plt.subplots(figsize=(10, 4.5))

        all_utilities = []
        for idx, row in df.iterrows():
            u_student = get_norm_utility(row["CRRA_r"], W)
            all_utilities.append(u_student)
            ax_u.plot(W, u_student, color="skyblue", alpha=0.35, lw=1.2)

        avg_utility = np.mean(all_utilities, axis=0)
        ax_u.plot(
            W,
            avg_utility,
            label=(
                "Class Average Utility Curve (Mean r ="
                f" {df['CRRA_r'].mean():.2f})"
            ),
            color="darkblue",
            lw=3.5,
        )
        ax_u.plot(
            W,
            (W - 1) / 99 * 100,
            label="Risk Neutral Benchmark (U(W)=W)",
            color="red",
            linestyle="--",
            lw=2,
        )
        ax_u.set_xlabel("Wealth ($W$)")
        ax_u.set_ylabel("Normalized Utility ($U(W)$)")
        ax_u.grid(True, linestyle=":", alpha=0.6)
        ax_u.legend()
        st.pyplot(fig_u)

        st.markdown("---")

        # Distributions
        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown("### Distribution of Safe Choices")
            fig1, ax1 = plt.subplots(figsize=(6, 4))
            counts = (
                df["Safe_Choices"].value_counts().reindex(range(0, 11), fill_value=0)
            )
            ax1.bar(counts.index, counts.values, color="steelblue", edgecolor="black")
            ax1.set_xlabel("Number of Safe Choices (Option A)")
            ax1.set_ylabel("Number of Students")
            ax1.set_xticks(range(0, 11))
            ax1.set_xlim(-0.8, 10.8)
            ax1.set_ylim(0, max(counts.values) + 1.5)
            ax1.yaxis.set_major_locator(MaxNLocator(integer=True))
            ax1.grid(axis="y", linestyle=":", alpha=0.6)
            st.pyplot(fig1)

        with col_right:
            st.markdown("### Distribution of Optimal Kelly Bet Fractions (f*)")
            fig2, ax2 = plt.subplots(figsize=(6, 4))
            counts_h, _, _ = ax2.hist(
                df["Optimal_Kelly_f"] * 100,
                bins=10,
                range=(0, 100),
                color="salmon",
                edgecolor="black",
            )
            ax2.axvline(
                20,
                color="black",
                linestyle="--",
                lw=2,
                label="Full Kelly Baseline (20%)",
            )
            ax2.set_xlabel("Optimal Bet Fraction (% of Wealth)")
            ax2.set_ylabel("Number of Students")
            ax2.set_ylim(0, max(counts_h) + 1.5)
            ax2.yaxis.set_major_locator(MaxNLocator(integer=True))
            ax2.legend()
            ax2.grid(axis="y", linestyle=":", alpha=0.6)
            st.pyplot(fig2)

        st.markdown("### Individual Student Submissions Table")
        st.dataframe(
            df[[
                "Student",
                "Safe_Choices",
                "Risk_Classification",
                "CRRA_r",
                "Optimal_Kelly_f",
                "Inconsistent_Switch",
                "Violated_Dominance",
                "Irrational",
            ]],
            use_container_width=True,
        )

        # CSV Download Button (Indented inside the IF statement)
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Class Data (CSV)",
            data=csv_data,
            file_name="holt_laury_class_results.csv",
            mime="text/csv",
            type="primary",
        )

    else:
        st.info(
            "No student responses submitted yet. Have students scan the QR code in"
            " the sidebar and complete the survey."
        )

