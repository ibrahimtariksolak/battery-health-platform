# Batarya Sağlık ve Telemetri Platformu

**Savunma sanayii ve İKA (İnsansız Kara Aracı) uygulamaları için batarya sağlığı izleme, hücre dengeleme ve öngörücü bakım sistemi**

> Durum: 🚧 Geliştirme aşamasında (Faz 6 — Termal CV modülü)

## Proje Nedir?

Bu proje, bir batarya/İKA sisteminin voltaj, akım, sıcaklık ve şarj durumu (SoC) verilerini simüle eden, bu veriyi zaman serisi bir veritabanında saklayan, üzerine klasik makine öğrenmesi ile sürüş/kullanım karakteri analizi ve temel BMS (Battery Management System) mantığı (SoH tahmini, hücre dengeleme, termal koruma) ekleyen, sonucu canlı bir web dashboard'unda gösteren uçtan uca bir sistemdir.

Gerçek bir batarya donanımına bağlı değildir — amaç, gerçek BMS sistemlerinin temel mantığını yazılım tarafında küçük ölçekte, anlaşılır ve genişletilebilir şekilde yeniden üretmektir.

## Neden Bu Proje?

- Gerçek EV/İKA sistemlerinde batarya arızaları güvenlik riski ve maliyet kaybı demektir; erken uyarı (termal kaçak, hücre dengesizliği, SoH düşüşü) öngörücü bakımın temelidir.
- Sürüş/kullanım karakterini sınıflandırmak için büyük dil modellerine ihtiyaç yoktur — klasik ML (K-Means) burada daha hızlı, daha ucuz ve daha yorumlanabilirdir.
- Proje, tek bir bileşene değil (sadece dashboard, sadece ML, sadece CV) uçtan uca bir sisteme odaklanır.

## Mimari

```
Veri Simülatörü → Backend API (FastAPI + WebSocket) → SQL Veritabanı (TimescaleDB)
                                ↓
                    ML Analiz Motoru (K-Means)
                                ↓
                          Dashboard (React)

Termal Görüntü Kaynağı → Termal CV Modülü → Backend API → Dashboard Uyarısı
```

Detaylı mimari diyagram: `docs/architecture.md` (yakında eklenecek)

## Teknoloji Yığını

| Katman | Teknoloji | Gerekçe |
|---|---|---|
| Simülatör | Python | Hızlı prototipleme |
| Backend API | Python + FastAPI | Async destek, otomatik OpenAPI dokümantasyonu |
| Gerçek zamanlı iletişim | WebSocket | Polling'e göre daha verimli canlı veri akışı |
| Veritabanı | PostgreSQL + TimescaleDB | Zaman serisi verisi için optimize edilmiş SQL |
| ML | scikit-learn (K-Means) | Hızlı, yorumlanabilir, düşük kaynak maliyeti |
| Termal CV | OpenCV / basit autoencoder | Görüntü tabanlı anomali tespiti |
| Frontend | React + Recharts/Plotly | Canlı grafik çizimi |
| Altyapı | Docker + docker-compose | Tek komutla ayağa kalkan, taşınabilir sistem |

## Klasör Yapısı

```
├── simulator/       # Batarya/hücre davranışı simülatörü
├── backend/         # FastAPI backend (API + WebSocket + BMS mantığı)
│   └── app/
│       ├── routes/  # API endpoint'leri
│       └── db/      # Veritabanı modelleri ve bağlantı
├── ml/              # Sürüş karakteri analizi (K-Means)
│   ├── models/
│   └── notebooks/
├── frontend/        # React dashboard
├── thermal-cv/      # Opsiyonel: termal görüntü anomali tespiti
│   ├── data/
│   └── models/
└── docs/            # Mimari diyagramlar, tasarım kararları
```

## Yol Haritası

- [x] Faz 0 — Proje iskeleti ve mimari planlama
- [x] Faz 1 — Veri simülatörü ve veritabanı
- [x] Faz 2 — Backend API ve gerçek zamanlı akış
- [x] Faz 3 — BMS mantığı (SoH, hücre dengeleme, termal koruma)
- [x] Faz 4 — Sürüş karakteri ML modülü
- [x] Faz 5 — Frontend dashboard
- [ ] Faz 6 — Termal CV modülü
- [ ] Faz 7 — Belgeleme ve sunum hazırlığı

## Kurulum

```bash
git clone <repo-url>
cd battery-health-platform
docker-compose up
```

> Not: docker-compose.yml şu an sadece iskelet halindedir, servisler Faz 1-2'de doldurulacaktır.

## Neden Bu Teknolojik Kararlar? (geliştikçe doldurulacak)

- **Neden TimescaleDB, düz PostgreSQL değil?**
- **Neden K-Means, DBSCAN değil?**
- **Neden WebSocket, polling değil?**

## Lisans

Bu proje bir portfolyo/öğrenme projesidir.
