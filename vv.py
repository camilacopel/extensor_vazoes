#! /home/airflow/ambiente_virtual_airflow/bin/python
"""
Foi colocado o 'shebang' do python acima para apontar para o interpretador
python do servidor de producao (nwautom).

Se der um erro do tipo:
    -bash: ./vaz20.py: /home/airflow/ambiente_virtual_airflow/bin/python^M:
        bad interpreter: No such file or directory

verifique se o arquivo está utilizado o separador de linha do Linux (LF)
ao invés do separador do Windows (CRLF).
Ou então indique o interpretador antes na linha de comando.
"""
import argparse
from pathlib import Path

from extensor_vazoes.scripts import vaz20

# Default para o número máximo de amplitudes fora do limite
DEF_MAX = 80

# Utiliza um parser para a entrada dos argumentos
parser = argparse.ArgumentParser(description='Extensor dos arquivos de vazoes '
                                             'usando Correlacao e Amplitude.')
parser.add_argument('pasta',
                    metavar='pasta',
                    type=str,
                    help='Pasta onde estao os arquivos')
parser.add_argument('-max',
                    metavar='n_max',
                    type=int,
                    default=DEF_MAX,
                    help='Numero maximo de postos com amplitude maior ou menor '
                         f'que as amplitudes historicas. O default e {DEF_MAX}')
args = parser.parse_args()

# Roda o script
pasta_entrada = Path(args.pasta)
vaz20(pasta_entrada, max_lt_min=args.max, max_gt_max=args.max)
