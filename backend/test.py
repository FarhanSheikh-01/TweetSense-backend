import logging
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
import tweepy
import models
from ml_model import predict_sentiment

logging.basicConfig(level=logging.INFO)
load_dotenv()

# Load bearer tokens from env file
BEARER_TOKENS = [
    os.getenv("BEARER_TOKEN_1"),
    os.getenv("BEARER_TOKEN_2"),
    os.getenv("BEARER_TOKEN_3"),
    os.getenv("BEARER_TOKEN_4")
]

MAX_RESULTS = 20

def get_client(token):
    return tweepy.Client(bearer_token=token)

def rotate_tokens_fetch(fetch_function, *args, **kwargs):
    """
    Tries each bearer token in order. If all fail, raises the last exception.
    fetch_function: function to call with Tweepy client as argument
    """
    last_exception = None
    for idx, token in enumerate(BEARER_TOKENS):
        client = get_client(token)
        try:
            logging.info(f"Trying Bearer Token #{idx+1}")
            return fetch_function(client, *args, **kwargs)
        except tweepy.TooManyRequests:
            logging.warning(f"Token {idx+1} hit rate limit. Trying next token.")
            continue
        except tweepy.Unauthorized:
            logging.warning(f"Token {idx+1} unauthorized. Trying next token.")
            continue
        except Exception as e:
            logging.error(f"Token {idx+1} exception: {e}")
            last_exception = e
            continue
    raise last_exception if last_exception else Exception("All bearer tokens failed.")

def fetch_tweets_by_username(db: Session, username: str):
    def _fetch(client, db, username):
        user = client.get_user(username=username)
        tweets = client.get_users_tweets(
            user.data.id,
            max_results=MAX_RESULTS,
            tweet_fields=["created_at", "public_metrics"]
        )
        if not tweets.data:
            logging.info(f"No tweets found for @{username}")
            return

        for tweet in tweets.data:
            if db.query(models.Tweet).filter_by(tweet_id=str(tweet.id)).first():
                logging.info(f"⏩ Tweet ID {tweet.id} already exists. Skipping.")
                continue

            metrics = tweet.public_metrics
            sentiment = predict_sentiment(tweet.text)

            tweet_obj = models.Tweet(
                username=username.lower(),
                tweet_id=str(tweet.id),
                content=tweet.text,
                date=str(tweet.created_at),
                sentiment=sentiment,
                retweets=metrics["retweet_count"],
                likes=metrics["like_count"]
            )
            db.add(tweet_obj)
            logging.info(f"✅ Added tweet ID {tweet.id}")

        db.commit()
        logging.info(f"✅ DB COMMIT executed for @{username}")

    # Use rotation logic
    rotate_tokens_fetch(_fetch, db, username)

def fetch_tweets_by_hashtag(db: Session, hashtag: str):
    def _fetch(client, db, hashtag):
        query = f"#{hashtag}"
        tweets = client.search_recent_tweets(
            query=query,
            max_results=MAX_RESULTS,
            tweet_fields=["created_at", "author_id", "public_metrics"]
        )

        if not tweets.data:
            logging.info(f"No tweets found for #{hashtag}")
            return

        for tweet in tweets.data:
            if db.query(models.Tweet).filter_by(tweet_id=str(tweet.id)).first():
                logging.info(f"⏩ Tweet ID {tweet.id} already exists. Skipping.")
                continue

            try:
                user = client.get_user(id=tweet.author_id)
                username = user.data.username
            except Exception:
                username = str(tweet.author_id)

            metrics = tweet.public_metrics
            sentiment = predict_sentiment(tweet.text)

            tweet_obj = models.Tweet(
                username=username.lower(),
                tweet_id=str(tweet.id),
                content=tweet.text,
                date=str(tweet.created_at),
                sentiment=sentiment,
                retweets=metrics["retweet_count"],
                likes=metrics["like_count"]
            )
            db.add(tweet_obj)
            logging.info(f"✅ Added tweet ID {tweet.id}")

        db.commit()
        logging.info(f"✅ DB COMMIT executed for #{hashtag}")

    # Use rotation logic
    rotate_tokens_fetch(_fetch, db, hashtag)

def fetch_tweet_by_id(db: Session, tweet_id: str):
    def _fetch(client, db, tweet_id):
        tweet = client.get_tweet(
            tweet_id,
            tweet_fields=["created_at", "author_id", "public_metrics"]
        )

        if not tweet.data:
            raise ValueError("Tweet not found.")

        if db.query(models.Tweet).filter_by(tweet_id=str(tweet.data.id)).first():
            logging.info(f"⏩ Tweet ID {tweet_id} already exists. Skipping.")
            return

        try:
            user = client.get_user(id=tweet.data.author_id)
            username = user.data.username
        except Exception:
            username = str(tweet.data.author_id)

        metrics = tweet.data.public_metrics
        sentiment = predict_sentiment(tweet.data.text)

        tweet_obj = models.Tweet(
            username=username.lower(),
            tweet_id=str(tweet.data.id),
            content=tweet.data.text,
            date=str(tweet.data.created_at),
            sentiment=sentiment,
            retweets=metrics["retweet_count"],
            likes=metrics["like_count"]
        )
        db.add(tweet_obj)
        db.commit()
        logging.info(f"✅ Stored tweet ID {tweet_id}")

    # Use rotation logic
    rotate_tokens_fetch(_fetch, db, tweet_id)
