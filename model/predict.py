import pandas as pd
import joblib

# ── Model Yükleme ─────────────────────────────────────────────────────────────
model = joblib.load("model/xgboost_model.pkl")


def predict_solar(tarih: str, sicaklik: float = 15.0, ruzgar: float = 2.5,
                  bulutluluk: float = 20.0, nem: float = 60.0,
                  panel_gucu_kw: float = 5.0):
    """
    Verilen tarihe gore saatlik gunes enerjisi uretim tahmini yapar.

    Parametreler
    ------------
    tarih        : "YYYY-MM-DD" formatinda tahmin yapilacak gun (orn. "2025-06-15")
    sicaklik     : Ortalama sicaklik (C). Varsayilan: 15.0
    ruzgar       : Ortalama ruzgar hizi (m/s). Varsayilan: 2.5
    bulutluluk   : Bulutluluk orani (%). Varsayilan: 20.0 (az bulutlu)
    nem          : Bagil nem (%). Varsayilan: 60.0
    panel_gucu_kw: Kurulu panel gucu (kW). Varsayilan: 5.0

    Dondurur
    --------
    pd.DataFrame : 'saat', 'isinim_wm2', 'beklenen_uretim_kw' sutunlari
    """

    # ── 1. 24 Saatlik Girdi Tablosu Olustur ──────────────────────────────────
    ay = pd.to_datetime(tarih).month

    # Gunes zenit acisi (SZA) saate gore yaklasik degerler:
    # Gece: 90 (gunes ufkun altinda), oglen: minimum (gunes en yukse)
    sza_saatlik = [
        90.0, 90.0, 90.0, 90.0, 90.0, 90.0,   # 00-05 gece
        88.0, 80.0, 70.0, 58.0, 47.0, 38.0,   # 06-11 sabah
        34.0, 38.0, 47.0, 58.0, 70.0, 80.0,   # 12-17 ogleden sonra
        88.0, 90.0, 90.0, 90.0, 90.0, 90.0,   # 18-23 aksam/gece
    ]

    girdi = pd.DataFrame({
        "T2M"      : [sicaklik]   * 24,
        "WS10M"    : [ruzgar]     * 24,
        "Saat"     : list(range(24)),
        "Ay"       : [ay]         * 24,
        "CLOUD_AMT": [bulutluluk] * 24,
        "SZA"      : sza_saatlik,
        "RH2M"     : [nem]        * 24,
    })

    # ── 2. Model ile Tahmin Al (W/m²) ────────────────────────────────────────
    isinim_tahmin = model.predict(girdi)          # güneş ışınımı (W/m²)

    # ── 3. Işınımı Enerji Üretimine Dönüştür (kWh) ───────────────────────────
    # Basit yaklaşım: Üretim ∝ ışınım × panel gücü / maksimum ışınım (1000 W/m²)
    # Her satır 1 saatlik dilimi temsil ettiğinden doğrudan kWh olarak yorumlanır.
    uretim_kw = (isinim_tahmin / 1000.0) * panel_gucu_kw
    uretim_kw = uretim_kw.clip(min=0)            # negatif tahminleri sıfırla

    # ── 4. Sonuç DataFrame ───────────────────────────────────────────────────
    saatler = [f"{str(i).zfill(2)}:00" for i in range(24)]

    sonuc = pd.DataFrame({
        "saat"              : saatler,
        "isinim_wm2"        : isinim_tahmin.round(2),
        "beklenen_uretim_kw": uretim_kw.round(4),
    })

    return sonuc


# ── Hızlı Test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    test_tarihi = "2025-06-15"
    tahmin = predict_solar(tarih=test_tarihi, sicaklik=28.0, ruzgar=3.0,
                           bulutluluk=15.0, nem=45.0, panel_gucu_kw=5.0)

    print(f"{test_tarihi} icin saatlik gunes enerjisi tahmini:\n")
    print(tahmin.to_string(index=False))
    print(f"\nGunluk Toplam Uretim: {tahmin['beklenen_uretim_kw'].sum():.2f} kWh")
