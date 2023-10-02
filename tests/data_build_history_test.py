
import sys
import os
sys.path.insert(0, os.path.abspath("./"))
from data.build_history import timestep_delta_unit, timestep_to_seconds
from binance_bridge.schemas import TimeStep

def test_timestep_delta_unit():
    assert timestep_delta_unit(TimeStep.MINUTELY) == 'T'
    assert timestep_delta_unit(TimeStep.HOURLY) == 'H'
    assert timestep_delta_unit(TimeStep.DAILY) == 'D'
    assert timestep_delta_unit(TimeStep.WEEKLY) == 'W'

def test_timestep_to_seconds():
    assert timestep_to_seconds(TimeStep.MINUTELY) == 60
    assert timestep_to_seconds(TimeStep.HOURLY) == 3600
    assert timestep_to_seconds(TimeStep.DAILY) == 86400
    assert timestep_to_seconds(TimeStep.WEEKLY) == 604800