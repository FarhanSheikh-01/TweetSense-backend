from sqlalchemy import Column, Integer, String, DateTime
from database import Base

class Tweet(Base):
    __tablename__ = "tweets"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False)
    tweet_id = Column(String, unique=True, nullable=False)
    content = Column(String, nullable=False)
    date = Column(String, nullable=False)
    sentiment = Column(String)
    likes = Column(Integer, default=0)
    retweets = Column(Integer, default=0)
