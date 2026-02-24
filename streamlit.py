
import streamlit as st
import requests

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(page_title="Sports Reddit News Recommender", layout="wide")

# -----------------------------
# CSS Styling
# -----------------------------

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    color: white;
    font-family: 'Segoe UI', sans-serif;
}

h1 { color: #00ffcc; text-align: center; }

.recommend-card {
    background: #1f2933;
    border-radius: 15px;
    padding: 15px;
    margin-bottom: 12px;
}

/* FORCE metric text to white */
div[data-testid="stMetric"] label {
    color: white !important;
}

div[data-testid="stMetric"] div {
    color: white !important;
}

div[data-testid="stMetricValue"] {
    color: white !important;
}

div[data-testid="stMetricLabel"] {
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

st.title("🏟️🏆 Sports Reddit News Recommendation System")

# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.header("User Preferences")

user_id = st.sidebar.text_input("Enter User ID")

selected_sport = st.sidebar.multiselect(
    "Preferred Sports",
    ["nba", "football", "cricket", "tennis", "f1"],
    default=["nba", "football", "cricket", "tennis", "f1"]
)

# -----------------------------
# Get Recommendations Button
# -----------------------------
if st.sidebar.button("Get Recommendations"):

    if user_id.strip() == "":
        st.warning("⚠️ Please enter a User ID")
    else:
        try:
            response = requests.get(
                f"http://127.0.0.1:8000/recommend/{user_id}"
            )

            data = response.json()
            recommendations = data["recommendations"]

            st.subheader("📰 Recommended Sports News")

            if not recommendations:
                st.info("❄️ No personalized data. Showing trending news.")

            for row in recommendations:

                # Filter by selected sport
                if row["subreddit"] not in selected_sport:
                    continue

                st.markdown(f"""
                <div class="recommend-card">
                    <h4>📰 {row['news']}</h4>
                    <p>🏷️ Sport: <b>{row['subreddit'].upper()}</b></p>
                    <p>🆔 Post ID: {row['post_id']}</p>
                </div>
                """, unsafe_allow_html=True)

        except:
            st.error("⚠️ Could not connect to backend. Make sure FastAPI is running.")

# -----------------------------
# Metrics Section
# -----------------------------
st.markdown("## 📊 Recommendation Metrics")

if st.button("Load Model Metrics"):

    try:
        metrics_response = requests.get("http://127.0.0.1:8000/metrics")
        metrics = metrics_response.json()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("🎯 Precision@5", f"{metrics['precision@5']:.4f}")

        with col2:
            st.metric("📥 Recall@5", f"{metrics['recall@5']:.4f}")

        with col3:
            st.metric("📈 NDCG@5", f"{metrics['ndcg@5']:.4f}")

    except:
        st.error("⚠️ Could not load metrics.")

# -----------------------------
# Footer
# -----------------------------
st.markdown("""
<hr>
<center>
🚀 Built by Mounika | Sports Reddit News Recommendation System
</center>
""", unsafe_allow_html=True)
