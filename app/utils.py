def is_positive_integer(value):
    try:
        int_value = int(value)
        return int_value > 0
    except ValueError:
        return False
    

def is_valid_quantity(value):
    try:
        int(value)
        return True
    except Exception:
        return False