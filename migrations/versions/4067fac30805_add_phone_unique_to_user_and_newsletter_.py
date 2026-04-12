"""add phone unique to user and newsletter subscriber

Revision ID: 4067fac30805
Revises: 258e6008cc86
Create Date: 2026-04-12 15:27:53.309411

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4067fac30805'
down_revision = '258e6008cc86'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('newsletter_subscribers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('phone', sa.String(length=20), nullable=True))
        batch_op.create_unique_constraint('uq_newsletter_phone', ['phone'])

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_users_phone', ['phone'])


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint('uq_users_phone', type_='unique')

    with op.batch_alter_table('newsletter_subscribers', schema=None) as batch_op:
        batch_op.drop_constraint('uq_newsletter_phone', type_='unique')
        batch_op.drop_column('phone')
