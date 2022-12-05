# -*- coding: utf-8 -*-
"""Apenas para testes de funcionamento."""
from pathlib import Path

from extensor_vazoes.scripts import vaz20

folderpath = Path(__file__).parent

result_modelos = vaz20(folderpath / 'teste_arquivos_entrada', 80, 80)
