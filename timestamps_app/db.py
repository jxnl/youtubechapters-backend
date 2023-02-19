import os

import sqlalchemy as sa

url = os.environ["DB_URL"]
engine = sa.create_engine(url=url, connect_args={"sslmode": "require"})
