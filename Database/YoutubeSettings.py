from sqlalchemy import Column, Integer, String, BigInteger, select
from Database.DatabaseConfig import Session, Base

class YoutubeSettings(Base):
    __tablename__ = 'youtube_settings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    youtube_id = Column(String)
    mention_role_id = Column(BigInteger)
    post_channel_id = Column(BigInteger)
    last_video_id = Column(String)

    async def get_all():
        async with Session() as session:
            stmt = select(YoutubeSettings)
            results = await session.execute(stmt)
            return results.scalars().all()
        
    async def update(self):
        async with Session() as session:
            session.add(self)
            await session.commit()