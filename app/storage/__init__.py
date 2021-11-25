from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.settings import APP_CONF

engine = create_engine(APP_CONF.db.conn_string, echo=True)
Session = sessionmaker(bind=engine)
session = Session()
