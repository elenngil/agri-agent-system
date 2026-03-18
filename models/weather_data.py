from tools.aemet_climate import get_climmate_summary
from datetime import date

data1 = get_climmate_summary(station = "3195", start_date = date(2025,5,13), end_date = date(2025,5,13))

def get_climate_features(data):

    d = data[0]

    frost_risk = d['tmin'] <= 0
    cold_hours = d['tmin'] < 7
    heatwave = d['tmax'] >= 35

    features = {'temperature_max': d['tmax'], 
                'temperature_mean': d["tmed"], 
                'temperature_min': d['tmin'], 
                'precipitation': d['prec'], 
                'humidity': d['hrMedia'],
                'wind': d['velmedia'],
                'pressure': (d['presMax'] + d['presMin'])/2,
                'frost_risk': frost_risk,
                'cold_hours': cold_hours,
                'heatwave': heatwave}
    
    return features

print(get_climate_features(data1))