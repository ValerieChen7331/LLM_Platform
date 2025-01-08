import pandas as pd
from sqlalchemy import create_engine

engine = create_engine('sqlite:///CC17.db')
df = pd.read_excel(r"2022-W0NFCC17.xlsx")
df.to_sql('CC17', engine, index=False, if_exists='replace')