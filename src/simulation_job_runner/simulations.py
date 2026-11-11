from tlw.cli import get_decay_rate_raw

def run_heat(steps: int, alpha: float):
    return {"final_temp": 0.5 * alpha * steps}   # fake for now

def run_transmission_line(n: list[int], l: list[float], c: list[float], k: list[float]):
    return {"decay_rate": get_decay_rate_raw(n, l, c, k)}

SIMULATIONS = {
        "heat": run_heat,
        "transmission-line": run_transmission_line
        }
