"""
Batarya paketi ve hucre seviyesinde fizik tabanli simulator.
Gercek bir BMS'in temel davranisini (SoC, sicaklik, voltaj, pasif dengeleme)
kucuk olcekte taklit eder. Herhangi bir veritabani veya API'ye bagimli degildir,
bagimsiz test edilebilir.
"""

import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List
from bms_logic import ThermalProtection, SoHEstimator

# ---- Sabitler (kucuk olcekli bir EV/IKA pack'i baz alinarak) ----
NOMINAL_CELL_CAPACITY_AH = 50.0           # hucre (grubu) basina anma kapasitesi
CELL_FULL_VOLTAGE = 4.2                   # tam dolu OCV
CELL_EMPTY_VOLTAGE = 3.0                  # tam bos OCV
CELL_NOMINAL_INTERNAL_RESISTANCE = 0.015  # ohm - EV olcegi hucre grubu icin daha dusuk
AMBIENT_TEMP_C = 25.0
THERMAL_MASS = 150.0                      # sicaklik degisimini yumusatan katsayi (J/C benzeri)
COOLING_COEFFICIENT = 0.01                # ortam ile isi alisverisi hizi
# Bu iki deger, eco/normal/aggressive suruş profilleriyle 1 saatlik test
# sonucunda sirasiyla ~26C / ~28.5C / ~40C max sicaklik veren degerler olarak
# kucuk bir tarama ile kalibre edildi (bkz. test_run.py).


def ocv_from_soc(soc: float) -> float:
    """
    SoC (0-1) degerinden acik devre voltajini (OCV) tahmin eder.
    Basitlestirilmis dogrusal model; gercek hucrelerde bu egri S seklindedir
    ama simulasyon amaciyla dogrusal yaklasim yeterlidir.
    """
    soc = max(0.0, min(1.0, soc))
    return CELL_EMPTY_VOLTAGE + soc * (CELL_FULL_VOLTAGE - CELL_EMPTY_VOLTAGE)


@dataclass
class Cell:
    cell_id: str
    capacity_ah: float
    internal_resistance: float
    soc: float = 1.0                      # 1.0 = %100 dolu
    temperature_c: float = AMBIENT_TEMP_C
    balancing_active: bool = False
    voltage: float = field(init=False)

    def __post_init__(self):
        self.voltage = round(ocv_from_soc(self.soc), 4)

    def step(self, current_a: float, dt_seconds: float):
        """
        current_a > 0 : desarj (akim cekiliyor)
        current_a < 0 : sarj
        """
        capacity_as = self.capacity_ah * 3600.0
        delta_soc = -(current_a * dt_seconds) / capacity_as
        self.soc = max(0.0, min(1.0, self.soc + delta_soc))

        ocv = ocv_from_soc(self.soc)
        self.voltage = round(ocv - current_a * self.internal_resistance, 4)

        heat_generated = (current_a ** 2) * self.internal_resistance
        cooling = COOLING_COEFFICIENT * (self.temperature_c - AMBIENT_TEMP_C)
        d_temp = (heat_generated / THERMAL_MASS - cooling) * dt_seconds
        self.temperature_c = round(self.temperature_c + d_temp, 3)

    def to_dict(self) -> dict:
        return {
            "cell_id": self.cell_id,
            "soc": round(self.soc, 4),
            "voltage": self.voltage,
            "temperature_c": self.temperature_c,
            "balancing_active": self.balancing_active,
        }


@dataclass
class BatteryPack:
    pack_id: str
    cells: List[Cell]
    balance_threshold_v: float = 0.05     # bu farkin ustunde pasif dengeleme tetiklenir
    soh_estimator: SoHEstimator = field(init=False)
    thermal_protection: ThermalProtection = field(init=False)

    def __post_init__(self):
        self.soh_estimator = SoHEstimator(rated_capacity_ah=NOMINAL_CELL_CAPACITY_AH)
        self.thermal_protection = ThermalProtection()

    @classmethod
    def create(cls, pack_id: str, cell_count: int = 8, seed: int = None) -> "BatteryPack":
        rng = random.Random(seed)
        cells = []
        for i in range(cell_count):
            capacity = NOMINAL_CELL_CAPACITY_AH * rng.uniform(0.97, 1.03)
            resistance = CELL_NOMINAL_INTERNAL_RESISTANCE * rng.uniform(0.9, 1.1)
            initial_soc = rng.uniform(0.95, 1.0)
            cells.append(Cell(
                cell_id=f"{pack_id}-C{i + 1}",
                capacity_ah=capacity,
                internal_resistance=resistance,
                soc=initial_soc,
            ))
        return cls(pack_id=pack_id, cells=cells)

    def step(self, current_a: float, dt_seconds: float, seconds_since_last_reading: float = 0.0):
        for cell in self.cells:
            cell.balancing_active = False
            cell.step(current_a, dt_seconds)
        self._apply_passive_balancing()
        self.soh_estimator.update(current_a, dt_seconds)
        self.thermal_protection.update(self.max_temperature, seconds_since_last_reading)

    def _apply_passive_balancing(self):
        voltages = [c.voltage for c in self.cells]
        v_max, v_min = max(voltages), min(voltages)
        if (v_max - v_min) > self.balance_threshold_v:
            max_cell = max(self.cells, key=lambda c: c.voltage)
            max_cell.soc = max(0.0, max_cell.soc - 0.0005)
            max_cell.voltage = round(ocv_from_soc(max_cell.soc), 4)
            max_cell.balancing_active = True

    @property
    def pack_voltage(self) -> float:
        return round(sum(c.voltage for c in self.cells), 3)

    @property
    def pack_soc(self) -> float:
        return round(min(c.soc for c in self.cells), 4)

    @property
    def max_temperature(self) -> float:
        return round(max(c.temperature_c for c in self.cells), 3)

    @property
    def cell_voltage_delta(self) -> float:
        voltages = [c.voltage for c in self.cells]
        return round(max(voltages) - min(voltages), 4)

    def to_dict(self) -> dict:
        return {
            "pack_id": self.pack_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pack_voltage": self.pack_voltage,
            "pack_soc": self.pack_soc,
            "max_temperature_c": self.max_temperature,
            "cell_voltage_delta": self.cell_voltage_delta,
            "soh_percent": self.soh_estimator.soh_percent,
            "thermal_state": self.thermal_protection.state.value,
            "cells": [c.to_dict() for c in self.cells],
        }