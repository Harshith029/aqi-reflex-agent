from config.pollutants import BREAKPOINTS, AQI_BINS

def sub_index(pollutant, concentration):
    if pollutant not in BREAKPOINTS:
        return None
    if concentration is None or concentration < 0:
        return None
    for (bp_lo, bp_hi, aqi_lo, aqi_hi) in BREAKPOINTS[pollutant]["breakpoints"]:
        if bp_lo <= concentration <= bp_hi:
            value = ((aqi_hi - aqi_lo) / (bp_hi - bp_lo)) * (concentration - bp_lo) + aqi_lo
            return round(value, 2)
    return 500.0

def aqi_category(aqi_value):
    for (lo, hi, label) in AQI_BINS:
        if lo <= aqi_value <= hi:
            return label
    return "Severe"

def compute_aqi(sensor_readings):
    sub_indices = {}
    for pollutant, conc in sensor_readings.items():
        if pollutant.startswith("_"):
            continue
        si = sub_index(pollutant, conc)
        if si is not None:
            sub_indices[pollutant] = si
    if not sub_indices:
        return None
    dominant  = max(sub_indices, key=sub_indices.get)
    final_aqi = sub_indices[dominant]
    return {
        "aqi":         final_aqi,
        "category":    aqi_category(final_aqi),
        "dominant":    dominant,
        "sub_indices": sub_indices,
    }
