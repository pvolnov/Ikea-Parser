from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import ARRAY, BigInteger, Boolean, Column, Integer, JSON, Text, text, String
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv, find_dotenv
import os
from contextlib import contextmanager

load_dotenv()

DB_URL = os.environ['DB_URL']
engine = create_engine(DB_URL, convert_unicode=True)
Session = sessionmaker(autocommit=False,
                       autoflush=False,
                       bind=engine)

Base = declarative_base()

current_session = scoped_session(Session)

@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


class Ikeaitem(Base):
    __tablename__ = 'ikeaitems'

    id = Column(Integer, primary_key=True)
    code = Column(Integer, nullable=False, unique=True)
    url = Column(Text, nullable=False, unique=True)
    name = Column(Text, nullable=False, default='')
    search = Column(Text, nullable=False, default='')
    discr = Column(Text, nullable=False, default='')
    price = Column(Text, nullable=False, default='')
    ukr_price = Column(Text, nullable=False, default='')
    avilable = Column(Text, nullable=False, default='')
    tags = Column(ARRAY(Text()), nullable=False, index=True, default=["", ""])
    image = Column(Text, nullable=False)
    group_id = Column(Integer, nullable=False)
    subgroup_id = Column(Integer, nullable=False)
    new = Column(Boolean, nullable=False)
    correct = Column(Boolean, nullable=False)


class IkeaProduct(Base):
    __tablename__ = 'ikeaproduct'

    id = Column(Integer, primary_key=True)
    url = Column(String(300), nullable=False, unique=True)
    code = Column(String(50), nullable=False, unique=False)
    country = Column(String(5), nullable=False)
    data = Column(JSON, nullable=True, default=None)
    ru_data = Column(JSON, nullable=True, default=None)
    pl_data = Column(JSON, nullable=True, default=None)
    ua_data = Column(JSON, nullable=True, default=None)
    is_failed = Column(Boolean, server_default=text("false"))


class Plikeaitem(Base):
    __tablename__ = 'plikeaitems'

    id = Column(Integer, primary_key=True, server_default=text("nextval('plikeaitems_id_seq'::regclass)"))
    url = Column(Text, nullable=False)
    code = Column(Text, nullable=False, unique=True)
    data = Column(JSON, nullable=False)
    tags = Column(ARRAY(Text()), nullable=False, index=True)
    loaded = Column(Boolean, nullable=False)
    avilable_updated = Column(Boolean, nullable=False)
    avilable = Column(Boolean, nullable=False)
    is_translated = Column(Boolean, nullable=False, server_default=text("true"))
    is_failed = Column(Boolean, server_default=text("false"))


class Uaikeaitem(Base):
    __tablename__ = 'uaikeaitems'

    id = Column(Integer, primary_key=True, server_default=text("nextval('uaikeaitems_id_seq'::regclass)"))
    url = Column(Text, nullable=False)
    code = Column(Text, nullable=False, unique=True)
    data = Column(JSON, nullable=False)
    tags = Column(ARRAY(Text()), nullable=False, index=True)
    loaded = Column(Boolean, nullable=False)
    avilable = Column(Boolean, nullable=False)
    avilable_updated = Column(Boolean, nullable=False)
    is_translated = Column(Boolean, server_default=text("true"))
    is_failed = Column(Boolean, server_default=text("false"))


class Post(Base):
    __tablename__ = 'posts'

    id = Column(Integer, primary_key=True, server_default=text("nextval('posts_id_seq'::regclass)"))
    item_id = Column(BigInteger, nullable=False, unique=True)
    info = Column(JSON, nullable=False)
    history = Column(ARRAY(Text()), nullable=False, index=True)


class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True, server_default=text("nextval('tasks_id_seq'::regclass)"))
    url = Column(Text, nullable=False, unique=True)
    updted = Column(Boolean, nullable=False)
    loaded = Column(Boolean, nullable=False)


class Tguser(Base):
    __tablename__ = 'tgusers'

    id = Column(Integer, primary_key=True, server_default=text("nextval('tgusers_id_seq'::regclass)"))
    tel_id = Column(BigInteger, nullable=False, unique=True)
    mst = Column(Text, nullable=False)
