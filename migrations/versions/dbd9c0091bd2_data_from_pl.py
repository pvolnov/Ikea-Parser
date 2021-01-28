"""data from PL

Revision ID: dbd9c0091bd2
Revises: c51761a7fe78
Create Date: 2021-01-24 23:59:39.178185

Переносим данные из таблички по Польше

"""
from alembic import op
from migrations.utils import get_session
from app.db import Plikeaitem, IkeaProduct
from tqdm import trange
from sqlalchemy import orm
from sqlalchemy.dialects.postgresql import insert


# revision identifiers, used by Alembic.
revision = 'dbd9c0091bd2'
down_revision = 'c51761a7fe78'
branch_labels = None
depends_on = None


def upgrade():
    session = get_session()
    count = session.query(Plikeaitem).count()
    bunch = 50
    for i in trange(0, count, bunch):
        items = session.query(Plikeaitem).offset(i).limit(bunch).all()
        products = []
        for item in items:
            if not item.url or not item.data or not item.code:
                continue
            data = item.data
            data['tags'] = item.tags
            pl_data = data
            ru_data = None
            if item.is_translated:
                ru_data, pl_data = pl_data, ru_data
            products.append(
                {
                    'url': item.url,
                    'code': item.code,
                    'pl_data': pl_data,
                    'ru_data': ru_data,
                    'is_failed': item.is_failed,
                    'country': 'PL'
                }
            )
        query = insert(IkeaProduct).values(
            products
        ).on_conflict_do_nothing()
        session.execute(query)
        session.flush()


def downgrade():
    bind = op.get_bind()
    session = orm.Session(bind=bind)
    session.query(IkeaProduct).filter(IkeaProduct.country == 'PL').delete()

