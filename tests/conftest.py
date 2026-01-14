"""
configuration pytest pour les test du projet BootcampIA
Fixtures partagées et configurations
"""
import sys
import os

# ajouter backend au chemin pour tous les tests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../backend'))
