import dtale
import pandas as pd
import sys
import os



df = pd.read_csv(sys.argv[1])
d = dtale.show(df)
d.open_browser()

#ENV = os.getenv

while(True):
	pass

# delete the csv
