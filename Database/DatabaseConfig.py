import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

DATABASE_URL = os.environ.get('DATABASE_URL')
engine = create_async_engine(DATABASE_URL)
Session = async_sessionmaker(engine, expire_on_commit=False)