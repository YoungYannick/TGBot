from sqlalchemy import create_engine, Column, Integer, String, Boolean, BigInteger, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.sql import func
import datetime

DATABASE_URL = "sqlite:///bot_data.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    """ 存储所有交互过的用户 """
    __tablename__ = "users"
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=False)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    lang_code = Column(String, nullable=True)

    is_verified = Column(Boolean, default=False)
    is_blocked = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_seen = Column(DateTime(timezone=True), onupdate=func.now(), default=func.now())


class BlockedKeyword(Base):
    """ 存储屏蔽的关键词 """
    __tablename__ = "blocked_keywords"
    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String, unique=True, index=True, nullable=False)
    added_at = Column(DateTime(timezone=True), server_default=func.now())

class MessageMap(Base):
    """ 保存 admin 收到的每条转发消息 与 原用户 ID 的映射 """
    __tablename__ = "message_map"
    admin_msg_id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, nullable=False)

class StartMessage(Base):
    __tablename__ = "start_message"
    id = Column(Integer, primary_key=True)
    lang = Column(String, unique=True, nullable=False)   # zh / en
    content = Column(String, nullable=False)


def init_db():
    Base.metadata.create_all(bind=engine)

    from sqlalchemy.orm import Session
    db = Session(bind=engine)

    from database import StartMessage

    # 如果没有欢迎语记录，则初始化
    if db.query(StartMessage).count() == 0:
        zh_text = """🤖 欢迎使用 Yannick Young 传话筒

🔒 温馨提示

- 请勿发送违法、违规或骚扰信息
- 若多次滥用，可能会被拉黑屏蔽

感谢你的理解与配合，祝沟通顺利！🙌"""
        en_text = """🤖 Welcome to Yannick Young’s Message Bot!

🔒 Note

- Please do not send illegal, abusive, or spam messages
- Repeated misuse may get you blocked

Thank you for your understanding and cooperation. Happy chatting! 🙌"""

        db.add(StartMessage(lang="zh", content=zh_text))
        db.add(StartMessage(lang="en", content=en_text))
        db.commit()

    db.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()