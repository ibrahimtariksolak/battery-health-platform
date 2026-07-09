"""
battery_simulator.py ve driving_profile.py'nin dogru calistigini
dogrulamak icin hizli bir test scripti. Faz 1'in son adiminda bu mantik
API'ye ve veritabanina baglanacak; burada sadece cekirdek fizik dogrulaniyor.
"""

from battery_simulator import BatteryPack
from driving_profile import generate_current_profile, DrivingStyle

DT_SECONDS = 1.0
STEPS = 3600


def run_scenario(style: DrivingStyle):
    pack = BatteryPack.create(pack_id="PACK-1", cell_count=8, seed=42)
    profile = generate_current_profile(STEPS, style=style, seed=42)

    print(f"\n=== Senaryo: {style.value.upper()} ===")
    print(f"Baslangic  -> SoC: {pack.pack_soc:.4f}  Voltaj: {pack.pack_voltage}V  "
          f"MaxSicaklik: {pack.max_temperature}C")

    for i, current in enumerate(profile):
        pack.step(current_a=current, dt_seconds=DT_SECONDS)
        if (i + 1) % 900 == 0:
            print(f"  {i+1:>4}s -> SoC: {pack.pack_soc:.4f}  Voltaj: {pack.pack_voltage}V  "
                  f"MaxSicaklik: {pack.max_temperature}C  HucreFarki: {pack.cell_voltage_delta}V")

    print(f"Bitis      -> SoC: {pack.pack_soc:.4f}  Voltaj: {pack.pack_voltage}V  "
          f"MaxSicaklik: {pack.max_temperature}C")

    return pack


if __name__ == "__main__":
    eco_pack = run_scenario(DrivingStyle.ECO)
    normal_pack = run_scenario(DrivingStyle.NORMAL)
    aggressive_pack = run_scenario(DrivingStyle.AGGRESSIVE)

    print("\n=== Karsilastirma ===")
    print(f"Eko        -> SoC dususu: {1.0 - eco_pack.pack_soc:.4f}  MaxSicaklik: {eco_pack.max_temperature}C")
    print(f"Normal     -> SoC dususu: {1.0 - normal_pack.pack_soc:.4f}  MaxSicaklik: {normal_pack.max_temperature}C")
    print(f"Agresif    -> SoC dususu: {1.0 - aggressive_pack.pack_soc:.4f}  MaxSicaklik: {aggressive_pack.max_temperature}C")

    assert eco_pack.pack_soc > normal_pack.pack_soc > aggressive_pack.pack_soc, \
        "SoC dususu suruş stiline gore beklenen sirada degil!"
    assert eco_pack.max_temperature < aggressive_pack.max_temperature, \
        "Agresif suruşte sicaklik daha yuksek olmali!"
    print("\n[OK] Tum dogrulama kontrolleri basarili.")
