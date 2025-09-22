# backend/config/__init__.py
# Este arquivo marca o diretório como um pacote Python

# backend/config/settings/__init__.py
"""
Settings package para OndeAtende
Permite múltiplas configurações (dev, prod, test)
"""

import os
from pathlib import Path

# Determina qual configuração usar baseado em variável de ambiente
env = os.environ.get('DJANGO_ENV', 'development')

if env == 'production':
    from .production import *
elif env == 'testing':
    from .testing import *
else:
    from .base import *