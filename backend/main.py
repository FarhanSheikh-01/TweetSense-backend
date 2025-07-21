from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from database import engine, Base
from routes import router


import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import re
from wordcloud import WordCloud, STOPWORDS

# ----------------------------------------
# App Initialization
# ----------------------------------------

app = FastAPI()

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

# CORS settings
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://tweetsens.netlify.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static images directory for visuals
STATIC_DIR = "static"
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# ----------------------------------------
# Existing API routes
# ----------------------------------------

app.include_router(router)

# ----------------------------------------
# Visualization Endpoints
# ----------------------------------------

class Tweet(BaseModel):
    username: str
    tweet_id: str
    content: str
    date: str
    sentiment: str
    likes: int
    retweets: int

class TweetsList(BaseModel):
    tweets: list[Tweet]

# --------- Wordcloud Generator ---------

def generate_wordcloud_image(tweets, filename="tweet_wordcloud.png"):
    text = " ".join(
        re.sub(r"http\S+|@\S+|#[A-Za-z0-9_]+", "", tweet.content)
        for tweet in tweets
    )
    wordcloud = WordCloud(
        width=800,
        height=400,
        background_color="white",
        stopwords=STOPWORDS,
        colormap="cool"
    ).generate(text)

    filepath = os.path.join(STATIC_DIR, filename)
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(filepath, bbox_inches="tight", pad_inches=0)
    plt.close()

    return filepath

# --------- Heatmap Generator ---------

def generate_heatmap_image(tweets, filename="tweet_heatmap.png"):
    entries = []
    for t in tweets:
        try:
            hour = pd.to_datetime(t.date).hour
        except Exception:
            hour = 0
        engagement = int(t.likes) + int(t.retweets)
        entries.append([t.sentiment, hour, engagement])

    df = pd.DataFrame(entries, columns=["sentiment", "hour", "engagement"])
    heatmap_df = df.pivot_table(index="sentiment", columns="hour", values="engagement", aggfunc="sum").fillna(0)

    filepath = os.path.join(STATIC_DIR, filename)
    plt.figure(figsize=(12, 4))
    sns.heatmap(heatmap_df, cmap="Reds", annot=True, fmt=".0f")
    plt.xlabel("Hour of Day")
    plt.ylabel("Sentiment")
    plt.title("Tweet Engagement Heatmap")
    plt.tight_layout()
    plt.savefig(filepath, bbox_inches="tight", pad_inches=0)
    plt.close()

    return filepath

# --------- Visualization Routes ---------

@app.post("/visualize/wordcloud")
async def wordcloud_endpoint(data: TweetsList):
    img_file = generate_wordcloud_image(data.tweets)
    return {"url": f"/static/{os.path.basename(img_file)}"}

@app.post("/visualize/heatmap")
async def heatmap_endpoint(data: TweetsList):
    img_file = generate_heatmap_image(data.tweets)
    return {"url": f"/static/{os.path.basename(img_file)}"}
