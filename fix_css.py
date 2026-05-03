with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the exact start and end of the CSS theme block
start_marker = 'if grafik_temasi == "Karanlık Mod (Dark)":'
end_marker = '# --- 4. HAFTALIK VERİ ÇEKİMİ ---'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print("Markers not found!")
    print("start:", start_idx, "end:", end_idx)
else:
    new_css_block = '''if grafik_temasi == "Karanlık Mod (Dark)":
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    * { font-family: 'Inter', sans-serif !important; }
    .stApp { background: linear-gradient(135deg, #0a0e1a 0%, #0f172a 50%, #0a0e1a 100%) !important; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%) !important; border-right: 1px solid rgba(99,102,241,0.25) !important; }
    [data-testid="stSidebar"] > div:first-child { padding-top: 1.5rem !important; }
    [data-testid="stHeader"] { background: rgba(10,14,26,0.9) !important; border-bottom: 1px solid rgba(99,102,241,0.2) !important; }
    h1 { background: linear-gradient(90deg,#F59E0B,#FBBF24,#6366F1) !important; -webkit-background-clip: text !important; -webkit-text-fill-color: transparent !important; background-clip: text !important; font-size: 2.4rem !important; font-weight: 800 !important; }
    h2, h3 { color: #E2E8F0 !important; font-weight: 700 !important; }
    h4, h5, h6 { color: #94A3B8 !important; font-weight: 600 !important; }
    .stMarkdown p, .stMarkdown li { color: #CBD5E1 !important; }
    [data-testid="metric-container"] { background: linear-gradient(135deg,rgba(30,27,75,0.8),rgba(15,23,42,0.9)) !important; border: 1px solid rgba(99,102,241,0.35) !important; border-radius: 16px !important; padding: 1.2rem 1.4rem !important; box-shadow: 0 4px 24px rgba(99,102,241,0.15) !important; transition: transform 0.2s ease, box-shadow 0.2s ease !important; }
    [data-testid="metric-container"]:hover { transform: translateY(-3px) !important; box-shadow: 0 8px 32px rgba(245,158,11,0.25) !important; }
    [data-testid="stMetricValue"] { color: #F59E0B !important; font-size: 1.9rem !important; font-weight: 800 !important; }
    [data-testid="stMetricLabel"] { color: #94A3B8 !important; font-size: 0.78rem !important; font-weight: 600 !important; text-transform: uppercase !important; letter-spacing: 0.06em !important; }
    .stAlert { border-radius: 14px !important; border-left-width: 5px !important; }
    hr { border-color: rgba(99,102,241,0.3) !important; }
    [data-testid="stExpander"] { background: rgba(30,27,75,0.5) !important; border: 1px solid rgba(99,102,241,0.3) !important; border-radius: 14px !important; }
    [data-testid="stPlotlyChart"] { background: rgba(15,23,42,0.6) !important; border: 1px solid rgba(99,102,241,0.2) !important; border-radius: 16px !important; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    * { font-family: 'Inter', sans-serif !important; }
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

'''

    new_content = content[:start_idx] + new_css_block + '\n' + content[end_idx:]

    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Done! Replaced CSS block.")
    print(f"Old block was {end_idx - start_idx} chars, new block is {len(new_css_block)} chars")
