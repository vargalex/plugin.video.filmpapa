# -*- coding: utf-8 -*-

import sys

def py2_encode(s, encoding='utf-8', errors='strict'):
    """
    Encode Python 2 ``unicode`` to ``str``
    In Python 3 the string is not changed.
    """
    if sys.version_info[0] == 2 and isinstance(s, unicode):
        s = s.encode(encoding, errors)
    return s

def py2_decode(s, encoding='utf-8', errors='strict'):
    """
    Decode Python 2 ``str`` to ``unicode``
    In Python 3 the string is not changed.
    """
    if sys.version_info[0] == 2 and isinstance(s, str):
        s = s.decode(encoding, errors)
    return s