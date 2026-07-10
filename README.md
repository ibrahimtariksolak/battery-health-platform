# Batarya Sağlık ve Telemetri Platformu

**Savunma sanayii ve İKA (İnsansız Kara Aracı) uygulamaları için batarya sağlığı izleme, hücre dengeleme ve öngörücü bakım sistemi**

## Proje Nedir?

Bu proje, bir batarya/İKA sisteminin voltaj, akım, sıcaklık ve şarj durumu (SoC) verilerini fizik tabanlı simüle eden, bu veriyi bir zaman serisi veritabanında saklayan, üzerine klasik makine öğrenmesi ile sürüş/kullanım karakteri analizi ve temel BMS (Battery Management System) mantığı (SoH tahmini, hücre dengeleme, termal koruma) ekleyen, sonucu canlı bir web dashboard'unda gösteren uçtan uca bir sistemdir.

Gerçek bir batarya donanımına bağlı değildir — amaç, gerçek BMS sistemlerinin temel mantığını yazılım tarafında küçük ölçekte, anlaşılır ve genişletilebilir şekilde yeniden üretmektir.

## Neden Bu Proje?

- Gerçek EV/İKA sistemlerinde batarya arızaları güvenlik riski ve maliyet kaybı demektir; erken uyarı (termal kaçak, hücre dengesizliği, SoH düşüşü) öngörücü bakımın temelidir.
- Sürüş/kullanım karakterini sınıflandırmak için büyük dil modellerine ihtiyaç yoktur — klasik ML (K-Means) burada daha hızlı, daha ucuz ve daha yorumlanabilirdir.
- Proje, tek bir bileşene değil (sadece dashboard, sadece ML, sadece backend) uçtan uca bir sisteme odaklanır: veri üretiminden karar destek arayüzüne kadar tüm hattı kapsar.

## Sistem Mimarisi
Batarya Simülatörü (Python)
│  (voltaj, akım, sıcaklık, SoC — fizik tabanlı)
▼
Backend API (FastAPI)  ──────────────►  TimescaleDB
│  WebSocket (canlı akış)         (zaman serisi veri)
▼
┌───────────────────────┐
│  BMS Mantığı            │  SoH tahmini, hücre dengeleme,
│  (bms_logic.py)         │  termal koruma state machine
└───────────────────────┘
│
▼
K-Means ML Modülü  ──────────────────►  /ml/driving-style
(sürüş karakteri sınıflandırma)        endpoint'i
│
▼
React Dashboard (Vite + Recharts)
canlı KPI kartları, grafikler,
sürüş analizi paneli
Detaylı mimari notları ve tasarım kararlarının gerekçeleri: [`docs/architecture.md`](docs/architecture.md)

## Teknoloji Yığını

| Katman | Teknoloji | Gerekçe |
|---|---|---|
| Simülatör | Python (saf, bağımlılıksız) | Fizik motoru bağımsız test edilebilir olsun diye harici kütüphaneye ihtiyaç duymaz |
| Backend API | FastAPI + Uvicorn | Async destek, otomatik OpenAPI dokümantasyonu, WebSocket desteği |
| Gerçek zamanlı iletişim | WebSocket | Polling'e göre daha düşük gecikme, daha az gereksiz istek |
| Veritabanı | PostgreSQL + TimescaleDB | Zaman serisi verisi için optimize edilmiş hypertable yapısı |
| BMS Mantığı | Python (histerezisli state machine) | Termal salınım (flapping) olmadan güvenilir durum geçişleri |
| ML | scikit-learn (K-Means + StandardScaler) | Hızlı, yorumlanabilir, düşük kaynak maliyeti; k=3 silhouette skoruyla doğrulanmış (0.93) |
| Frontend | React (Vite) + Recharts | Canlı grafik çizimi, component tabanlı yapı |
| Altyapı | Docker (TimescaleDB için) | Veritabanının taşınabilir, tek komutla ayağa kalkan bir servis olması |

## Klasör Yapısı
├── simulator/            # Bağımsız test edilebilir batarya fizik motoru
│   ├── battery_simulator.py
│   ├── bms_logic.py      # SoH tahmini + termal koruma state machine
│   └── driving_profile.py
├── backend/
│   └── app/
│       ├── main.py       # FastAPI: REST + WebSocket endpoint'leri
│       ├── live_simulation.py  # Arka planda sürekli çalışan simülasyon görevi
│       ├── ws_manager.py
│       └── db/           # Bağlantı, şema, okuma/yazma katmanı
├── ml/
│   ├── features.py       # Ortak özellik çıkarımı (eğitim ve tahmin aynı tanımı paylaşır)
│   ├── train_model.py    # K-Means eğitim scripti
│   ├── predict.py        # Model yükleme + tahmin + öneri motoru
│   └── models/           # Eğitilmiş model dosyası
├── frontend/              # React + Vite dashboard
└── docs/                  # Mimari notlar, tasarım kararları
## Kurulum

```bash
git clone https://github.com/ibrahimtariksolak/battery-health-platform.git
cd battery-health-platform

# 1) Veritabanını ayağa kaldır
docker compose up -d db

# 2) Python sanal ortamı ve bağımlılıklar
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

# 3) Şemayı veritabanına uygula
Get-Content backend\app\db\schema.sql | docker exec -i battery-db psql -U battery_admin -d battery_health

# 4) ML modelini eğit (bir kereye mahsus)
cd ml
python train_model.py
cd ..

# 5) Backend'i başlat
uvicorn backend.app.main:app --reload

# 6) Frontend'i başlat (yeni bir terminalde)
cd frontend
npm install
npm run dev
```

Dashboard: `http://localhost:5173`
API dokümantasyonu (Swagger): `http://127.0.0.1:8000/docs`

## Neden Bu Teknolojik Kararlar?

**Neden TimescaleDB, düz PostgreSQL değil?**
Batarya telemetrisi doğası gereği zaman serisi verisidir — sürekli artan, zaman damgasıyla sorgulanan, eski verinin nadiren güncellendiği bir yapı. TimescaleDB, tabloyu otomatik olarak zaman bazlı parçalara (chunk) böler (`create_hypertable`), bu da zaman aralığı sorgularını standart PostgreSQL'e göre belirgin şekilde hızlandırır. Aynı zamanda standart SQL ile sorgulanabildiği için (InfluxDB gibi ayrı bir sorgu dili öğrenmeye gerek kalmadan) geliştirme hızını korur.

**Neden K-Means, DBSCAN değil?**
Sürüş stili sayısının önceden bilindiği (Eko/Normal/Agresif — üç sabit kategori) bir problemde K-Means, k parametresini elle belirleyebildiğimiz için daha kontrollü ve yorumlanabilir sonuçlar veriyor. DBSCAN, k'yı önceden bilmediğimiz ve gürültülü/aykırı noktaları ayrı bir "noise" sınıfına ayırmak istediğimiz senaryolarda (örneğin anomali tespiti) daha uygun olurdu — ileride termal anomali tespiti eklenirse orada değerlendirilebilir. Bu projede k=3 seçimi, silhouette skoru analiziyle de doğrulanmıştır (bkz. `ml/train_model.py` çıktısı: k=3 için 0.93, en yakın diğer k değerlerinden belirgin şekilde yüksek).

**Neden WebSocket, polling değil?**
Dashboard'un saniyede bir güncellenen bir veri akışını göstermesi gerekiyor. Polling (istemcinin her saniye "yeni veri var mı?" diye sorması) hem gereksiz HTTP overhead'i yaratır hem de gerçek gecikmeyi (veri üretilme anı ile gösterilme anı arasındaki fark) artırır. WebSocket, sunucunun veri üretilir üretilmez istemciye anında göndermesini sağlıyor — tek bağlantı üzerinden çift yönlü, düşük gecikmeli iletişim.

## Donanım Entegrasyon Planı (gerçek sensörlere geçiş için)

Şu an sistem tamamen yazılım tabanlı simülasyonla çalışıyor. Gerçek donanıma bağlanmak istenirse:
- **Akım/voltaj sensörü:** ACS712 (akım) + basit bir voltaj bölücü devresi, bir ESP32'ye I2C/ADC üzerinden bağlanır
- **Sıcaklık sensörü:** NTC termistör veya DS18B20 (dijital, daha hassas)
- **Veri aktarımı:** ESP32 üzerinde çalışan basit bir firmware, okunan değerleri `POST /telemetry` endpoint'ine (Faz 2'de tanımlanan) periyodik olarak gönderir — böylece backend ve üzeri tüm katman (BMS mantığı, ML, dashboard) hiçbir değişiklik gerektirmeden gerçek veriyle çalışmaya devam eder.

## Sonuçlar / Doğrulama

- **Fizik motoru:** Eko/Normal/Agresif sürüş senaryolarında SoC düşüşü ve sıcaklık artışı beklenen sırayla ve gerçekçi aralıklarda (Eko ~26°C, Normal ~28.5°C, Agresif ~40°C tepe sıcaklık) doğrulanmıştır.
- **Termal koruma:** Histerezisli state machine, eşik civarında salınım (flapping) yapmadan durum geçişi yapıyor; sensör veri kaybında fail-safe (SHUTDOWN) davranışı doğrulanmıştır.
- **K-Means modeli:** 120 sentetik oturumla eğitildi, k=3 için silhouette skoru 0.93, küme-etiket uyum oranı (purity) %100. Eğitim setinde hiç bulunmayan test senaryolarında da 3/3 doğru sınıflandırma yapmıştır.

## Lisans

Bu proje bir portfolyo/öğrenme projesidir. MIT lisansı altında paylaşılmıştır.
