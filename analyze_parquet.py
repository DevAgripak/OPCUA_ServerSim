import pandas as pd
import os

# Leggi il file parquet
file_path = 'variables/CI2306-P01_2026-03-01.parquet'
if os.path.exists(file_path):
    df = pd.read_parquet(file_path)
    print("--- Dtypes ---")
    print(df.dtypes)
    print("\n--- Prima riga ---")
    print(df.head(1).to_dict(orient='records'))
    
    # Calcola min/max per le colonne numeriche per avere un'idea del range per i dati random
    print("\n--- Statistiche (min/max) ---")
    stats = df.describe().loc[['min', 'max']]
    print(stats)
else:
    print(f"File non trovato: {file_path}")
