"""empty message

Revision ID: 27bcb4cd80c1
Revises: a7d445896d4a
Create Date: 2016-03-24 15:51:04.100137

"""

# revision identifiers, used by Alembic.
revision = '27bcb4cd80c1'
down_revision = 'a7d445896d4a'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.drop_table('inpatientlocation')
    op.drop_table('inpatientepisode')

    op.create_table('inpatientadmission',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('updated', sa.DateTime(), nullable=True),
    sa.Column('created', sa.DateTime(), nullable=True),
    sa.Column('datetime_of_admission', sa.DateTime(), nullable=False),
    sa.Column('datetime_of_discharge', sa.DateTime(), nullable=True),
    sa.Column('visit_number', sa.String(length=250), nullable=False),
    sa.Column('admission_diagnosis', sa.String(length=250), nullable=True),
    sa.Column('gloss_reference_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['gloss_reference_id'], ['glossolaliareference.id'], ),
    sa.PrimaryKeyConstraint('id')
    )

    op.create_table('inpatientlocation',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('updated', sa.DateTime(), nullable=True),
    sa.Column('created', sa.DateTime(), nullable=True),
    sa.Column('inpatient_admission_id', sa.Integer(), nullable=True),
    sa.Column('datetime_of_transfer', sa.DateTime(), nullable=True),
    sa.Column('ward_code', sa.String(length=250), nullable=True),
    sa.Column('room_code', sa.String(length=250), nullable=True),
    sa.Column('bed_code', sa.String(length=250), nullable=True),
    sa.ForeignKeyConstraint(['inpatient_admission_id'], ['inpatientadmission.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    ### end Alembic commands ###


def downgrade():
    op.drop_table('inpatientlocation')
    op.drop_table('inpatientadmission')

    op.create_table('inpatientepisode',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('updated', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('created', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('datetime_of_admission', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('datetime_of_discharge', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('visit_number', sa.VARCHAR(length=250), autoincrement=False, nullable=False),
    sa.Column('admission_diagnosis', sa.VARCHAR(length=250), autoincrement=False, nullable=True),
    sa.Column('gloss_reference_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['gloss_reference_id'], [u'glossolaliareference.id'], name=u'inpatientepisode_gloss_reference_id_fkey'),
    sa.PrimaryKeyConstraint('id', name=u'inpatientepisode_pkey')
    )
    op.create_table('inpatientlocation',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('updated', sa.DateTime(), nullable=True),
    sa.Column('created', sa.DateTime(), nullable=True),
    sa.Column('inpatient_episode_id', sa.Integer(), nullable=True),
    sa.Column('datetime_of_transfer', sa.DateTime(), nullable=True),
    sa.Column('ward_code', sa.String(length=250), nullable=True),
    sa.Column('room_code', sa.String(length=250), nullable=True),
    sa.Column('bed_code', sa.String(length=250), nullable=True),
    sa.ForeignKeyConstraint(['inpatient_episode_id'], ['inpatientepisode.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    ### end Alembic commands ###
