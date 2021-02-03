from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import ARRAY, BigInteger, Boolean, Column, Integer, JSON, Text, text, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
import datetime
from dotenv import load_dotenv, find_dotenv
import os
from contextlib import contextmanager
from sqlalchemy_mixins import ActiveRecordMixin, ReprMixin, TimestampsMixin, SerializeMixin

import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import scoped_session, sessionmaker

load_dotenv()

DB_URL = os.environ['DB_URL']

Base = declarative_base()


class BaseModel(Base, ActiveRecordMixin, ReprMixin, TimestampsMixin, SerializeMixin):
    __abstract__ = True
    __repr__ = ReprMixin.__repr__


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


class IkeaProduct(BaseModel):
    __tablename__ = 'ikeaproduct'

    id = Column(Integer, primary_key=True)
    create_date = Column(DateTime, default=datetime.datetime.utcnow)
    url = Column(String(300), nullable=False, unique=True)
    code = Column(String(50), nullable=False, unique=False)
    country = Column(String(5), nullable=False)
    data = Column(JSON, nullable=True)
    ru_data = Column(JSON(none_as_null=True), nullable=True)
    pl_data = Column(JSON(none_as_null=True), nullable=True)
    ua_data = Column(JSON(none_as_null=True), nullable=True)
    is_available = Column(Boolean, nullable=True)
    is_failed = Column(Boolean, default=False)
    is_new = Column(Boolean, default=True)


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


engine = create_engine(DB_URL, convert_unicode=True, echo=False)
Session = scoped_session(sessionmaker(autocommit=False,
                                      autoflush=False,
                                      expire_on_commit=False,
                                      bind=engine))

# Base.metadata.create_all(engine)

BaseModel.set_session(Session)


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
