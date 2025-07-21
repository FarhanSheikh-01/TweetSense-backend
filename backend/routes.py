from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import test
import models
import schemas
from database import SessionLocal

router = APIRouter()

# Dependency to get a DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Set to False to disable fetching from X (Twitter) API
FETCH_ENABLED = True

# -------------------------------
# Fetch Tweets from Twitter APIs
# -------------------------------

@router.post("/fetch/username/{username}")
def fetch_by_username(username: str, db: Session = Depends(get_db)):
    if not FETCH_ENABLED:
        raise HTTPException(
            status_code=403,
            detail="Fetching from X API is disabled due to rate limits or quota. Use only stored tweets for analysis."
        )
    try:
        test.fetch_tweets_by_username(db, username)
        return {"message": f"Tweets by @{username} fetched and stored with sentiment."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/fetch/hashtag/{hashtag}")
def fetch_by_hashtag(hashtag: str, db: Session = Depends(get_db)):
    if not FETCH_ENABLED:
        raise HTTPException(
            status_code=403,
            detail="Fetching from X API is disabled due to rate limits or quota. Use only stored tweets for analysis."
        )
    try:
        test.fetch_tweets_by_hashtag(db, hashtag)
        return {"message": f"Tweets with #{hashtag} fetched and stored with sentiment."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/fetch/id/{tweet_id}")
def fetch_by_id(tweet_id: str, db: Session = Depends(get_db)):
    if not FETCH_ENABLED:
        raise HTTPException(
            status_code=403,
            detail="Fetching from X API is disabled due to rate limits or quota. Use only stored tweets for analysis."
        )
    try:
        test.fetch_tweet_by_id(db, tweet_id)
        return {"message": f"Tweet with ID {tweet_id} fetched and stored with sentiment."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# -------------------------------
# Retrieve Stored Tweets
# -------------------------------

@router.get("/tweets", response_model=List[schemas.Tweet])
def get_all_tweets(db: Session = Depends(get_db)):
    tweets = db.query(models.Tweet).order_by(models.Tweet.date.desc()).all()
    if not tweets:
        raise HTTPException(status_code=404, detail="No tweets found in the database.")
    return tweets

@router.get("/tweets/username/{username}", response_model=List[schemas.Tweet])
def get_tweets_by_username(username: str, db: Session = Depends(get_db)):
    tweets = db.query(models.Tweet).filter(models.Tweet.username.ilike(username)).all()
    if not tweets:
        raise HTTPException(status_code=404, detail=f"No tweets found for username '{username}'.")
    return tweets

@router.get("/tweets/id/{tweet_id}", response_model=schemas.Tweet)
def get_tweet_by_id(tweet_id: str, db: Session = Depends(get_db)):
    tweet = db.query(models.Tweet).filter(models.Tweet.tweet_id == tweet_id).first()
    if not tweet:
        raise HTTPException(status_code=404, detail=f"Tweet ID '{tweet_id}' not found.")
    return tweet

@router.get("/tweets/hashtag/{hashtag}", response_model=List[schemas.Tweet])
def get_tweets_by_hashtag(hashtag: str, db: Session = Depends(get_db)):
    search = f"#{hashtag}"
    tweets = db.query(models.Tweet).filter(models.Tweet.content.ilike(f"%{search}%")).all()
    if not tweets:
        raise HTTPException(status_code=404, detail=f"No tweets found with hashtag '{hashtag}'.")
    return tweets
