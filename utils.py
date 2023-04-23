from config import ATOMIC


def to_atomic(value: float) -> int:
    return value * ATOMIC


def from_atomic(value: int) -> float:
    return float(value) / ATOMIC


def from_atomic_formatted(value: int, precision: int = 8) -> str:
    # noinspection PyStringFormat
    return f"{{:,.{precision}f}}".format(from_atomic(value))


def price_formatted(value: float) -> str:
    return "{:.2f}".format(value)


def time_delta_formatted(time_delta_seconds: int) -> str:
    days, remainder = divmod(time_delta_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{days}d {hours}h {minutes}m {seconds}s"
