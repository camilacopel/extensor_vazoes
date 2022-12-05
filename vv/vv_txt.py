
# -*- coding: utf-8 -*-
"""Arquivo vazoes.txt."""
from pathlib import Path
from typing import Optional, Union
import pandas as pd
import numpy as np



def ler_arquivo_vazoes_txt(arquivo: Union[str, Path]) -> pd.DataFrame:
    """
    Leitura de um arquivo txt de vazões como dataframe.
    O dataframe é semelhante ao formato original de linhas e colunas.
    Como índice ficam o posto e ano, e como colunas os meses.
    Parameters
    ----------
    posto : int
        Número do posto com o qual foi feita a correlação.
    Returns
    -------
    DataFrame
        Dataframe com os dados lidos.
    """
    # Leitura do arquivo como dataframe, usando espaços como separador.
    df_arq = pd.read_csv(arquivo, header=None, delim_whitespace=True)
    # Nomeação das colunas e índices
    df_arq.columns = ['posto', 'ano', *range(1, 13)]
    df_arq.set_index(['posto', 'ano'], inplace=True)
    df_arq.columns.name = 'mes'
    df_arq = df_arq.astype(int)
    return df_arq
  
  
def _periodizar_df_arq(df_arq: pd.DataFrame) -> pd.DataFrame:
    """
    Cria um dataframe 'periodizado' (ano/mes x postos).
    Com o tempo como linhas e os postos como colunas, tem-se um dataframe
    mais simples com apenas duas dimensões, facilitando sua manipulação.
    Parameters
    ----------
    df_arq : DataFrame
        Dataframe com os dados lidos, oriundo de ler_arquivo_vazoes_txt.
    Returns
    -------
    DataFrame
        Dataframe com os dados 'periodizados'.
    """
    # Empilha os meses e desempilha o posto
    df_period = df_arq.stack().unstack('posto')
    # Transforma os indexes ano e mes em um index só que representa ambas
    # as informações de uma melhor forma. O nome do index continua sendo 'mes'
    df_period.index = pd.PeriodIndex(df_period.index.get_level_values('ano').astype(str)
                                   + '/'
                                   + df_period.index.get_level_values('mes').astype(str),
                                   freq='M')
    df_period.index.name = 'mes'
    # Se todas as colunas são 0, muda para NaN
    # Presume-se aqui que isso só acontece nos períodos finais, caso
    # contrário melhorar este trecho.
    df_period.loc[(df_period == 0).all(axis='columns')] = np.NaN
    # exclui as colunas com NaN
    df_period.dropna(inplace=True)
    # Sem NaN, é possível deixar as colunas com o tipo inteiro
    df_period = df_period.astype(int)
    return df_period
  
  
def _desperiodizar_df_arq(df_period: pd.DataFrame) -> pd.DataFrame:
    """
    Cria um dataframe 'desperiodizado', voltando ao formato tradicional.
    Parameters
    ----------
    df_period : DataFrame
        Dataframe com os dados 'periodizados'.
    Returns
    -------
    DataFrame
        Dataframe com os dados 'desperiodizados'.
    """
    df_arq = df_period.set_index([df_period.index.year,
                                df_period.index.month])
    df_arq.index.names = ['ano', 'mes']
    df_arq = df_arq.stack().unstack('mes').swaplevel()
    # Substitui os NaN por 0 e deixa como inteiro
    df_arq.fillna(0, inplace=True)
    df_arq = df_arq.astype(int)
    df_arq.sort_index(inplace=True)
    return df_arq

  
class VazoesTxt:
    """
    Classe que representa o arquivo vazoes.txt.
    Attributes
    ----------
    df_arquivo : DataFrame
        Representação mais fiel ao estilo do arquivo.
    df_periodizado : DataFrame
        Representação (ano/mes x posto). Simplifica cálculos e manipulações
        por ter apenas duas dimensões.
    """
    
    
    def __init__(self, arquivo: Optional[Union[str, Path]] = None):
        """
        Construtor do objeto.
        Parameters
        ----------
        arquivo : str or Path, optional
            Nome ou caminho do arquivo de vazões.txt utilizado.
        """
        self._filepath = Path(arquivo) if arquivo else None
        # Construção dos dataframes.
        # Poderiam ser tanto métodos como funções à parte,
        # discutir o que seria melhor
        self.df_arquivo = ler_arquivo_vazoes_txt(self._filepath) if arquivo else None
        self.df_period = _periodiza_df_arq(self.df_arquivo) if arquivo else None
    
    
    @classmethod
    def from_df_period(cls, df_period: pd.DataFrame):
        """
        Construtor a partir de um dataframe 'periodizado'.
        Parameters
        ----------
        df_period : DataFrame
            Dataframe com os dados 'periodizados' (PeriodIndex freq 'M').
        """
        self = cls()
        self.df_period = df_period
        self.df_arquivo = _desperiodizar_df_arq(self.df_period)
        return self
      
      
    def add_novo_periodo(self,
                         df_new_months: pd.DataFrame,
                         inplace: bool = False,
                         ) -> None:
        """
        Adiciona informações dos próximos meses.
        Parameters
        ----------
        df_new_months : DataFrame
            Dataframe com as informações a serem adicionadas.
        Returns
        -------
        if not inplace:
            VazoesTxt
                Um novo objeto com as informações concatenadas
        if inplace:
            None
                O atributos do objeto são modificados localmente.
        """
        # Verifica o próximo mês a ser preenchido
        next_month = self.df_period.index[-1] + pd.offsets.MonthEnd()
        # Calcula a diferença entre o próximo mês e o primeiro do período informado
        diff_months = next_month - df_new_months.index[0]
        # Ajusta o index
        df_new_months_ajust = df_new_months.copy()
        df_new_months_ajust.index = df_new_months.index + diff_months
        # Concatena com os dados originais
        df_new = pd.concat([self.df_period, df_new_months_ajust],
                            verify_integrity=True)
        # Se não muda localmente, retorna um novo objeto
        if inplace is False:
            return self.from_df_period(df_new)
        # Muda o objeto no local
        self.df_period = df_new
        # Desnormaliza
        self.df_arquivo = _desperiodizar_df_arq(self.df_period)
        return None
      
      
    def salvar_txt(self,
                   arquivo_destino: Union[str, Path],
                   ) -> None:
        """
        Salva o dataframe modificado em um novo arquivo de vazões.txt.
        Parameters
        ----------
        arquivo_destino : str or Path
            Nome ou caminho do arquivo de destino.
        """
        lista_linhas = list()
        for idx, row in self.df_arquivo.iterrows():
            lista_linhas.append(f"{idx[0]:3} {idx[1]:4}"
                                f"{row[1]:6}{row[2]:6}{row[3]:6}"
                                f"{row[4]:6}{row[5]:6}{row[6]:6}"
                                f"{row[7]:6}{row[8]:6}{row[9]:6}"
                                f"{row[10]:6}{row[11]:6}{row[12]:6}")
        conteudo_arquivo = '\n'.join(lista_linhas)
        with open(arquivo_destino, 'w') as file:
            file.write(conteudo_arquivo)
            file.write('\n')
