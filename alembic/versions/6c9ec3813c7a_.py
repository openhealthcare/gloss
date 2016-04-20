"""empty message

Revision ID: 6c9ec3813c7a
Revises: 440bea99abd6
Create Date: 2016-04-19 15:54:50.394941

"""

# revision identifiers, used by Alembic.
revision = '6c9ec3813c7a'
down_revision = '440bea99abd6'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from gloss.models import Merge


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('merge', sa.Column('new_reference_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'merge', 'glossolaliareference', ['new_reference_id'], ['id'])
    connection = op.get_bind()
    Session = sa.orm.sessionmaker()
    session = Session(bind=connection)
    all_merges = session.query(Merge).all()

    for merge in all_merges:
        merge.new_reference_id = merge.gloss_reference_id
        merge.gloss_reference_id = merge.old_reference_id
        session.add(merge)
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    Session = sa.orm.sessionmaker()
    connection = op.get_bind()
    session = Session(bind=connection)
    all_merges = session.query(Merge).all()

    for merge in all_merges:
        merge.gloss_reference_id = merge.new_reference_id
        session.add(merge)
    op.drop_column('merge', 'new_reference_id')
    ### end Alembic commands ###
