"""
Fichier utilisé par pytest
"""

import os
import sys

# Racine du projet = .../qkdSimulator (on remonte de test/attacks/).
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import pytest
import settings


@pytest.fixture(autouse=True)
def restore_settings():
    """Permet la sauvegarde et la restauration (honnêtemetn merci claude parce que la aucun moment j'aurai su :( 
    """
    saved = {name: getattr(settings, name)
             for name in dir(settings) if not name.startswith("__")}
    yield
    for name, value in saved.items():
        setattr(settings, name, value)
