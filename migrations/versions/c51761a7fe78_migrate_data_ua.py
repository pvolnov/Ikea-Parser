"""migrate data

Revision ID: c51761a7fe78
Revises: fcedb687167f
Create Date: 2021-01-24 22:11:37.013874

"""
from alembic import op
from sqlalchemy import orm
import os, sys

sys.path.append(os.getcwd())
from app.db import IkeaProduct, Uaikeaitem
from migrations.utils import get_session
from tqdm import trange
from sqlalchemy import Column, JSON

# revision identifiers, used by Alembic.
revision = 'c51761a7fe78'
down_revision = '9f36279c4638'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('ikeaproduct', 'translated_data')
    session = get_session()
    count = session.query(Uaikeaitem).count()
    bunch = 30
    for i in trange(0, count + bunch, bunch):
        items = session.query(Uaikeaitem).offset(i).limit(bunch).all()
        products = []
        for item in items:
            data = item.data
            data['tags'] = item.tags
            ua_data = data
            ru_data = None
            if item.is_translated:
                ru_data, ua_data = ua_data, ru_data
            products.append(
                {
                    'url': item.url,
                    'code': item.code,
                    'ua_data': ua_data,
                    'ru_data': ru_data,
                    'is_failed': item.is_failed,
                    'country': 'UA'
                }
            )
        op.bulk_insert(
            IkeaProduct.__table__,
            products
        )


def downgrade():
    op.add_column('ikeaproduct',
                  Column('translated_data', JSON, nullable=True, default=None))

    bind = op.get_bind()
    session = orm.Session(bind=bind)
    session.query(IkeaProduct).delete()
