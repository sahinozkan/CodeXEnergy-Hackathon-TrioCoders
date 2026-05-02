import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import joblib
import numpy as np

# ── 1. Veriyi Oku ────────────────────────────────────────────────────────────
# İlk 15 satır meta-veri olduğundan atlanıyor (skiprows=15)
df = pd.read_csv("datasets/Ankara_Solar.csv", skiprows=15)

# ── 2. Eksik Ölçümleri Temizle ───────────────────────────────────────────────
# -999.0 değerleri eksik ölçümü temsil ediyor; önce pd.NA ile değiştir,
# ardından bir önceki saatin verisiyle doldur (forward fill)
df.replace(-999.0, pd.NA, inplace=True)
df.ffill(inplace=True)

# ── 3. Tarih Kolonu Oluştur ──────────────────────────────────────────────────
# YEAR, MO, DY, HR kolonlarını birleştirerek tek bir datetime kolonu yap
df["Tarih"] = pd.to_datetime(
    df["YEAR"].astype(str)
    + "-"
    + df["MO"].astype(str).str.zfill(2)
    + "-"
    + df["DY"].astype(str).str.zfill(2)
    + " "
    + df["HR"].astype(str).str.zfill(2)
    + ":00:00"
)

# ── 4. Eski Kolonları Sil ve İndex Ayarla ────────────────────────────────────
df.drop(columns=["YEAR", "MO", "DY", "HR"], inplace=True)
df.set_index("Tarih", inplace=True)

# ── 5. Doğrulama ─────────────────────────────────────────────────────────────
print("İlk 5 Satır:")
print(df.head())
print("\nVeri Seti Boyutu (satır, sütun):", df.shape)

# ── 6. Feature Engineering (Özellik Çıkarımı) ────────────────────────────────
df["Saat"] = df.index.hour
df["Ay"]   = df.index.month

# ── 7. Hedef ve Özellik Değişkenlerini Belirle ───────────────────────────────
y = df["ALLSKY_SFC_SW_DWN"]                          # Hedef: güneş ışınımı

# Iyilestirilmis feature seti:
#   CLOUD_AMT : bulutluluk orani - isinimi dogrudan etkiler (en guclu belirleyici)
#   SZA       : gunes zenit acisi - gunesin gokyuzundeki pozisyonu
#   RH2M      : bagil nem         - atmosferik gecirgenlik
X = df[["T2M", "WS10M", "Saat", "Ay", "CLOUD_AMT", "SZA", "RH2M"]]

# ── 8. Eğitim / Test Ayrımı ──────────────────────────────────────────────────
# Zaman serisi olduğu için shuffle=False ile sıra korunuyor
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, shuffle=False
)

# ── 9. Baseline Model (karsilastirma icin) ───────────────────────────────────
baseline = xgb.XGBRegressor()
baseline.fit(X_train[["T2M", "WS10M", "Saat", "Ay"]], y_train)
baseline_pred = baseline.predict(X_test[["T2M", "WS10M", "Saat", "Ay"]])
baseline_rmse = np.sqrt(mean_squared_error(y_test, baseline_pred))

# ── 10. Iyilestirilmis Model Egitimi ─────────────────────────────────────────
# Ayarlanan hiperparametreler:
#   n_estimators  : agac sayisi  - fazla agac daha iyi ogrenme saglar
#   max_depth     : agac derinligi - karmasik iliskileri yakalar
#   learning_rate : ogrenme hizi  - yavaş ama istikrarli ogrenme
#   subsample     : her agac icin kullanilan veri orani - asiri uyumu onler
#   colsample_bytree: her agac icin kullanilan feature orani
model = xgb.XGBRegressor(
    n_estimators     = 500,
    max_depth        = 6,
    learning_rate    = 0.05,
    subsample        = 0.8,
    colsample_bytree = 0.8,
    random_state     = 42,
)
model.fit(X_train, y_train)

# ── 11. Degerlendirme ve Karsilastirma ───────────────────────────────────────
y_pred = model.predict(X_test)
rmse   = np.sqrt(mean_squared_error(y_test, y_pred))

print(f"\nBaseline RMSE (4 feature) : {baseline_rmse:.4f} W/m2")
print(f"Iyilestirilmis RMSE (7 feature): {rmse:.4f} W/m2")
print(f"Kazanim : % {(1 - rmse / baseline_rmse) * 100:.1f} daha iyi")

# ── 12. Modeli Kaydet ────────────────────────────────────────────────────────
joblib.dump(model, "model/xgboost_model.pkl")
print("\nModel 'model/xgboost_model.pkl' olarak kaydedildi.")
