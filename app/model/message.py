from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base



from app.database import Base

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    channel = Column(String, index=True)
    user = Column(String)
    text = Column(String)
    timestamp = Column(String)

# Create the table