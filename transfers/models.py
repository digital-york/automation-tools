import os

from sqlalchemy import create_engine
from sqlalchemy import Sequence
from sqlalchemy import Column, Binary, Boolean, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import ConfigParser


# Read config file
automationToolsConfigFilePath = '/etc/archivematica/automation-tools/automation-tools.conf'
config = ConfigParser.SafeConfigParser()
config.read(automationToolsConfigFilePath)
databaseDirectory = config.get('automation-tools', 'databaseDirectory')

db_path = os.path.join(databaseDirectory, 'transfers.db')

engine = create_engine('sqlite:///{}'.format(db_path), echo=False)

Session = sessionmaker(bind=engine)
Base = declarative_base()

class Unit(Base):
    __tablename__ = 'unit'
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    uuid = Column(String(36))
    path = Column(Binary())
    unit_type = Column(String(10))  # ingest or transfer
    status = Column(String(20), nullable=True)
    microservice = Column(String(50))
    current = Column(Boolean(create_constraint=False))

    def __repr__(self):
        return "<Unit(id={s.id}, uuid={s.uuid}, unit_type={s.unit_type}, path={s.path}, status={s.status}, current={s.current})>".format(s=self)

Base.metadata.create_all(engine)
