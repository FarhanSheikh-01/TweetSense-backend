from pydantic import BaseModel

class Tweet(BaseModel):
    username: str
    tweet_id: str
    content: str
    date: str
    sentiment: str
    likes: int = 0
    retweets: int = 0

    class Config:
        orm_mode = True