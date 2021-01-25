

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session


def get_session():
    bind = op.get_bind()
    return Session(bind=bind)
