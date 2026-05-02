import streamlit as st
import pandas as pd
import plotly.express as px
import time
import io
import re
import requests
from gtts import gTTS
from model.predict import predict_solar_weekly
from api_template.llm_asistan import generate_weekly_advice_for_app, generate_advice_for_dataframe

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

# --- 4. HAFTALIK VERİ ÇEKİMİ ---
# Tüm 120 saatlik veriyi tek seferde alıyoruz
df_haftalik_genel = predict_solar_weekly(panel_gucu_kw=panel_gucu)
benzersiz_tarihler = df_haftalik_genel['tarih'].unique().tolist()

# --- 5. ANA EKRAN VE METRİKLER ---
st.title("☀️ Akıllı Çatı Güneş Asistanı")
st.markdown("Günlük enerji üretiminizi takip edin ve tüketiminizi yapay zeka ile optimize edin.")
st.divider()

col_sel, _, _ = st.columns([1, 2, 1])
with col_sel:
    secilen_tarih = st.selectbox("📅 İncelenecek Günü Seçin", benzersiz_tarihler)

# Veriyi seçilen güne göre filtrele (24 saatlik veri)
secilen_gun_df = df_haftalik_genel[df_haftalik_genel['tarih'] == secilen_tarih].reset_index(drop=True)

st.subheader(f"📊 {secilen_tarih} Tarihi İçin Üretim Özeti")
col1, col2, col3 = st.columns(3)

# Seçilen günün metrikleri
gunluk_toplam = secilen_gun_df['beklenen_uretim_kw'].sum()
zirve_saat = secilen_gun_df.loc[secilen_gun_df['beklenen_uretim_kw'].idxmax(), 'saat']
zirve_uretim = secilen_gun_df['beklenen_uretim_kw'].max()
gunluk_tasarruf_tl = gunluk_toplam * elektrik_fiyati

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
col2.metric(label="Toplam Günlük Üretim", value=f"{gunluk_toplam:.1f} kWh", delta="Güneşli ve Verimli", delta_color="normal")
col3.metric(label="Tahmini Tasarruf", value=f"{sembol} {gosterilen_tasarruf:.2f}", delta="Faturaya Katkısı")

engellenen_karbon_kg = gunluk_toplam * 0.45
araba_km_esdegeri = engellenen_karbon_kg * 4

st.divider()
st.subheader("🌍 Çevresel Etki (Karbon Ayak İzi)")
st.success(f"**Bugünkü Güneş Enerjisi Üretiminizle Doğaya Katkınız:** \n* 💨 **{engellenen_karbon_kg:.1f} kg** CO₂ salınımı engellendi! \n* 🚗 Bu miktar, benzinli bir araçla **{araba_km_esdegeri:.0f} km** yol gitmemeye eşdeğerdir.")

# --- 6. PLOTLY İLE SAATLİK GRAFİK ---
st.subheader(f"📈 {secilen_tarih} Saatlik Üretim Beklentisi")

fig = px.area(secilen_gun_df, x='saat', y='beklenen_uretim_kw', 
              color_discrete_sequence=['#FFA500'],
              markers=True)

fig.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    xaxis_title="Saat",
    yaxis_title="Üretim (kW)",
    hovermode="x unified"
)
fig.update_yaxes(range=[0, 4])

if grafik_temasi == "Karanlık Mod (Dark)":
    fig.update_layout(template="plotly_dark")
else:
    fig.update_layout(template="plotly_white")

st.plotly_chart(fig, use_container_width=True)

# --- 6.4 HAFTALIK PLANLAMA ---
st.divider()
st.subheader("📆 Haftalık Planlama")

gunluk_uretim_plan = df_haftalik_genel.groupby('tarih')['beklenen_uretim_kw'].sum().reset_index()

toplam_5_gun = gunluk_uretim_plan['beklenen_uretim_kw'].sum()
ortalama_gunluk = gunluk_uretim_plan['beklenen_uretim_kw'].mean()
toplam_tasarruf_5_gun = toplam_5_gun * elektrik_fiyati

col_plan1, col_plan2, col_plan3 = st.columns(3)
with col_plan1:
    st.metric(label="5 Günlük Toplam", value=f"{toplam_5_gun:.1f} kWh")
with col_plan2:
    st.metric(label="Günlük Ortalama", value=f"{ortalama_gunluk:.1f} kWh")
with col_plan3:
    st.metric(label="5 Günlük Tahmini Tasarruf", value=f"{sembol} {toplam_tasarruf_5_gun:.2f}", help=f"{elektrik_fiyati} TL/kWh üzerinden hesaplanmıştır")


# --- 6.5 HAFTALIK ENERJİ İÇGÖRÜSÜ ---
st.divider()
st.subheader("📅 Haftalık Enerji İçgörüsü")

en_iyi_gun_idx = gunluk_uretim_plan['beklenen_uretim_kw'].idxmax()
en_iyi_gun_tarih = gunluk_uretim_plan.loc[en_iyi_gun_idx, 'tarih']
en_iyi_gun_uretim = gunluk_uretim_plan.loc[en_iyi_gun_idx, 'beklenen_uretim_kw']

gun_isimleri = {
    "Monday": "Pazartesi", "Tuesday": "Salı", "Wednesday": "Çarşamba", 
    "Thursday": "Perşembe", "Friday": "Cuma", "Saturday": "Cumartesi", "Sunday": "Pazar"
}
en_iyi_gun_ismi = pd.to_datetime(en_iyi_gun_tarih).strftime("%A")
en_iyi_gun_ismi_tr = gun_isimleri.get(en_iyi_gun_ismi, en_iyi_gun_ismi)

tasarruf_tl = en_iyi_gun_uretim * elektrik_fiyati
karbon_avantaji = en_iyi_gun_uretim * 0.45

col_w1, col_w2, col_w3 = st.columns(3)
with col_w1:
    st.info(f"**Haftanın En Verimli Günü:**\n\n### {en_iyi_gun_ismi_tr}")
with col_w2:
    st.success(f"**Beklenen Toplam Üretim:**\n\n### {en_iyi_gun_uretim:.1f} kWh")
with col_w3:
    st.warning(f"**Karbon Ayak İzi Avantajı:**\n\n### {karbon_avantaji:.1f} kg CO2 engellendi")

st.markdown(f"**💡 Fırsat:** Bu gün ({en_iyi_gun_ismi_tr}) çamaşır/bulaşık yıkarsanız tahmini **{sembol} {tasarruf_tl:.2f}** tasarruf edersiniz.")

try:
    with st.spinner("🤖 Gemini Haftalık Planınızı Hazırlıyor..."):
        haftalik_tavsiye = generate_weekly_advice_for_app(en_iyi_gun_ismi_tr, en_iyi_gun_uretim)
    st.info(f"**🤖 CarbonZero AI Haftalık Tavsiyesi:**\n\n{haftalik_tavsiye}")
except Exception as e:
    pass


# --- 7. YAPAY ZEKA ÖNERİ MODÜLÜ (Gemini) ---
st.divider()
st.subheader(f"🤖 Gemini Akıllı Planlayıcı ({secilen_tarih})")

try:
    with st.spinner(f"🤖 Gemini {secilen_tarih} günü için tavsiyesini hazırlıyor..."):
        gunluk_tavsiye = generate_advice_for_dataframe(secilen_gun_df, secilen_tarih)
    
    st.info(f"**💡 {secilen_tarih} İçin Günlük Eylem Planı:**\n\n{gunluk_tavsiye}")
    
    st.write("🔊 Asistanı Sesli Dinle")
    # 1. Okunacak tam metni başlık dahil olacak şekilde birleştir
    tam_metin = f"{secilen_tarih} İçin Günlük Eylem Planı. " + gunluk_tavsiye

    # 2. Yıldızları temizle
    temiz_metin = tam_metin.replace('*', '')

    # 3. Emojileri ve özel sembolleri Regex ile temizle (Sadece harfler, sayılar, Türkçe karakterler ve temel noktalama işaretleri kalsın)
    temiz_metin = re.sub(r'[^\w\s.,;:!?()\-üÜğĞıİşŞçÇöÖ]', '', temiz_metin)

    # 4. Temizlenmiş ve emojilerden arındırılmış metni gTTS'e gönder
    try:
        tts = gTTS(text=temiz_metin, lang='tr')
        sound_file = io.BytesIO()
        tts.write_to_fp(sound_file)
        st.audio(sound_file)
    except Exception as tts_err:
        st.warning("Sesli asistan (Google TTS) sunuculara bağlanamadığı için şu an okuma yapılamıyor.")
    
    st.divider()
    st.write("📱 Akıllı Cihaz Entegrasyonu")
    if st.button("📲 Eylem Planını Telefonuma Gönder", use_container_width=True):
        try:
            # ntfy.sh servisine POST isteği atıyoruz
            requests.post(
                "https://ntfy.sh/Trio_Coders",
                data=temiz_metin.encode('utf-8'),
                headers={
                    "Title": "CodeXEnergy Asistani",
                    "Priority": "high",
                    "Tags": "robot,zap"
                }
            )
            st.toast("Bildirim başarıyla telefonunuza iletildi!", icon="✅")
        except Exception as e:
            st.error(f"Bildirim gönderilemedi. Hata detayı: {e}")

except Exception as e:
    st.error(f"Gemini bağlantı hatası: {e}")


# --- 8. AKILLI BİLDİRİM SİMÜLASYONU ---
st.divider()
st.subheader("📲 Akıllı Bildirim Sistemi")
st.write(f"Ev Sahibi: **{demo_kullanici['ad_soyad']}** ({demo_kullanici['lokasyon']})")

if st.button("📱 Yapay Zeka Önerisini Telefona Gönder"):
    with st.spinner("Şebeke üzerinden güvenli SMS iletiliyor..."):
        time.sleep(1.5) 
        
    st.toast("SMS Başarıyla İletildi!", icon="🚀")
    mesaj = f"CodeXEnergy Asistanı: Sayın {demo_kullanici['ad_soyad']}, {secilen_tarih} tarihinde güneş paneli üretiminiz {zirve_saat}'te {zirve_uretim:.1f}kW ile zirve yapacak. Beyaz eşyalarınızı bu saatlerde çalıştırmanızı öneririm."
    st.success(f"**Bildirim Gönderildi:** Aşağıdaki mesaj {demo_kullanici['telefon']} numaralı telefona başarıyla ulaştı.\n\n> *{mesaj}*")
