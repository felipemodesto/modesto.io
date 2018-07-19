from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
Heartrate = Table('Heartrate', post_meta,
    Column('ip', Integer),
    Column('time', DateTime),
    Column('heartrate', Integer),
    Column('accuracy', Integer),
    Column('deviceID', String(length=64), primary_key=True, nullable=False),
    Column('deviceHash', String(length=64)),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['Heartrate'].columns['accuracy'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['Heartrate'].columns['accuracy'].drop()
