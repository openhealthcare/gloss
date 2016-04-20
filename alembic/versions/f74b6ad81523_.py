"""empty message

Revision ID: f74b6ad81523
Revises: 6c9ec3813c7a
Create Date: 2016-04-19 17:22:52.606757

"""

# revision identifiers, used by Alembic.
revision = 'f74b6ad81523'
down_revision = '6c9ec3813c7a'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(u'merge_old_reference_id_fkey', 'merge', type_='foreignkey')
    op.drop_column('merge', 'old_reference_id')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('merge', sa.Column('old_reference_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.create_foreign_key(u'merge_old_reference_id_fkey', 'merge', 'glossolaliareference', ['old_reference_id'], ['id'])
    ### end Alembic commands ###
