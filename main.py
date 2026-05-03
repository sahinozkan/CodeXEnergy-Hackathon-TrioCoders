import streamlit as st
import pandas as pd
import plotly.express as px
import time
import io
import re

try:
    from gtts import gTTS
    HAS_GTTS = True
except ImportError:
    HAS_GTTS = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

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
import os
if os.path.exists("triocoders_logo.png") and os.path.getsize("triocoders_logo.png") > 0:
    st.sidebar.image("triocoders_logo.png", use_container_width=True)
else:
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100) # Fallback
st.sidebar.divider()
panel_gucu = st.sidebar.slider("⚡ Kurulu Panel Gücünüz (kW)", min_value=1.0, max_value=50.0, value=5.0, step=1.0)
sehir = st.sidebar.selectbox("📍 Pilot Bölge", ["Ankara (Merkez)"])
elektrik_fiyati = st.sidebar.slider("💰 Elektrik Birim Fiyatı (₺/kWh)", 1.0, 5.0, 2.75)

with st.sidebar.expander("🔧 Sistem Ayarları", expanded=False):
    secilen_kur = st.selectbox("Para Birimi", ["₺ (TRY)", "$ (USD)", "€ (EUR)"])
    grafik_temasi = st.selectbox("Tema", ["Aydınlık Mod (Light)", "Karanlık Mod (Dark)"])

if grafik_temasi == "Karanlık Mod (Dark)":
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    body, p, h1, h2, h3, h4, h5, h6, label, button, input, textarea, select, .stMarkdown, .stAlert, [data-testid="stMetricValue"], [data-testid="stMetricLabel"], [data-testid="stWidgetLabel"], .stButton, .stSelectbox, .stSlider, .stExpander { font-family: 'Inter', sans-serif !important; }

    /* ANA ARKA PLAN */
    .stApp { background: linear-gradient(135deg, #0a0e1a 0%, #0f172a 50%, #0a0e1a 100%) !important; }

    /* SIDEBAR */
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%) !important; border-right: 1px solid rgba(99,102,241,0.25) !important; }
    [data-testid="stSidebar"] > div:first-child { padding-top: 1.5rem !important; }
    [data-testid="stSidebar"] label { color: #A5B4FC !important; font-size: 0.82rem !important; font-weight: 600 !important; }
    [data-testid="stSidebar"] p { color: #CBD5E1 !important; }
    [data-testid="stSidebar"] .stSlider [data-testid="stTickBarMin"],
    [data-testid="stSidebar"] .stSlider [data-testid="stTickBarMax"] { color: #94A3B8 !important; }

    /* HEADER */
    [data-testid="stHeader"] { background: rgba(10,14,26,0.9) !important; border-bottom: 1px solid rgba(99,102,241,0.2) !important; }

    /* BAŞLIK H1 — gradient */
    h1 { background: linear-gradient(90deg,#F59E0B,#FBBF24,#6366F1) !important; -webkit-background-clip: text !important; -webkit-text-fill-color: transparent !important; background-clip: text !important; font-size: 2.4rem !important; font-weight: 800 !important; }

    /* ALT BAŞLIKLAR */
    h2, h3 { color: #E2E8F0 !important; font-weight: 700 !important; }
    h4, h5, h6 { color: #A5B4FC !important; font-weight: 600 !important; }

    /* GENEL METİN */
    .stMarkdown p { color: #CBD5E1 !important; }
    .stMarkdown li { color: #94A3B8 !important; }
    .stMarkdown strong { color: #FBBF24 !important; }
    .stMarkdown a { color: #818CF8 !important; }
    .element-container p { color: #CBD5E1 !important; }

    /* WIDGET ETİKETLERİ (ana alan) */
    [data-testid="stWidgetLabel"] p { color: #A5B4FC !important; font-weight: 600 !important; }
    label { color: #A5B4FC !important; }

    /* SELECTBOX */
    .stSelectbox > div > div { background: rgba(30,27,75,0.8) !important; border: 1px solid rgba(99,102,241,0.4) !important; border-radius: 10px !important; color: #E2E8F0 !important; }
    .stSelectbox [data-baseweb="select"] span { color: #E2E8F0 !important; }

    /* METRİK KARTLAR */
    [data-testid="metric-container"] { background: linear-gradient(135deg,rgba(30,27,75,0.8),rgba(15,23,42,0.9)) !important; border: 1px solid rgba(99,102,241,0.35) !important; border-radius: 16px !important; padding: 1.2rem 1.4rem !important; box-shadow: 0 4px 24px rgba(99,102,241,0.15) !important; transition: transform 0.2s ease, box-shadow 0.2s ease !important; }
    [data-testid="metric-container"]:hover { transform: translateY(-3px) !important; box-shadow: 0 8px 32px rgba(245,158,11,0.25) !important; }
    [data-testid="stMetricValue"] { color: #F59E0B !important; font-size: 1.9rem !important; font-weight: 800 !important; }
    [data-testid="stMetricLabel"] { color: #A5B4FC !important; font-size: 0.78rem !important; font-weight: 600 !important; text-transform: uppercase !important; letter-spacing: 0.06em !important; }
    [data-testid="stMetricDelta"] { color: #34D399 !important; font-size: 0.8rem !important; }

    /* ALERT KUTULAR */
    .stAlert { border-radius: 14px !important; border-left-width: 5px !important; }
    [data-testid="stAlertContentInfo"] { background: rgba(99,102,241,0.15) !important; }
    [data-testid="stAlertContentInfo"] p, [data-testid="stAlertContentInfo"] li { color: #C7D2FE !important; }
    [data-testid="stAlertContentInfo"] strong { color: #818CF8 !important; }
    [data-testid="stAlertContentSuccess"] { background: rgba(16,185,129,0.12) !important; }
    [data-testid="stAlertContentSuccess"] p, [data-testid="stAlertContentSuccess"] li { color: #A7F3D0 !important; }
    [data-testid="stAlertContentSuccess"] strong { color: #34D399 !important; }
    [data-testid="stAlertContentWarning"] { background: rgba(245,158,11,0.12) !important; }
    [data-testid="stAlertContentWarning"] p, [data-testid="stAlertContentWarning"] li { color: #FDE68A !important; }
    [data-testid="stAlertContentWarning"] strong { color: #FBBF24 !important; }

    /* DIVIDER */
    hr { border-color: rgba(99,102,241,0.3) !important; }

    /* EXPANDER */
    [data-testid="stExpander"] { background: rgba(30,27,75,0.5) !important; border: 1px solid rgba(99,102,241,0.3) !important; border-radius: 14px !important; }
    [data-testid="stExpander"] summary span { color: #E2E8F0 !important; }
    [data-testid="stExpander"] p { color: #CBD5E1 !important; }

    /* PLOTLY */
    [data-testid="stPlotlyChart"] { background: rgba(15,23,42,0.6) !important; border: 1px solid rgba(99,102,241,0.2) !important; border-radius: 16px !important; }

    /* YAZILI BÖLÜMLER (slider değer yazısı) */
    [data-testid="stSlider"] p { color: #F59E0B !important; font-weight: 700 !important; }

    /* CHAT MESAJı */
    [data-testid="stChatMessage"] { background: rgba(30,27,75,0.6) !important; border: 1px solid rgba(99,102,241,0.2) !important; border-radius: 12px !important; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    body, p, h1, h2, h3, h4, h5, h6, label, button, input, textarea, select, .stMarkdown, .stAlert, [data-testid="stMetricValue"], [data-testid="stMetricLabel"], [data-testid="stWidgetLabel"], .stButton, .stSelectbox, .stSlider, .stExpander { font-family: 'Inter', sans-serif !important; }
    .stApp { background: linear-gradient(135deg,#F8FAFF 0%,#EEF2FF 50%,#FFF7ED 100%) !important; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg,#FFFFFF 0%,#EEF2FF 100%) !important; border-right: 1px solid rgba(99,102,241,0.15) !important; box-shadow: 2px 0 20px rgba(99,102,241,0.08) !important; }
    [data-testid="stSidebar"] > div:first-child { padding-top: 1.5rem !important; }
    [data-testid="stHeader"] { background: rgba(248,250,255,0.9) !important; border-bottom: 1px solid rgba(99,102,241,0.12) !important; }
    h1 { background: linear-gradient(90deg,#D97706,#F59E0B,#6366F1) !important; -webkit-background-clip: text !important; -webkit-text-fill-color: transparent !important; background-clip: text !important; font-size: 2.4rem !important; font-weight: 800 !important; }
    h2, h3 { color: #1E293B !important; font-weight: 700 !important; }
    h4, h5, h6 { color: #475569 !important; font-weight: 600 !important; }
    .stMarkdown p, .stMarkdown li { color: #334155 !important; }
    [data-testid="metric-container"] { background: linear-gradient(135deg,#FFFFFF,#F8FAFF) !important; border: 1px solid rgba(99,102,241,0.2) !important; border-radius: 16px !important; padding: 1.2rem 1.4rem !important; box-shadow: 0 4px 20px rgba(99,102,241,0.1) !important; transition: transform 0.2s ease, box-shadow 0.2s ease !important; }
    [data-testid="metric-container"]:hover { transform: translateY(-3px) !important; box-shadow: 0 8px 30px rgba(245,158,11,0.2) !important; }
    [data-testid="stMetricValue"] { color: #D97706 !important; font-size: 1.9rem !important; font-weight: 800 !important; }
    [data-testid="stMetricLabel"] { color: #64748B !important; font-size: 0.78rem !important; font-weight: 600 !important; text-transform: uppercase !important; letter-spacing: 0.06em !important; }
    .stAlert { border-radius: 14px !important; border-left-width: 5px !important; }
    hr { border-color: rgba(99,102,241,0.2) !important; }
    [data-testid="stExpander"] { background: #FFFFFF !important; border: 1px solid rgba(99,102,241,0.2) !important; border-radius: 14px !important; box-shadow: 0 2px 12px rgba(99,102,241,0.06) !important; }
    [data-testid="stPlotlyChart"] { background: #FFFFFF !important; border: 1px solid rgba(99,102,241,0.15) !important; border-radius: 16px !important; box-shadow: 0 4px 20px rgba(99,102,241,0.08) !important; }
    .stSelectbox > div > div { background: #FFFFFF !important; border: 1px solid rgba(99,102,241,0.3) !important; border-radius: 10px !important; }
    </style>
    """, unsafe_allow_html=True)


# --- 4. HAFTALIK VERİ ÇEKİMİ ---
# Tüm 120 saatlik veriyi tek seferde alıyoruz
df_haftalik_genel = predict_solar_weekly(panel_gucu_kw=panel_gucu)
benzersiz_tarihler = df_haftalik_genel['tarih'].unique().tolist()

# --- 5. ANA EKRAN VE METRİKLER ---
st.title("☀️ Akıllı Güneş Paneli Sistemi")
st.markdown("Günlük enerji üretiminizi takip edin ve tüketiminizi yapay zeka ile optimize edin.")
st.divider()

col_sel, _, _ = st.columns([1, 2, 1])
with col_sel:
    secilen_tarih = st.selectbox("📅 İncelenecek Günü Seçin", benzersiz_tarihler)

# Veriyi seçilen güne göre filtrele (24 saatlik veri)
secilen_gun_df = df_haftalik_genel[df_haftalik_genel['tarih'] == secilen_tarih].reset_index(drop=True)

gemini_container = st.container()

st.subheader(f"📊 {secilen_tarih} Tarihi İçin Üretim Özeti")
tracker_aktif = st.toggle("🔄 Akıllı Güneş Takip (Solar Tracker) Simülasyonunu Aç")
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

col1.metric(label="⚡ Zirve Üretim", value=f"{zirve_uretim:.1f} kW", delta=f"{zirve_saat}'te Bekleniyor")
col2.metric(label="☀️ Günlük Toplam", value=f"{gunluk_toplam:.1f} kWh", delta="Güneşli ve Verimli", delta_color="normal")
col3.metric(label="💰 Fatura Tasarrufu", value=f"{sembol} {gosterilen_tasarruf:.2f}", delta="Faturaya Katkısı")

if tracker_aktif:
    sabit_uretim = gunluk_toplam
    hareketli_uretim = sabit_uretim * 1.30
    ekstra_kwh = hareketli_uretim - sabit_uretim
    ekstra_co2 = ekstra_kwh * 0.45
    ekstra_gelir_tl = ekstra_kwh * elektrik_fiyati
    
    if secilen_kur == "$ (USD)":
        ekstra_gelir = ekstra_gelir_tl / 45.19
    elif secilen_kur == "€ (EUR)":
        ekstra_gelir = ekstra_gelir_tl / 53.20
    else:
        ekstra_gelir = ekstra_gelir_tl
        
    st.markdown("##### 🔄 Hareketli Panel (Solar Tracker) Farkı")
    tcol1, tcol2, tcol3 = st.columns(3)
    tcol1.metric("⚡ Tracker Kazancı", f"+ {ekstra_kwh:.1f} kWh")
    tcol2.metric("🌍 CO₂ Tasarrufu", f"+ {ekstra_co2:.1f} kg")
    tcol3.metric("💵 Ekstra Gelir", f"+ {sembol} {ekstra_gelir:.2f}")

# --- 6. PLOTLY İLE SAATLİK GRAFİK ---
st.subheader("📈 Saatlik Üretim Tahmini")

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

if tracker_aktif:
    import plotly.graph_objects as go
    fig.add_trace(
        go.Scatter(
            x=secilen_gun_df['saat'], 
            y=secilen_gun_df['beklenen_uretim_kw'] * 1.30, 
            mode='lines+markers',
            name='Hareketli Panel (+%30)',
            line=dict(color='#00b894', width=3, dash='dash'),
            marker=dict(size=6)
        )
    )

st.plotly_chart(fig, use_container_width=True)

engellenen_karbon_kg = gunluk_toplam * 0.45
kurtarilan_agac = int(engellenen_karbon_kg / 0.06)

st.divider()
st.subheader("🌍 Çevresel Etki (Karbon Ayak İzi)")
st.success(f"**Bugünkü Güneş Enerjisi Üretiminizle Doğaya Katkınız:** \n* 💨 **{engellenen_karbon_kg:.1f} kg** CO₂ salınımı engellendi! \n* 🌳 Bu miktar, tam {kurtarilan_agac} yetişkin ağacın bir tam günde temizleyebileceği havaya eşdeğerdir!")

st.write("") # Boşluk bırak
with st.expander("⚡ Şebekeye Satış (Mahsuplaşma) Simülatörü", expanded=True):
    st.markdown("Türkiye 'Lisanssız Elektrik Üretimi' yönetmeliğine göre ihtiyaç fazlası enerjinizi şebekeye satabilirsiniz. (EPDK verilerine göre Türkiye'de günlük ortalama ev tüketimi **8.0 kWh**'dir.)")
    
    # Kullanıcıdan tahmini günlük tüketimini al
    gunluk_tuketim = st.slider("Bugünkü Tahmini Ev Tüketiminiz (kWh)", min_value=0.0, max_value=50.0, value=8.0, step=0.5)
    
    # Hesaplama:
    net_enerji = gunluk_toplam - gunluk_tuketim 
    
    if net_enerji > 0:
        satis_geliri = net_enerji * elektrik_fiyati 
        
        if 'secilen_kur' in locals() and secilen_kur == "$ (USD)":
            gosterilen_gelir = f"$ {(satis_geliri / 45.19):.2f}"
        elif 'secilen_kur' in locals() and secilen_kur == "€ (EUR)":
            gosterilen_gelir = f"€ {(satis_geliri / 53.20):.2f}"
        else:
            gosterilen_gelir = f"₺ {satis_geliri:.2f}"
            
        st.success(f"**Tebrikler!** Tüketiminizden arta kalan **{net_enerji:.1f} kWh** enerjiyi şebekeye sattınız. **Net Kazanç: {gosterilen_gelir}**")
    else:
        st.warning(f"Bugün üretiminiz tüketiminizi karşılamıyor. Şebekeden **{abs(net_enerji):.1f} kWh** enerji çekeceksiniz.")

# --- 6.4 HAFTALIK PLANLAMA ---
st.divider()
st.subheader("📅 Haftalık Enerji Planı")

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
    st.warning(f"**Karbon Ayak İzi Avantajı:**\n\n### 🌍 {karbon_avantaji:.1f} kg CO₂")

st.markdown(f"**💡 Fırsat:** Bu gün ({en_iyi_gun_ismi_tr}) çamaşır/bulaşık yıkarsanız tahmini **{sembol} {tasarruf_tl:.2f}** tasarruf edersiniz.")

try:
    with st.spinner("🤖 Gemini Haftalık Planınızı Hazırlıyor..."):
        haftalik_tavsiye = generate_weekly_advice_for_app(en_iyi_gun_ismi_tr, en_iyi_gun_uretim)
    st.info(f"**🤖 CarbonZero AI Haftalık Tavsiyesi:**\n\n{haftalik_tavsiye}")
except Exception as e:
    pass


# --- 7. YAPAY ZEKA ÖNERİ MODÜLÜ (Gemini) ---
with gemini_container:
    st.divider()
    st.subheader(f"🤖 AI Enerji Danışmanı ({secilen_tarih})")

    try:
        with st.spinner(f"🤖 Gemini {secilen_tarih} günü için tavsiyesini hazırlıyor..."):
            gunluk_tavsiye = generate_advice_for_dataframe(secilen_gun_df, secilen_tarih)
        
        # Ekranda (st.info) görünmesi için ek analitik kuralı doğrudan ana metne dahil ediyoruz
        gunluk_tavsiye += f"\n\n📌 **Öneri:** Haftanın en verimli günü **{en_iyi_gun_ismi_tr}**. Eğer aciliyetin yoksa yüksek enerji gerektiren planlarını o güne bırakabilirsin."

        if tracker_aktif:
            gunluk_tavsiye += f"\n\n💡 Yatırım Tavsiyesi: Eğer çatıdaki sisteminizi 'Hareketli Panel (Solar Tracker)' sistemine geçirirseniz, sadece bugün ekstra {ekstra_kwh:.1f} kWh enerji ve {sembol} {ekstra_gelir:.2f} kazanç elde ederdiniz. Bu sistem kendini kısa sürede amorti edebilir!"

        st.write("🔊 Asistanı Sesli Dinle")
        # 1. Okunacak tam metni başlık dahil olacak şekilde birleştir
        tam_metin = f"{secilen_tarih} İçin Günlük Eylem Planı. " + gunluk_tavsiye

        # 2. Yıldızları temizle
        temiz_metin = tam_metin.replace('*', '')

        # 3. Emojileri ve özel sembolleri Regex ile temizle (Sadece harfler, sayılar, Türkçe karakterler ve temel noktalama işaretleri kalsın)
        temiz_metin = re.sub(r'[^\w\s.,;:!?()\-üÜğĞıİşŞçÇöÖ]', '', temiz_metin)


        if "ilk_bildirim_gonderildi" not in st.session_state:
            try:
                import requests
                requests.post(
                    "https://ntfy.sh/Trio_Coders",
                    data=temiz_metin.encode('utf-8'),
                    headers={
                        "Title": "CodeXEnergy Asistani", 
                        "Priority": "high", 
                        "Tags": "robot,zap",
                        "Actions": "view, Panele Don ve Uygula, http://localhost:8501" 
                    }
                )
                st.session_state.ilk_bildirim_gonderildi = True
            except Exception as e:
                pass # Otomatik akışta arayüze hata basıp UX'i bozma

        # 4. Temizlenmiş ve emojilerden arındırılmış metni gTTS'e gönder
        if HAS_GTTS:
            try:
                tts = gTTS(text=temiz_metin, lang='tr')
                sound_file = io.BytesIO()
                tts.write_to_fp(sound_file)
                st.audio(sound_file)
            except Exception as tts_err:
                st.warning("Sesli asistan (Google TTS) sunuculara bağlanamadığı için şu an okuma yapılamıyor.")
        else:
            st.warning("Sesli okuma için 'gTTS' kütüphanesi eksik. Terminale yazın: pip install gTTS")
            
        st.info(f"**💡 {secilen_tarih} İçin Günlük Eylem Planı:**\n\n{gunluk_tavsiye}")
        


    except Exception as e:
        st.error(f"Gemini bağlantı hatası: {e}")


# --- 8. YARDIM MASASI (Kural Tabanlı Asistan) ---
st.divider()
st.subheader("💬 Sık Sorulan Sorular")

sss_sozlugu = {
    "Lütfen sormak istediğiniz soruyu seçin...": "",
    "💰 Sistem kendini ne kadar sürede amorti eder?": "Mevcut elektrik fiyatları ve güneşlenme süreleri göz önüne alındığında, ortalama 5 kW'lık bir sistem kendini 4-5 yıl içinde amorti eder. Yukarıdaki 'Tahmini Tasarruf' metriklerinden günlük kazancınızı takip edebilirsiniz.",
    "🌍 Karbon tasarrufu hesaplaması nasıl çalışıyor?": "Türkiye ortalamasına göre şebekeden çekilmeyen her 1 kWh elektrik, yaklaşık 0.45 kg CO2 salınımını engeller. Sistemimiz, anlık üretiminizle bu katsayıyı çarparak doğaya katkınızı şeffafça hesaplar.",
    "⏱️ Yüksek enerji tüketen cihazları ne zaman çalıştırmalıyım?": "Grafikteki 'Tahmini Zirve Üretimi' saatlerinde (genellikle 11:00 - 14:00 arası) yüksek tüketimli cihazları çalıştırmak, şebekeye olan maliyetinizi sıfıra indirir.",
    "🛠️ Panellerin veriminin düştüğünü nasıl anlarım?": "Yapay zeka asistanımız, meteoroloji verileri ile üretim verilerinizi anlık karşılaştırır. Eğer optimum şartlarda üretim düşük kalırsa, eylem planı üzerinden size 'Temizlik veya Bakım' uyarısı verir.",
    "☁️ Hava bulutlu veya yağmurlu olduğunda sistem çalışır mı?": "Evet, panellerimiz dağınık ışıkta bile enerji üretmeye devam eder. Ancak güneşli günlere kıyasla verim %10 ila %25 arasına düşebilir. Akıllı planlayıcımız bu dalgalanmaları önceden tahmin ederek planınızı günceller.",
    "🔋 Evimde batarya (depolama) sistemi kullanmalı mıyım?": "Ürettiğiniz enerjinin fazlasını gece kullanmak veya elektrik kesintilerinden etkilenmemek istiyorsanız batarya sistemleri harika bir yatırımdır. Sistemimiz, mevcut üretim profilinize göre batarya ihtiyacınızı analiz edebilir.",
    "📈 'Tahmini Zirve Üretimi' ne anlama geliyor?": "Gün içinde güneş ışınlarının panellerinize en dik açıyla geldiği ve sistemin maksimum verimle çalıştığı (en yüksek kW değerine ulaştığı) tepe noktasını ifade eder.",
    "📱 Akıllı asistan bildirimleri ücretli mi?": "Hayır, CodeXEnergy asistan bildirimleri tamamen ücretsizdir. ntfy altyapısı üzerinden telefonunuza güvenli ve anlık bir şekilde iletilir.",
    "🔌 Sisteme yeni akıllı ev aletleri (IoT) bağlayabilir miyim?": "Kesinlikle! Faz-2 aşamasında akıllı prizler ve Wi-Fi destekli röleler entegre edilecek. Böylece üretim zirvedeyken çamaşır makineniz sistem tarafından otomatik başlatılabilecek.",
    "📊 Verilerim ne kadar güvende tutuluyor?": "Tüm enerji üretim ve tüketim verileriniz yerel olarak işlenir veya şifrelenmiş sunucularımızda anonim olarak analiz edilir. Verileriniz asla üçüncü partilerle paylaşılmaz.",
    "⚡ İhtiyaç fazlası elektriğimi devlete satabilir miyim? (Mahsuplaşma)": "Evet! Türkiye'deki 'Aylık Mahsuplaşma' yönetmeliği sayesinde, çift yönlü sayaç taktırarak tüketiminizden arta kalan elektriği kendi satın aldığınız aktif enerji bedeli üzerinden dağıtım şirketine satıp nakit gelir elde edebilirsiniz."
}

secilen_soru = st.selectbox("Yardımcı Asistana Sorun:", list(sss_sozlugu.keys()), label_visibility="collapsed")

if secilen_soru != "Lütfen sormak istediğiniz soruyu seçin...":
    with st.chat_message("assistant"):
        st.write(sss_sozlugu[secilen_soru])
