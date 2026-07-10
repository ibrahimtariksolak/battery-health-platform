# Mimari Notları

## Veri Akışı

1. `simulator/battery_simulator.py` içindeki `BatteryPack`, her adımda (1 saniye) hücre bazlı voltaj/SoC/sıcaklık hesaplar; `bms_logic.py` bu veriye bakarak SoH ve termal durumu günceller.
2. `backend/app/live_simulation.py`, bu simülasyonu arka planda (asyncio task olarak) sürekli çalıştırır.
3. Her adımda üretilen veri iki yere gider:
   - WebSocket üzerinden bağlı istemcilere (`ws_manager.py`) anında yayınlanır
   - Belirli aralıklarla (`DB_FLUSH_EVERY_N_STEPS`) toplu halde TimescaleDB'ye yazılır
4. Frontend, `/ws/telemetry` üzerinden canlı veri alır; geçmiş analiz için REST endpoint'lerini (`/telemetry/history`, `/ml/driving-style`, `/bms/status`) kullanır.

## Neden Ayrı Bir `bms_logic.py` Modülü?

`ThermalProtection` ve `SoHEstimator` sınıfları kasıtlı olarak `BatteryPack`'ten bağımsız, saf mantık (pure logic) olarak yazıldı. Bu sayede:
- Veritabanı veya API'ye bağımlı olmadan izole test edilebiliyor (bkz. `simulator/test_bms_logic.py`)
- İleride farklı bir pack modeline (örneğin gerçek donanımdan gelen veriye) kolayca bağlanabilir

## Termal State Machine Tasarımı

Basit bir eşik kontrolü (`if sicaklik > 45: uyarı ver`) yerine histerezisli bir state machine kullanıldı, çünkü:
- Sıcaklık eşik civarında küçük dalgalanmalar gösterebilir (örn. 44.8°C - 45.2°C arası salınım)
- Basit eşik kontrolü bu durumda saniyede birkaç kez durum değiştirir ("flapping") — hem gerçekçi değil hem de dashboard'da anlamsız bir titreme yaratır
- Giriş ve çıkış eşiklerini farklı tutarak (örn. 35°C'de uyarıya gir, 32°C'ye düşmeden çıkma) bu sorun ortadan kalkar

Ayrıca `SHUTDOWN` durumu kasıtlı olarak kalıcıdır (otomatik çıkış yok) — gerçek bir BMS'te termal kapatma sonrası sistemin kendi kendine "her şey yolunda" deyip tekrar çalışmaya başlaması güvenlik açısından kabul edilemez; harici/manuel bir reset gerektirir.

## SoH Tahmin Modeli — Sınırlamalar

Gerçek Li-ion hücrelerde SoH, yüzlerce şarj/deşarj çevrimi sonrasında ölçülebilir bir düşüş gösterir. Bu projede tek bir oturumda gözlemlenebilir bir değişim görebilmek için yaşlanma etkisi demo amaçlı hızlandırılmıştır (`FADE_PERCENT_PER_EQUIVALENT_CYCLE` sabiti). Gerçek bir üretim sisteminde bu katsayı, üreticinin hücre veri sayfasındaki gerçek çevrim ömrü verilerinden kalibre edilmelidir.

## Bilinen Sınırlamalar ve Gelecek Çalışma

- Hücreler arası termal etkileşim modellenmiyor (her hücrenin sıcaklığı bağımsız hesaplanıyor, gerçekte komşu hücreler birbirini ısıtır)
- SoC tahmini saf coulomb counting'e dayanıyor; gerçek BMS'ler genelde buna ek olarak OCV tabanlı periyodik kalibrasyon da yapar
