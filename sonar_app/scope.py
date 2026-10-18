"""Public measurement records contain the implemented Layer 0–2 outputs only."""

EXCLUDED_FIELDS = frozenset({'PER', 'PER_status', 'relative_molecular'})


def measurement_data(value):
    """Return a projection without altering stored source records or user text."""
    if isinstance(value, dict):
        result = {key: measurement_data(item) for key, item in value.items() if key not in EXCLUDED_FIELDS}
        if 'notes' in result and isinstance(result['notes'], list):
            result['notes'] = [
                'RES is AC DNA mass equivalent.' if note == 'RES is AC DNA mass equivalent; no output here is an RNA editing fraction.' else note
                for note in result['notes']
            ]
        return result
    if isinstance(value, list):
        return [measurement_data(item) for item in value]
    return value
