import pandas as pd
import joblib
import requests

# ── Model Yükleme ─────────────────────────────────────────────────────────────
model = joblib.load("model/xgboost_model.pkl")

def get_live_weather():
    """Open-Meteo API'sinden Ankara'nın anlık sıcaklık, rüzgar ve bulutluluk verisini çeker."""
    url = "https://api.open-meteo.com/v1/forecast?latitude=39.9208&longitude=32.8541&current=temperature_2m,windspeed_10m,cloudcover"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        sicaklik = data["current"]["temperature_2m"]
        ruzgar_ms = data["current"]["windspeed_10m"] / 3.6
        bulutluluk = data["current"]["cloudcover"]
        return sicaklik, ruzgar_ms, bulutluluk
    except Exception:
        return 25.0, 3.0, 20.0


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
    
    canli_sicaklik, canli_ruzgar, canli_bulutluluk = get_live_weather()

    # Gunes zenit acisi (SZA) saate gore yaklasik degerler:
    # Gece: 90 (gunes ufkun altinda), oglen: minimum (gunes en yukse)
    sza_saatlik = [
        90.0, 90.0, 90.0, 90.0, 90.0, 90.0,   # 00-05 gece
        88.0, 80.0, 70.0, 58.0, 47.0, 38.0,   # 06-11 sabah
        34.0, 38.0, 47.0, 58.0, 70.0, 80.0,   # 12-17 ogleden sonra
        88.0, 90.0, 90.0, 90.0, 90.0, 90.0,   # 18-23 aksam/gece
    ]

    girdi = pd.DataFrame({
        "T2M"      : [canli_sicaklik] * 24,
        "WS10M"    : [canli_ruzgar]   * 24,
        "Saat"     : list(range(24)),
        "Ay"       : [ay]         * 24,
        "CLOUD_AMT": [canli_bulutluluk] * 24,
        "SZA"      : sza_saatlik,
        "RH2M"     : [nem]        * 24,
    })

    # ── 2. Model ile Tahmin Al (W/m²) ────────────────────────────────────────
    isinim_tahmin = model.predict(girdi)          # güneş ışınımı (W/m²)

    # ── 3. Işınımı Enerji Üretimine Dönüştür (kWh) ───────────────────────────
    # Basit yaklaşım: Üretim ∝ ışınım × panel gücü / maksimum ışınım (1000 W/m²)
    # Her satır 1 saatlik dilimi temsil ettiğinden doğrudan kWh olarak yorumlanır.
    uretim_kw = (isinim_tahmin / 1000.0) * panel_gucu_kw
    
    # Bulutluluk cezası (Matematiksel simülasyon)
    bulut_cezasi = 1.0 - (canli_bulutluluk / 100.0) * 0.75
    uretim_kw = uretim_kw * bulut_cezasi

    uretim_kw = pd.Series(uretim_kw).clip(lower=0)            # negatif tahminleri sıfırla

    # ── 4. Sonuç DataFrame ───────────────────────────────────────────────────
    saatler = [f"{str(i).zfill(2)}:00" for i in range(24)]

    sonuc = pd.DataFrame({
        "saat"              : saatler,
        "isinim_wm2"        : isinim_tahmin.round(2),
        "beklenen_uretim_kw": uretim_kw.round(4),
    })

    return sonuc


def get_5_day_forecast():
    """Open-Meteo API'sinden Ankara'nın 5 günlük saatlik sıcaklık, rüzgar ve bulutluluk verisini çeker."""
    url = "https://api.open-meteo.com/v1/forecast?latitude=39.9208&longitude=32.8541&hourly=temperature_2m,windspeed_10m,cloudcover&forecast_days=5"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        zamanlar = data["hourly"]["time"][:120]
        sicakliklar = data["hourly"]["temperature_2m"][:120]
        # km/h'yi m/s'ye çevir
        ruzgarlar = [w / 3.6 for w in data["hourly"]["windspeed_10m"][:120]]
        bulutluluk_oranlari = data["hourly"]["cloudcover"][:120]
        
        return zamanlar, sicakliklar, ruzgarlar, bulutluluk_oranlari
    except Exception:
        # Hata durumunda varsayılan veri (120 saatlik)
        now = pd.Timestamp.now().floor('h') # 'H' yerine 'h' kullanildi
        zamanlar = [(now + pd.Timedelta(hours=i)).strftime("%Y-%m-%dT%H:00") for i in range(120)]
        return zamanlar, [25.0]*120, [3.0]*120, [20.0]*120


def predict_solar_weekly(panel_gucu_kw: float = 5.0):
    """
    API'den 120 saatlik (5 günlük) hava durumunu alarak saatlik güneş enerjisi tahmini yapar.
    """
    zamanlar, sicakliklar, ruzgarlar, bulutluluk_oranlari = get_5_day_forecast()
    
    zaman_dt = pd.to_datetime(zamanlar)
    saatler = zaman_dt.hour
    aylar = zaman_dt.month
    tarihler = zaman_dt.strftime("%Y-%m-%d")
    
    sza_saatlik = [
        90.0, 90.0, 90.0, 90.0, 90.0, 90.0,   # 00-05 gece
        88.0, 80.0, 70.0, 58.0, 47.0, 38.0,   # 06-11 sabah
        34.0, 38.0, 47.0, 58.0, 70.0, 80.0,   # 12-17 ogleden sonra
        88.0, 90.0, 90.0, 90.0, 90.0, 90.0,   # 18-23 aksam/gece
    ]
    
    sza_120 = [sza_saatlik[h] for h in saatler]
    
    girdi = pd.DataFrame({
        "T2M"      : sicakliklar,
        "WS10M"    : ruzgarlar,
        "Saat"     : saatler,
        "Ay"       : aylar,
        "CLOUD_AMT": bulutluluk_oranlari,
        "SZA"      : sza_120,
        "RH2M"     : [60.0] * 120,  # Varsayılan nem
    })
    
    isinim_tahmin = model.predict(girdi)
    
    uretim_kw = (isinim_tahmin / 1000.0) * panel_gucu_kw
    
    # Bulutluluk cezası (Matematiksel simülasyon)
    bulut_cezasi = 1.0 - (pd.Series(bulutluluk_oranlari) / 100.0) * 0.75
    uretim_kw = uretim_kw * bulut_cezasi
    
    uretim_kw = pd.Series(uretim_kw).clip(lower=0)
    
    sonuc = pd.DataFrame({
        "tarih"             : tarihler,
        "saat"              : [f"{str(h).zfill(2)}:00" for h in saatler],
        "beklenen_uretim_kw": uretim_kw.round(4)
    })
    
    return sonuc


# ── Hızlı Test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=== Günlük Tahmin Testi ===")
    test_tarihi = "2025-06-15"
    tahmin_gunluk = predict_solar(tarih=test_tarihi, sicaklik=28.0, ruzgar=3.0,
                           bulutluluk=15.0, nem=45.0, panel_gucu_kw=5.0)

    print(f"{test_tarihi} icin saatlik gunes enerjisi tahmini (ilk 5 saat):\n")
    print(tahmin_gunluk.head().to_string(index=False))
    print(f"\nGunluk Toplam Uretim: {tahmin_gunluk['beklenen_uretim_kw'].sum():.2f} kWh\n")
    
    print("=== Haftalık (120 Saat) Tahmin Testi ===")
    tahmin_haftalik = predict_solar_weekly(panel_gucu_kw=5.0)
    print("5 gunluk tahminin ilk 5 saati:")
    print(tahmin_haftalik.head().to_string(index=False))
    print(f"Toplam Satır Sayısı: {len(tahmin_haftalik)}")
    print(f"5 Günlük Toplam Üretim: {tahmin_haftalik['beklenen_uretim_kw'].sum():.2f} kWh")
