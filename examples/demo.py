import random

import duckdb
import fastparquet
import pandas as pd
from faker import Faker

NUM_PEOPLE = 10

fake = Faker()

def get_person():
  return {
    'name': fake.name(),
    'age': random.randint(0, 100),
    'email': fake.email(),
    'company': fake.company(),
    'phone': fake.phone_number(),
  }


df = pd.DataFrame.from_dict([get_person() for _ in range(NUM_PEOPLE)])


con = duckdb.connect()
con.execute("CREATE TABLE persons AS SELECT * FROM df")

new_df = con.execute("SELECT * FROM persons LIMIT 10").fetchdf()
print(new_df)

fastparquet.write('outfile.parquet', df)
