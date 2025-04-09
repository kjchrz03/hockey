# %%
import pandas as pd

# Read all sheets into a dictionary of DataFrames
file_path = "C:\\Users\\kjcs2\\Desktop\\Jobs\\Abode\\abode_env\\abode_env\\Hancock Reconciliation Tool V1.xlsx"

sheets_dict = pd.read_excel(file_path, sheet_name=None)

# Access each sheet by its name
df_sheet1 = sheets_dict["HPC Cumulative Payments"]
df_sheet2 = sheets_dict["EVS - TrackSys"]
df_sheet3 = sheets_dict["NGRID - InDemand"]

df_sheet1.head()

# %%
