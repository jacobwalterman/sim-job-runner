def run_heat(steps: int, alpha: float):
    return {"final_temp": 0.5 * alpha * steps}   # fake for now

def run_transmission_line(decay_rate: float):
    return {"decay_rate": decay_rate}   # fake for now

SIMULATIONS = {
        "heat": run_heat,
        "transmission-line": run_transmission_line
        }
