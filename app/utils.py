

def get_dict(obj):
    if not isinstance(obj, dict):
        return {}
    return obj


def stringify(obj):
    if isinstance(obj, str):
        return obj
    if isinstance(obj, list):
        return ', '.join(obj)
    return str(obj)