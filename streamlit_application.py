import streamlit as st
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# -------------------------------
# Load Data
# -------------------------------
@st.cache_data
def load_data():
    cleaned_df = pd.read_csv("cleaned_data.csv", index_col=0)
    encoded_df = pd.read_csv("encoded_data.csv", index_col=0)
    return cleaned_df, encoded_df

cleaned_df, encoded_df = load_data()

# -------------------------------
# Recommendation Function
# -------------------------------
def get_restaurants(city, cuisine, top_n=15):
    city_df = cleaned_df[cleaned_df['City'].str.lower() == city.lower()]
    cuisine_df = city_df[city_df['cuisine'].str.lower().isin([c.lower() for c in cuisine])]
    restaurant_ids = cuisine_df.index
    city_encoded = encoded_df.loc[city_df.index]
    cuisine_encoded = encoded_df.loc[restaurant_ids]

    sim_matrix = cosine_similarity(cuisine_encoded, city_encoded)
    mean_similarity = sim_matrix.mean(axis=0)

    sorted_idx = np.argsort(mean_similarity)[::-1]
    similar_restaurants = city_df.iloc[sorted_idx].head(top_n).copy()
    similar_restaurants['similarity_score'] = mean_similarity[sorted_idx][:top_n]

    cols = ["name", "rating", "rating_count", "cost", "cuisine"]
    if list(city_df["Area"].unique()) != ["Unknown"]:
        cols.append("Area")
    
    return similar_restaurants[cols].reset_index(drop=True)

# -------------------------------
# Streamlit Config
# -------------------------------
st.set_page_config(page_title="🍴 Swiggy Recommender", layout="wide")

# -------------------------------
# Custom Swiggy-Themed CSS
# -------------------------------
st.markdown("""
<style>
/* Global text */
* {
    font-family: 'Poppins', sans-serif;
    color: #2E2E2E;
}

/* Sidebar base color */
[data-testid="stSidebar"] {
    background-color: #FC8019 !important;
}
[data-testid="stSidebar"] * {
    color: white !important;
    font-size: 14px !important;
}
[data-testid="stSidebar"] img {
    display: block;
    margin: 15px auto 25px auto;
    border-radius: 12px;
}

/* Main background */
.stApp {
    background-color: #FFF8E1 !important;
}

/* Headings */
h1 {
    color: #FC8019 !important;
    font-weight: 700 !important;
    font-size: 30px !important;
}
h2, h3 {
    font-weight: 600;
}

/* Button */
div.stButton > button:first-child {
    background-color: #FC8019;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 8px 25px;
    font-weight: 600;
    font-size: 15px;
    transition: all 0.3s ease;
}
div.stButton > button:hover {
    background-color: #ff9933;
}

/* Cards */
.card {
    background-color: #FFFFFF;
    border-radius: 12px;
    padding: 12px;
    margin: 10px 6px;
    box-shadow: 0 3px 8px rgba(0,0,0,0.15);
    transition: transform 0.2s;
}
.card:hover {
    transform: scale(1.02);
}
.card h3 {
    color: #FC8019;
    font-size: 16px !important;
    margin-bottom: 6px;
}
.card p {
    font-size: 13px !important;
    margin-bottom: 4px;
}
            
}
</style>
""", unsafe_allow_html=True)

st.sidebar.header("🍽️ Filters 🍴")

city_list = sorted(cleaned_df['City'].dropna().unique())
selected_city = st.sidebar.selectbox("🏙️ Select City", city_list)

city_df = cleaned_df[cleaned_df['City'].str.lower() == selected_city.lower()]
available_cuisines = city_df["cuisine"].unique()
selected_cuisine = st.sidebar.multiselect("🍜 Select Cuisine(s)", available_cuisines)

top_n = st.sidebar.slider("🔢 Number of Recommendations", 5, 30, 10)
sort_by = st.sidebar.selectbox("📊 Sort Recommendations By", ["Similarity", "Rating"])

# -------------------------------
# Logo and Title - Flexbox for alignment
# -------------------------------
import base64

def get_image_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

col1, col2 = st.columns([1, 5])

image_base64 = get_image_base64("swiggy_logo.png")

st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 20px; margin-bottom: 10px;">
        <img src="data:image/png;base64,{image_base64}" style="width: 60px; height: auto;">
        <div>
            <h1 style="margin: 0; color: #FC8019;">Swiggy Restaurant Recommendation System</h1>
            <p style="margin: 0; font-size: 16px; color: #555;">Discover top-rated and similar restaurants near you 🍕</p>
        </div>
    </div>
""", unsafe_allow_html=True)


# -------------------------------
# Display Recommendations
# -------------------------------
if st.button("🍽️ Get Recommendations"):
    if not selected_cuisine:
        st.warning("⚠️ Please select at least one cuisine.")
    else:
        with st.spinner("🔎 Finding delicious options..."):
            recommendations = get_restaurants(selected_city, selected_cuisine, top_n=top_n)

        if recommendations.empty:
            st.info("😔 No restaurants found for the selected city and cuisine(s).")
        else:
            if sort_by == "Rating":
                recommendations = recommendations.sort_values("rating", ascending=False)

            st.success(f"✅ Found {len(recommendations)} restaurants for {selected_city}! 🍕")

            # Grid layout for cards
            cols_per_row = 3
            for i in range(0, len(recommendations), cols_per_row):
                cols = st.columns(cols_per_row)
                for j, idx in enumerate(range(i, min(i+cols_per_row, len(recommendations)))):
                    row = recommendations.iloc[idx]
                    show_area = 'Area' in row and row['Area'] != "Unknown"
                    with cols[j]:
                        st.markdown(f"""
                        <div class="card">
                            <h3>🍴 {row['name']}</h3>
                            <p>⭐ <b>{row['rating']}</b> ({row['rating_count']} reviews)</p>
                            <p>💰 Avg Cost: ₹{row['cost']}</p>
                            <p>🍛 Cuisine: {row['cuisine']}</p>
                            {f"<p>📍 {row['Area']}</p>" if show_area else ""}
                        </div>
                        """, unsafe_allow_html=True)
