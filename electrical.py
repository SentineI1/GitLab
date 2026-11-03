import math


def series(*components):
    return ("series", components)


def parallel(*components):
    return ("parallel", components)


def equivalent_resistance(network):
    if isinstance(network, (int, float)) and not isinstance(network, bool):
        if not math.isfinite(network) or network <= 0:
            raise ValueError("Resistance must be a finite positive number")
        return network

    if not isinstance(network, tuple) or len(network) != 2:
        raise ValueError("Use a resistance value, series(...), or parallel(...)")

    connection, components = network
    if connection not in ("series", "parallel") or not components:
        raise ValueError("A circuit must have a valid connection and at least one component")

    resistances = [equivalent_resistance(component) for component in components]
    if connection == "series":
        return sum(resistances)
    return 1 / sum(1 / resistance for resistance in resistances)


def analyze_dc(voltage_v, resistance_ohm):
    if not isinstance(voltage_v, (int, float)) or isinstance(voltage_v, bool):
        raise ValueError("Voltage must be a number")
    if not math.isfinite(voltage_v):
        raise ValueError("Voltage must be finite")

    resistance_ohm = equivalent_resistance(resistance_ohm)
    current_a = voltage_v / resistance_ohm
    power_w = voltage_v * current_a
    return {
        "resistance_ohm": resistance_ohm,
        "current_a": current_a,
        "power_w": power_w,
    }


if __name__ == "__main__":
    circuit = series(6, parallel(12, 12))
    print(analyze_dc(12, circuit))