"""
CarbonZero AI Asistan Modulu
==============================
Bu modul, Gemini LLM entegrasyonunu ve gercek ML tahmin
verileriyle enerji uretim tavsiyelerini yonetir.
model/predict.py icerisindeki predict_solar fonksiyonunu
kullanarak kullanicilara akilli oneriler sunar.
"""

import os
import sys
import pandas as pd
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

try:
    from google import genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

# -- Proje kok dizinini sys.path'e ekle (model/ importu icin) ---------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from model.predict import predict_solar

# -- .env dosyasindan API anahtarini yukle ----------------------------------
env_path = os.path.join(PROJECT_ROOT, ".env")
load_dotenv(dotenv_path=env_path)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GLOBAL_CLIENT = None
if HAS_GENAI and GEMINI_API_KEY:
    try:
        GLOBAL_CLIENT = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"Gemini Client baslatilamadi: {e}")


# ---------------------------------------------------------------------------
#  Yardimci Fonksiyon: ML Tahmin Verisini Al
# ---------------------------------------------------------------------------
def get_solar_prediction(
    tarih: str,
    sicaklik: float = 28.0,
    ruzgar: float = 3.0,
    bulutluluk: float = 15.0,
    nem: float = 45.0,
    panel_gucu_kw: float = 5.0,
) -> pd.DataFrame:
    """
    predict_solar fonksiyonunu cagirip DataFrame olarak dondurur.
    Debug ve Streamlit goruntuleme icin kullanilir.

    Returns:
        pd.DataFrame: 'saat', 'isinim_wm2', 'beklenen_uretim_kw' kolonlari.
    """
    return predict_solar(
        tarih=tarih,
        sicaklik=sicaklik,
        ruzgar=ruzgar,
        bulutluluk=bulutluluk,
        nem=nem,
        panel_gucu_kw=panel_gucu_kw,
    )


# ---------------------------------------------------------------------------
#  Ana Sinif: CarbonZero AI Asistani
# ---------------------------------------------------------------------------
class CarbonZeroAssistant:
    """
    CarbonZero Yapay Zeka Asistani.

    Gercek ML tahmin verileriyle gunes enerjisi uretimini analiz eder
    ve Gemini LLM destekli tavsiyeler sunar.
    """

    def __init__(self):
        """Asistani baslat."""
        self.client = GLOBAL_CLIENT
        self.model_name = "gemini-2.0-flash"

    def generate_advice(self, df: pd.DataFrame, secilen_tarih: str = "Bugün", bulutluluk: float = 15.0) -> str:
        """
        DataFrame'deki zirve saatini bulup LLM destekli tavsiye uretir.

        Args:
            df (pd.DataFrame): predict_solar() ciktisi.
                Kolonlar: 'saat', 'beklenen_uretim_kw'
            secilen_tarih (str): Kullanıcının incelediği tarih.
            bulutluluk (float): O gunun bulutluluk orani. Yedek sistem icin.

        Returns:
            str: Gemini modelinden donen motive edici tavsiye metni.
        """
        # -- Kolon kontrolu --------------------------------------------------
        gerekli_kolonlar = ["saat", "beklenen_uretim_kw"]
        for kolon in gerekli_kolonlar:
            if kolon not in df.columns:
                return f"[HATA] DataFrame'de '{kolon}' kolonu bulunamadi. Mevcut kolonlar: {list(df.columns)}"

        # -- Zirve saatini bul -----------------------------------------------
        zirve_satir = df.loc[df["beklenen_uretim_kw"].idxmax()]
        saat = zirve_satir["saat"]
        beklenen_uretim_kw = round(float(zirve_satir["beklenen_uretim_kw"]), 2)

        # -- Gunluk toplam uretim --------------------------------------------
        toplam_kwh = round(float(df["beklenen_uretim_kw"].sum()), 2)

        # -- Engellenen karbon hesapla ---------------------------------------
        # Sebekeden cekilmeyen her 1 kWh = 0.4 kg CO2 kurtarir
        co2_kg = round(toplam_kwh * 0.4, 2)

        # -- Sistem rolu ve kullanici promptunu olustur ----------------------
        sistem_rolu = (
            "Sen CarbonZero AI adinda cevreci ve akilli bir ev enerjisi "
            "asistanisin. Yanitlarin cok kisa (maksimum 2-3 cumle), "
            "motive edici, samimi ve dogrudan eyleme yonelik olmali. "
            "Ciktida gereksiz uzatmalar yapma."
        )

        kullanici_promptu = (
            f"Kullanici {secilen_tarih} tarihinde toplam {toplam_kwh} kWh gunes enerjisi uretecek. "
            f"Zirve saati {saat}'te {beklenen_uretim_kw} kW ile en yuksek uretim olacak. "
            f"Gunluk toplam {co2_kg} kg CO2 salinimi engellenecek. "
            f"Kullaniciya camasir, bulasik makinesi veya elektrikli aracini "
            f"o gun {saat} civari calistirmasi icin motive edici, cevreci bir bildirim yaz. "
            f"Mesajda bu spesifik tarihi ({secilen_tarih}) de kullaniciya hissettir."
        )

        # -- Gemini API cagrisi (google-genai SDK) ---------------------------
        if self.client:
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=f"{sistem_rolu}\n\n{kullanici_promptu}",
                )
                return response.text
            except Exception as e:
                print(f"API Hatasi (Sistemi durdurmadik): {e}")

        # -- AKILLI YEDEK SISTEM (FALLBACK) --
        if bulutluluk > 50.0:
            # Hava cok kapaliyken
            sahte_cevap = (
                f"☁️ **Bugün hava kapalı, tasarruf moduna geçin!**\n\n"
                f"Panellerin maksimum **{beklenen_uretim_kw} kW** üretim ile "
                f"saat **{saat}**'te zirve yapacak. Ancak bulutlu hava sebebiyle "
                f"günlük toplam üretim **{toplam_kwh} kWh**'da kalacak.\n\n"
                f"**Şimdi yapabileceklerin:**\n"
                f"- ⏳ Ağır cihazları (çamaşır, kurutma) {secilen_tarih} yerine daha güneşli bir güne ertele\n"
                f"- 💡 Sadece gerekli elektrikli aletleri kullan"
            )
        elif beklenen_uretim_kw >= 4.0:
            # Hava cok iyi, uretim tavan
            sahte_cevap = (
                f"☀️ **Harika bir güneş var, tüm ağır cihazları çalıştırabilirsiniz!**\n\n"
                f"{secilen_tarih} tarihinde Saat **{saat}**'te üretim tam **{beklenen_uretim_kw} kW** ile tavan yapacak!\n"
                f"Bugün şebekeden çekmeyerek **{co2_kg} kg CO2** tasarrufu sağlıyoruz. 🌍💚\n\n"
                f"**Şimdi yapabileceklerin:**\n"
                f"- 🧺 Çamaşır ve bulaşık makinesini ayni anda çalıştır\n"
                f"- 🚗 Elektrikli aracını hızlı şarja tak"
            )
        elif beklenen_uretim_kw >= 1.90:
            # Orta seviye uretim
            sahte_cevap = (
                f"⚡ **Ortalama ve verimli bir güneş günü!**\n\n"
                f"{secilen_tarih} tarihi Saat **{saat}** civarında paneller **{beklenen_uretim_kw} kW** gücünde üretim sağlayacak.\n"
                f"Günlük **{toplam_kwh} kWh** enerjin var, **{co2_kg} kg CO2** engelleniyor. 📊\n\n"
                f"**Öneriler:**\n"
                f"- 🧺 Tek bir ağır makineyi (örneğin çamaşır makinesi) çalıştır\n"
                f"- 🏠 Orta tüketimli cihazlarını (süpürge vs.) bu saatlerde kullan"
            )
        else:
            # Genel dusuk uretim
            sahte_cevap = (
                f"📉 **Bugün gücümüz biraz sınırlı.**\n\n"
                f"{secilen_tarih} tarihi en iyi saatinde (**{saat}**) bile üretim "
                f"**{beklenen_uretim_kw} kW** seviyesinde kalacak.\n\n"
                f"**Öneriler:**\n"
                f"- 🔋 Varsa ev bataryalarını idareli kullan\n"
                f"- 💡 Zorunlu işlerini saat {saat}'e planla, diğerlerini yarına ertele"
            )

        return sahte_cevap

    def generate_weekly_advice(self, en_iyi_gun_ismi: str, en_iyi_gun_uretim: float) -> str:
        """
        Haftalık analiz için Gemini'den tavsiye üretir.
        """
        sistem_rolu = (
            "Sen CarbonZero AI adinda cevreci ve akilli bir ev enerjisi "
            "asistanisin. Yanitlarin cok kisa (maksimum 2-3 cumle), "
            "motive edici, samimi ve dogrudan eyleme yonelik olmali."
        )

        kullanici_promptu = (
            f"Sistemimiz önümüzdeki 5 günü analiz etti. En yüksek üretim {en_iyi_gun_ismi} günü "
            f"{en_iyi_gun_uretim:.1f} kWh ile gerçekleşecek. Lütfen kullanıcıya bu özel günü "
            f"vurgulayan, ağır beyaz eşyalarını o güne saklamasını öneren, hem doğayı hem "
            f"cebini koruduğunu hissettiren samimi bir tavsiye mesajı oluştur."
        )

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=f"{sistem_rolu}\n\n{kullanici_promptu}",
            )
            return response.text
        except Exception as e:
            print(f"API Hatasi (Sistemi durdurmadik): {e}")
            return (
                f"Sistemimiz önümüzdeki 5 günü analiz etti. En yüksek üretim {en_iyi_gun_ismi} günü "
                f"{en_iyi_gun_uretim:.1f} kWh ile gerçekleşecek. Doğayı ve cebinizi korumak için "
                f"ağır beyaz eşyalarınızı o güne planlayabilirsiniz!"
            )


# ---------------------------------------------------------------------------
#  Streamlit / Dis Kullanim icin Tek Fonksiyon
# ---------------------------------------------------------------------------
def generate_advice_for_date(
    tarih: str,
    sicaklik: float = 28.0,
    ruzgar: float = 3.0,
    bulutluluk: float = 15.0,
    nem: float = 45.0,
    panel_gucu_kw: float = 5.0,
) -> str:
    """
    Tek satirda ML tahmini + LLM tavsiyesi uretir.
    Streamlit tarafindan dogrudan cagirilabilir.

    Args:
        tarih: "YYYY-MM-DD" formatinda tarih.
        sicaklik: Ortalama sicaklik (C).
        ruzgar: Ortalama ruzgar hizi (m/s).
        bulutluluk: Bulutluluk orani (%).
        nem: Bagil nem (%).
        panel_gucu_kw: Kurulu panel gucu (kW).

    Returns:
        str: Kullaniciya gosterilecek tavsiye metni.
    """
    # 1) ML tahminini al
    df = predict_solar(
        tarih=tarih,
        sicaklik=sicaklik,
        ruzgar=ruzgar,
        bulutluluk=bulutluluk,
        nem=nem,
        panel_gucu_kw=panel_gucu_kw,
    )

    # 2) LLM tavsiyesi uret
    asistan = CarbonZeroAssistant()
    return asistan.generate_advice(df, bulutluluk=bulutluluk)

def generate_weekly_advice_for_app(en_iyi_gun_ismi: str, en_iyi_gun_uretim: float) -> str:
    """
    Haftalık analiz için LLM tavsiyesi üretir.
    Streamlit tarafindan dogrudan cagirilabilir.
    """
    asistan = CarbonZeroAssistant()
    return asistan.generate_weekly_advice(en_iyi_gun_ismi, en_iyi_gun_uretim)

def generate_advice_for_dataframe(df: pd.DataFrame, tarih: str) -> str:
    """
    Hazır DataFrame'i ve tarihi kullanarak Gemini'den tavsiye alır.
    """
    asistan = CarbonZeroAssistant()
    return asistan.generate_advice(df, secilen_tarih=tarih)

# ---------------------------------------------------------------------------
#  Test Blogu
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("  CarbonZero AI Asistan - Gercek ML Entegrasyonu Testi")
    print("=" * 60)

    test_tarihi = "2025-06-15"

    # 1) ML tahmin verisini al
    print(f"\n[ML] predict_solar('{test_tarihi}') cagriliyor...")
    df = get_solar_prediction(
        tarih=test_tarihi,
        sicaklik=28.0,
        ruzgar=3.0,
        bulutluluk=15.0,
        nem=45.0,
        panel_gucu_kw=5.0,
    )
    print(f"\n[DATA] Saatlik Gunes Uretim Tahmini:")
    print(df.to_string(index=False))

    # 2) Ozet istatistikler
    toplam = round(float(df["beklenen_uretim_kw"].sum()), 2)
    zirve = df.loc[df["beklenen_uretim_kw"].idxmax()]
    karbon = round(toplam * 0.4, 2)
    print(f"\n[OZET] Gunluk toplam uretim: {toplam} kWh")
    print(f"[ZIRVE] En yuksek: {zirve['saat']} -> {round(float(zirve['beklenen_uretim_kw']), 2)} kW")
    print(f"[CO2] Engellenen karbon: {karbon} kg")

    # 3) LLM tavsiyesi
    print("\n[AI] Gemini'den tavsiye isteniyor...")
    tavsiye = generate_advice_for_date(tarih=test_tarihi, sicaklik=28.0,
                                        ruzgar=3.0, bulutluluk=15.0,
                                        nem=45.0, panel_gucu_kw=5.0)
    print(f"\n[SONUC] AI Tavsiyesi:")
    print(f"   {tavsiye}")
