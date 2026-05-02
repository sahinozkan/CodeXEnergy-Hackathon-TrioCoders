from fastapi import FastAPI, HTTPException
import pandas as pd
import os

app = FastAPI(
    title="Energy Hackathon API", 
    description="A basic template API serving the Smart Grid dataset."
)

# Bu dosyadan verisetinin göreceli(relative) yolunu belirt
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "datasets", "Ankara_Solar.csv")

# Başlangıçta verisetini yükle
try:
    df = pd.read_csv(DATA_PATH)
except Exception as e:
    print(f"Failed to load dataset: {e}")
    df = pd.DataFrame()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Energy Hackathon API Starter!"}

@app.get("/data")
def get_data(limit: int = 10, skip: int = 0):
    """
    Get a subset of the dataset.
    """
    if df.empty:
        raise HTTPException(status_code=500, detail="Data could not be loaded.")
    
    # Sayfalandırılmış veriyi döndür
    subset = df.iloc[skip : skip + limit]
    return subset.to_dict(orient="records")

@app.get("/data/summary")
def get_data_summary():
    """
    Get basic descriptive statistics of the dataset.
    """
    if df.empty:
        raise HTTPException(status_code=500, detail="Data could not be loaded.")
    
    return df.describe().to_dict()

if __name__ == "__main__":
    import uvicorn
    # Serveri çalıştır
    uvicorn.run(app, host="0.0.0.0", port=8000)
