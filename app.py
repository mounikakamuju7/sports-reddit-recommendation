'''
from fastapi import FastAPI
import pandas as pd
import numpy as np
from sklearn.decomposition import TruncatedSVD

app = FastAPI(title="Sports Reddit News Recommendation API")
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Load Data
# -----------------------------
df = pd.read_csv("data/reddit_sports_news_data_1500.csv")
df["user_id"] = df["user_id"].astype(str)

# -----------------------------
# Train-Test Split
# -----------------------------
df = df.sample(frac=1, random_state=42)

train_list = []
test_list = []

for user in df["user_id"].unique():
    user_data = df[df["user_id"] == user]

    if len(user_data) < 2:
        train_list.append(user_data)
        continue

    split = int(0.8 * len(user_data))
    train_list.append(user_data.iloc[:split])
    test_list.append(user_data.iloc[split:])

train_df = pd.concat(train_list)
test_df = pd.concat(test_list) if test_list else pd.DataFrame()

# -----------------------------
# Build User-Item Matrix
# -----------------------------
user_item_matrix = pd.crosstab(
    train_df["user_id"],
    train_df["post_id"]
)

if user_item_matrix.shape[1] > 1:

    matrix = user_item_matrix.values
    n_components = min(20, matrix.shape[1] - 1)

    svd = TruncatedSVD(n_components=n_components, random_state=42)
    latent_matrix = svd.fit_transform(matrix)

    reconstructed_matrix = np.dot(latent_matrix, svd.components_)

    predicted_ratings = pd.DataFrame(
        reconstructed_matrix,
        index=user_item_matrix.index,
        columns=user_item_matrix.columns
    )

else:
    predicted_ratings = pd.DataFrame()

# -----------------------------
# Recommendation Function
# -----------------------------
def get_recommendations(user_id, top_n=5):

    user_id = str(user_id)

    if user_id not in predicted_ratings.index:
        return []

    user_scores = predicted_ratings.loc[user_id]

    interacted = user_item_matrix.loc[user_id]
    user_scores = user_scores[interacted == 0]

    top_items = user_scores.sort_values(ascending=False).head(top_n).index

    recommendations = df[
        df["post_id"].isin(top_items)
    ][["post_id", "news", "subreddit"]].drop_duplicates()

    return recommendations.to_dict(orient="records")

# -----------------------------
# Evaluation Function
# -----------------------------
def evaluate(k=5):

    precisions = []
    recalls = []
    ndcgs = []

    for user in test_df["user_id"].unique():

        recs = get_recommendations(user, top_n=k)

        actual_items = test_df[
            test_df["user_id"] == user
        ]["post_id"].values

        recommended_ids = [item["post_id"] for item in recs]

        if len(actual_items) == 0:
            continue

        relevant = len(set(recommended_ids) & set(actual_items))

        precision = relevant / k
        recall = relevant / len(actual_items)

        dcg = 0
        for i, item in enumerate(recommended_ids):
            if item in actual_items:
                dcg += 1 / np.log2(i + 2)

        idcg = sum(
            [1 / np.log2(i + 2) for i in range(min(len(actual_items), k))]
        )

        ndcg = dcg / idcg if idcg > 0 else 0

        precisions.append(precision)
        recalls.append(recall)
        ndcgs.append(ndcg)

    return {
        "precision@5": float(np.mean(precisions)),
        "recall@5": float(np.mean(recalls)),
        "ndcg@5": float(np.mean(ndcgs))
    }

# -----------------------------
# API Routes
# -----------------------------

@app.get("/")
def home():
    return {"message": "Sports Reddit News Recommendation API Running 🚀"}


@app.get("/recommend/{user_id}")
def recommend(user_id: str, top_n: int = 5):
    recommendations = get_recommendations(user_id, top_n)
    return {
        "user_id": user_id,
        "recommended_news": recommendations
    }


@app.get("/metrics")
def metrics():
    return evaluate(k=5)
'''


from fastapi import FastAPI
import pandas as pd
import numpy as np
from sklearn.decomposition import TruncatedSVD

app = FastAPI(title="Sports Reddit News Recommendation API")

# -----------------------------
# Load Data
# -----------------------------
df = pd.read_csv("data/reddit_sports_news_data_1500.csv")
df["user_id"] = df["user_id"].astype(str)

# -----------------------------
# Train-Test Split
# -----------------------------
df = df.sample(frac=1, random_state=42)

train_list = []
test_list = []

for user in df["user_id"].unique():
    user_data = df[df["user_id"] == user]

    if len(user_data) < 2:
        train_list.append(user_data)
        continue

    split = int(0.8 * len(user_data))
    train_list.append(user_data.iloc[:split])
    test_list.append(user_data.iloc[split:])

train_df = pd.concat(train_list)
test_df = pd.concat(test_list) if test_list else pd.DataFrame()

# -----------------------------
# Build User-Item Matrix
# -----------------------------
user_item_matrix = pd.crosstab(
    train_df["user_id"],
    train_df["post_id"]
)

if user_item_matrix.shape[1] > 1:

    matrix = user_item_matrix.values
    n_components = min(20, matrix.shape[1] - 1)

    svd = TruncatedSVD(n_components=n_components, random_state=42)
    latent_matrix = svd.fit_transform(matrix)

    reconstructed_matrix = np.dot(latent_matrix, svd.components_)

    predicted_ratings = pd.DataFrame(
        reconstructed_matrix,
        index=user_item_matrix.index,
        columns=user_item_matrix.columns
    )

else:
    predicted_ratings = pd.DataFrame()

# -----------------------------
# Cold Start - Trending News
# -----------------------------
def get_trending_news(top_n=5):
    trending = (
        df.groupby("post_id")
        .size()
        .sort_values(ascending=False)
        .head(top_n)
        .index
    )

    recommendations = df[
        df["post_id"].isin(trending)
    ][["post_id", "news", "subreddit"]].drop_duplicates()

    return recommendations.to_dict(orient="records")

# -----------------------------
# Personalized Recommendations
# -----------------------------
def get_recommendations(user_id, top_n=5):

    user_id = str(user_id)

    # ❄️ If new user → return trending
    if user_id not in predicted_ratings.index:
        return get_trending_news(top_n)

    user_scores = predicted_ratings.loc[user_id]
    interacted = user_item_matrix.loc[user_id]
    user_scores = user_scores[interacted == 0]

    top_items = user_scores.sort_values(ascending=False).head(top_n).index

    recommendations = df[
        df["post_id"].isin(top_items)
    ][["post_id", "news", "subreddit"]].drop_duplicates()

    # If somehow empty → fallback
    if len(recommendations) == 0:
        return get_trending_news(top_n)

    return recommendations.to_dict(orient="records")

# -----------------------------
# Routes
# -----------------------------
@app.get("/")
def home():
    return {"message": "Sports News API Running 🚀"}

@app.get("/recommend/{user_id}")
def recommend(user_id: str, top_n: int = 5):

    recommendations = get_recommendations(user_id, top_n)

    return {
        "user_id": user_id,
        "recommendations": recommendations
    }


# -----------------------------
# Evaluation Function
# -----------------------------
def evaluate(k=5):

    precisions = []
    recalls = []
    ndcgs = []

    for user in test_df["user_id"].unique():

        recs = get_recommendations(user, top_n=k)

        actual_items = test_df[
            test_df["user_id"] == user
        ]["post_id"].values

        recommended_ids = [item["post_id"] for item in recs]

        if len(actual_items) == 0:
            continue

        relevant = len(set(recommended_ids) & set(actual_items))

        precision = relevant / k
        recall = relevant / len(actual_items)

        dcg = 0
        for i, item in enumerate(recommended_ids):
            if item in actual_items:
                dcg += 1 / np.log2(i + 2)

        idcg = sum(
            [1 / np.log2(i + 2) for i in range(min(len(actual_items), k))]
        )

        ndcg = dcg / idcg if idcg > 0 else 0

        precisions.append(precision)
        recalls.append(recall)
        ndcgs.append(ndcg)

    return {
        "precision@5": float(np.mean(precisions)),
        "recall@5": float(np.mean(recalls)),
        "ndcg@5": float(np.mean(ndcgs))
    }


# -----------------------------
# Metrics Route
# -----------------------------
@app.get("/metrics")
def get_metrics():
    return evaluate(k=5)
