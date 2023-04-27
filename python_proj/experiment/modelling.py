

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import pandas as pd 
from sys import argv


file_name =  argv[argv.index('-i') + 1]
data_path = f'./data/libraries/npm-libraries-1.6.0-2020-01-12/pull-requests/{file_name}.csv'
df = pd.read_csv(filepath_or_buffer=data_path, header=0)

train, test = train_test_split(df, test_size=0.2)

print(f'Training with {len(train)} entries, and testing with {len(test)} entries.')




