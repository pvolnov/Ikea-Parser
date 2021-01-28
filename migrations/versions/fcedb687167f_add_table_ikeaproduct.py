"""Add table IkeaProduct

Revision ID: fcedb687167f
Revises: 1c7c939406a4
Create Date: 2021-01-24 22:04:36.682129

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'fcedb687167f'
down_revision = '1c7c939406a4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('ikeaproduct',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('url', sa.String(length=300), nullable=False),
                    sa.Column('code', sa.String(length=50), nullable=False),
                    sa.Column('raw_data', sa.JSON(), nullable=True),
                    sa.Column('translated_data', sa.JSON(), nullable=True),
                    sa.Column('is_failed', sa.Boolean(), server_default=sa.text('false'), nullable=True),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('code'),
                    sa.UniqueConstraint('url')
                    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('ikeaproduct')
    # ### end Alembic commands ###