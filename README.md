# ☀️ Akıllı Güneş Paneli Sistemi 

> **"Güneşin gücünü yapay zekanın aklıyla yönetin."**

Akıllı Güneş Paneli Sistemi, ev ve işletme kullanıcıları için makine öğrenmesi ve üretken yapay zeka (LLM) destekli otonom bir enerji yönetim panosudur. 

Sadece anlık üretimi gösteren geleneksel "dikiz aynası" uygulamalarının aksine, sistemimiz gelecekteki enerji üretimini tahmin eder, kullanıcıya özel günlük/haftalık eylem planları sunar ve "Smart Load Shifting" (Akıllı Yük Kaydırma) ile elektrik faturalarını optimize eder.

## 🚀 Öne Çıkan Özellikler

* 🤖 **AI Enerji Danışmanı (Sesli Asistan):** Gemini yapay zekası, o günkü üretim verilerine göre "Çamaşır makinesini 14:00'te çalıştırın" gibi kişisel tavsiyeler üretir. Üstelik bu tavsiyeler **sesli asistan** entegrasyonu ile dinlenebilir.
* 📅 **Haftalık Enerji Planı ve İçgörü:** 5 günlük tahminleri analiz ederek haftanın "En Verimli Gününü" belirler ve ağır beyaz eşyaların kullanımını bu günlere planlayarak maksimum tasarruf sağlar.
* 🔄 **Hareketli Panel (Solar Tracker) Simülasyonu:** Kullanıcıların standart sabit paneller ile güneşi takip eden hareketli paneller (+%30 verim) arasındaki kazanç, karbon tasarrufu ve ekstra gelir farkını anlık olarak kıyaslamasını sağlar.
* ⚡ **Şebekeye Satış (Mahsuplaşma) Simülatörü:** Kullanıcının günlük tüketimini (kWh) belirleyebildiği interaktif araç sayesinde, üretilen fazla enerjinin şebekeye satılmasıyla elde edilecek gelir veya şebekeden çekilecek eksik enerji anında hesaplanır.
* 🌍 **Çevresel Etki ve Oyunlaştırma:** Engellenen CO₂ salınımını hesaplar ve doğaya yapılan katkıyı "Yetişkin Ağaç Eşdeğeri" olarak oyunlaştırılmış bir şekilde sunar.
* 🛠️ **Dinamik Parametre Kontrolü:** Kurulu panel gücü (kW), pilot bölge ve elektrik birim fiyatı (₺/kWh) gibi değerler yan menüden anlık olarak değiştirilip tüm hesaplamalar dinamik olarak güncellenebilir.
* ❓ **İnteraktif S.S.S. Modülü:** Kullanıcıların amorti süreleri, batarya kullanımı ve sistem verimliliği gibi konulardaki sorularına anında yanıt bulabilecekleri entegre bilgi bankası.

## 💻 Kullanılan Teknolojiler (Tech Stack)

* **Arayüz (Frontend):** Streamlit (Python)
* **Makine Öğrenmesi (Tahmin Motoru):** XGBoost, Scikit-learn, Pandas
* **Yapay Zeka Karar Motoru:** Google Gemini API (`google-genai` SDK)
* **Veri Görselleştirme:** Streamlit Native Charts & Metrics

<img width="1448" height="818" alt="WhatsApp Image 2026-05-03 at 10 12 42" src="https://github.com/user-attachments/assets/da7bb2a8-ebdf-4b46-ab5f-a4d7ff1feccb" />
<img width="1435" height="640" alt="WhatsApp Image 2026-05-03 at 10 12 41" src="https://github.com/user-attachments/assets/18cbf27a-f609-48d7-b01f-7c0592478b57" />



## ⚙️ Kurulum ve Çalıştırma

Projeyi kendi yerel ortamınızda (localhost) test etmek için aşağıdaki adımları izleyin:

**1. Projeyi Klonlayın:**
```bash
git clone [https://github.com/kullaniciadiniz/CodeXEnergy-Hackathon-TrioCoders.git](https://github.com/kullaniciadiniz/CodeXEnergy-Hackathon-TrioCoders.git)
cd CodeXEnergy-Hackathon-TrioCoders

2. Gerekli Kütüphaneleri Yükleyin:

Bash
pip install -r requirements.txt
3. Çevre Değişkenlerini Ayarlayın:
Ana dizinde bir .env dosyası oluşturun ve Google Gemini API anahtarınızı ekleyin:

Kod snippet'i
GOOGLE_API_KEY=sizin_api_anahtariniz_buraya
4. Uygulamayı Başlatın:

Bash
streamlit run app.py
Geliştirici Ekip: TrioCoders

CodeXEnergy Hackathon Finalist Projesidir.
