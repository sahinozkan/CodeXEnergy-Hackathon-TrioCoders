import streamlit as st
import pandas as pd
import plotly.express as px
import time
from model.predict import predict_solar
from api_template.llm_asistan import generate_advice_for_date

# --- 1. SAYFA YAPILANDIRMASI (Jüri için profesyonel görünüm) ---
# st.set_page_config sayfanın ilk Streamlit komutu olmak zorundadır!
st.set_page_config(
    page_title="CodeXEnergy | Akıllı Çatı", 
    page_icon="☀️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Streamlit'in varsayılan menülerini gizleyerek pro-app hissiyatı verelim
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- 2. SAHTE VERİTABANI (Jüri Demosu İçin) ---
demo_kullanici = {
    "ad_soyad": "Yusuf",
    "telefon": "+90 555 123 4567",
    "lokasyon": "Ankara, Türkiye",
    "panel_gucu": 5.0
}

# --- 3. YAN MENÜ (Sistem Ayarları) ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100) # İstersen buraya hackathon logonuzu koy
st.sidebar.title("⚙️ Ayarlar")
panel_gucu = st.sidebar.slider("Kurulu Panel Gücünüz (kW)", min_value=1.0, max_value=50.0, value=5.0, step=1.0)
sehir = st.sidebar.selectbox("Pilot Bölge", ["Ankara (Merkez)"])
elektrik_fiyati = st.sidebar.slider("Elektrik Birim Fiyatı (₺/kWh)", 1.0, 5.0, 2.75)

with st.sidebar.expander("⚙️ Sistem Ayarları", expanded=False):
    secilen_kur = st.selectbox("Para Birimi", ["₺ (TRY)", "$ (USD)", "€ (EUR)"])
    grafik_temasi = st.selectbox("Tema", ["Aydınlık Mod (Light)", "Karanlık Mod (Dark)"])

if grafik_temasi == "Karanlık Mod (Dark)":
    st.markdown("""
    <style>
    .stApp { background-color: #0E1117 !important; }
    [data-testid="stSidebar"] { background-color: #262730 !important; }
    [data-testid="stHeader"] { background-color: #0E1117 !important; }
    [data-testid="stSidebar"] > div:first-child { padding-top: 2.5rem !important; }
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"], p, h1, h2, h3, h4, h5, h6, label, span { color: #FAFAFA !important; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF !important; }
    [data-testid="stSidebar"] { background-color: #F0F2F6 !important; }
    [data-testid="stHeader"] { background-color: #FFFFFF !important; }
    [data-testid="stSidebar"] > div:first-child { padding-top: 2.5rem !important; }
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"], p, h1, h2, h3, h4, h5, h6, label, span { color: #31333F !important; }
    </style>
    """, unsafe_allow_html=True)

# 1. Önce Kişi 1'in modeliyle veriyi al (Zaten yapmıştın)
# df_gercek = predict_solar(tarih=secilen_tarih, panel_gucu_kw=panel_gucu)

# 2. ŞİMDİ KİŞİ 2'NİN KODUNU (2. SEÇENEK) BURAYA EKLE:
try:
    with st.spinner("Yapay Zeka tavsiyesi hazırlanıyor..."):
        # Buradaki değişkenleri senin arayüzdeki slider/inputlardan alman lazım
        tavsiye_metni = generate_advice_for_date(
            tarih="2026-05-02",   # Arayüzden gelen tarih
            sicaklik=28.0,        # Arayüzden gelen sıcaklık
            ruzgar=3.0, 
            bulutluluk=15.0, 
            nem=45.0, 
            panel_gucu_kw=panel_gucu
        )
    
    st.subheader("🤖 KarbonSıfır Asistan Tavsiyesi")
    st.info(tavsiye_metni)

except Exception as e:
    st.error("Asistan şu an yoğun, lütfen birazdan tekrar dene.")

# --- 4. VERİ ÜRETİMİ (XGBoost Modeli ile Gerçek Tahmin) ---
# model/predict.py'den gelen fonksiyonu tek bir kez çağırıyoruz.
df_gercek = predict_solar(
    tarih="2026-05-02", 
    sicaklik=22.0,     # İsteseniz bu değerleri de yan menüden slider ile alabilirsiniz
    bulutluluk=10.0,   
    panel_gucu_kw=panel_gucu 
)

# --- 5. ANA EKRAN VE METRİKLER ---
st.title("☀️ Akıllı Çatı Güneş Asistanı")
st.markdown("Günlük enerji üretiminizi takip edin ve tüketiminizi yapay zeka ile optimize edin.")
st.divider()

st.subheader("📊 Günlük Üretim Özeti")
col1, col2, col3 = st.columns(3)

# Modelden gelen verilere göre dinamik metrikler hesaplayalım
toplam_uretim = df_gercek['beklenen_uretim_kw'].sum()
zirve_saat = df_gercek.loc[df_gercek['beklenen_uretim_kw'].idxmax(), 'saat']
zirve_uretim = df_gercek['beklenen_uretim_kw'].max()
gunluk_tasarruf_tl = toplam_uretim * elektrik_fiyati

if secilen_kur == "$ (USD)":
    gosterilen_tasarruf = gunluk_tasarruf_tl / 45.19
    sembol = "$"
elif secilen_kur == "€ (EUR)":
    gosterilen_tasarruf = gunluk_tasarruf_tl / 53.20
    sembol = "€"
else:
    gosterilen_tasarruf = gunluk_tasarruf_tl
    sembol = "₺"

col1.metric(label="Tahmini Zirve Üretimi", value=f"{zirve_uretim:.1f} kW", delta=f"{zirve_saat}'te Bekleniyor")
col2.metric(label="Toplam Günlük Üretim", value=f"{toplam_uretim:.1f} kWh", delta="Güneşli ve Verimli", delta_color="normal")
col3.metric(label="Tahmini Tasarruf", value=f"{sembol} {gosterilen_tasarruf:.2f}", delta="Faturaya Katkısı")

engellenen_karbon_kg = toplam_uretim * 0.45
araba_km_esdegeri = engellenen_karbon_kg * 4

st.divider()
st.subheader("🌍 Çevresel Etki (Karbon Ayak İzi)")
st.success(f"**Bugünkü Güneş Enerjisi Üretiminizle Doğaya Katkınız:** \n* 💨 **{engellenen_karbon_kg:.1f} kg** CO₂ salınımı engellendi! \n* 🚗 Bu miktar, benzinli bir araçla **{araba_km_esdegeri:.0f} km** yol gitmemeye eşdeğerdir.")

# --- 6. PLOTLY İLE SAATLİK GRAFİK ---
st.subheader("📈 Saatlik Üretim Beklentisi")

# df_mock hatasını çözdük, df_gercek kullanıyoruz
fig = px.area(df_gercek, x='saat', y='beklenen_uretim_kw', 
              color_discrete_sequence=['#FFA500'],
              markers=True)

# Grafiğin arka planını transparan yapıp modernleştirelim ve Y eksenini sabitleyelim
fig.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    xaxis_title="Saat",
    yaxis_title="Üretim (kW)",
    hovermode="x unified",
    yaxis=dict(range=[0, panel_gucu * 1.2])  # Y eksenini panel gücüne göre dinamik ölçekledik
)

if grafik_temasi == "Karanlık Mod (Dark)":
    fig.update_layout(template="plotly_dark")
else:
    fig.update_layout(template="plotly_white")

st.plotly_chart(fig, use_container_width=True)


# --- 7. YAPAY ZEKA ÖNERİ MODÜLÜ (Mock) ---
st.subheader("🤖 Gemini Akıllı Planlayıcı")
st.info(f"""
**💡 Günlük Eylem Planı:**  
Analizlerime göre enerji üretiminiz bugün saat **{zirve_saat}** civarında zirveye ({zirve_uretim:.1f} kW) ulaşacak. Şebekeden elektrik çekmemek ve %100 temiz enerji kullanmak için:
*   Çamaşır ve bulaşık makinenizi o saatlerde çalıştırın.
*   Öğleden sonra bulutlanma beklendiği için yüksek tüketimli cihazları 15:00'ten sonraya bırakmayın.
""")

