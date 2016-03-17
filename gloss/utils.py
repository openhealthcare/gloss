"""
Generic Gloss Utilities
"""

class AbstractClass(object):
    pass

def itersubclasses(cls, _seen=None):
    """
    Recursively iterate through subclasses
    """
    abstract_classes = AbstractClass.__subclasses__()
    if not isinstance(cls, type):
        raise TypeError('itersubclasses must be called with '
                        'new-style classes, not %.100r' % cls)
    if _seen is None: _seen = set()
    try:
        subs = cls.__subclasses__()
    except TypeError: # fails only when cls is type
        subs = cls.__subclasses__(cls)
    for sub in subs:
        if sub not in _seen:
            _seen.add(sub)
            if sub not in abstract_classes:
                yield sub
            for sub in itersubclasses(sub, _seen):
                if sub not in abstract_classes:
                    yield sub
