# -*- coding: utf-8 -*-
"""Modelos de previsão para alguns meses à frente."""
from typing import Optional

import numpy as np
import pandas as pd


def calc_corr_last12(df_hist: pd.DataFrame) -> pd.DataFrame:
    """
    Cálculo da correlação dos últimos 12 meses informados com anos anteriores.

    Parameters
    ----------
    df_hist : DataFrame
        Dataframe do histórico a ser analisado.
        As 12 últimas linhas devem ser os 12 meses com os quais será calculada
        a correlação com dados de anos anteriores.

    Returns
    -------
    DataFrame
        Dataframe com as correlações calculadas.
        Como index é informado o mês final do período de 12 meses com o qual
        foi calculada a correlação.

    """
    # pylint: disable=protected-access
    # Conferindo se o index está no formato desejado (pd.PeriodIndex freq=M)
    if not isinstance(df_hist.index.freq, pd._libs.tslibs.offsets.MonthEnd):
        raise Exception("Favor informar dataframe periodizado mensalmente.")

    df_ref = df_hist.copy()
    # Trecho de 12 meses com o qual será calculada a correlação
    df_trecho = df_ref.iloc[-12:]
    # Espalha o trecho por uma cópia do dataframe respeitando os meses
    df_other = df_ref.copy()
    for month in range(1, 13):
        df_other[df_other.index.month == month] = df_trecho[df_trecho.index.month == month].iloc[0]

    # Calcula a correlação
    df_corr = df_ref.rolling(12).corr(df_other)
    # Filtra os dados da correlação com o mês final
    df_corr = df_corr[df_corr.index.month == df_trecho.index.month[-1]]
    df_corr.index.name = 'mes_final'

    return df_corr


class SimpleCorrelation12:
    """
    Classe que representa o um modelo de correlações simples.

    Attributes
    ----------
    coluna : int
        Coluna referência para a escolha da <posicao> maior correlação.
    posicao : int
        Posição na ordem de maior correlação relativo à <coluna>.
    df_base : DataFrame
        Base utilizada para o modelo
    df_correlacao_ : DataFrame
        Tabela com a correlação entre os últimos 12 meses e
        estes doze meses em outros anos.
    correlacao_ : float
        Correlação encontrada para <posicao> melhor correlação para <coluna>
    correlacao_outros_ : Series
        Correlação para as outras colunas na <posicao>
    mes_final_periodo_ : str
        'Ano-mes' do perído com a <posicao> melhor correlação para <coluna>
    """

    # pylint: disable=too-many-instance-attributes

    def __init__(self,
                 coluna: int,
                 posicao: int = 1,
                 ):
        """
        Criação do modelo.

        Parameters
        ----------
        coluna : int
            Coluna a ser usada para ordenação das maiores correlações.
        posicao : int, optional
            Posição na ordenação de maiores correlações.
            O default é a usar a primeira posição (1).

        """
        self.coluna = coluna
        self.posicao = posicao

        # Atributos que serão definidos apenas ao realizar o fit
        self.df_base = None
        self.df_correlacao = None
        self._period_ = None
        self.correlacao_ = None
        self.correlacao_outros_ = None
        self.mes_final_periodo_ = None


    def fit(self, df_base: pd.DataFrame) -> 'SimpleCorrelation12':
        """
        Cálculo das correlações.

        Parameters
        ----------
        df_base : DataFrame
            Dados históricos para cálculo das correlações.

        """
        self.df_base = df_base.copy()
        self.df_correlacao = calc_corr_last12(df_base)

        top_corr = self.df_correlacao[self.coluna].sort_values(ascending=False)

        # Dados que serão usados para previsão
        self._period_ = top_corr.index[self.posicao]

        # Outras informações sobre o modelo 'treinado'
        # Usando sufixo _ semelhante ao scikit-learn
        self.correlacao_ = top_corr.iloc[self.posicao]
        self.correlacao_outros_ = self.df_correlacao.loc[top_corr.index[self.posicao]]
        self.mes_final_periodo_ = self._period_.strftime('%Y-%m')

        # Retorna o próprio objeto para o caso de ser encadeado com .predict()
        return self


    def predict(self,
                num_meses: Optional[int] = None,
                ) -> pd.DataFrame:
        """
        Previsão para os próximos 'num_meses'.

        Parameters
        ----------
        num_meses : int, optional
            Número de meses a serem previstos.
            Se não informado será feita a previsão até final do último ano informado.

        Returns
        -------
        DataFrame
            Previsão para os próximos meses.

        """
        # Mês seguinte ao período selecionado pelo modelo
        try:
            # Não havendo erro supomos que o fit foi realizado
            mes_escolhido_ini = self._period_ + 1
        except TypeError:
            # Podemos futuramente usar o erro sklearn.exceptions.NotFittedError,
            # mas para simplificar:
            raise Exception("Realizar o fit do modelo antes") from None

        # Primeiro mês a ser previsto
        next_month = self.df_base.index[-1] + 1

        # Se num_meses não for informado vai o final do ano
        num_meses = num_meses if num_meses else (13 - mes_escolhido_ini.month)

        # Dados do período escolhido
        df_escolhido = self.df_base.loc[mes_escolhido_ini:].iloc[:num_meses]

        # Ajusta o index para o novo período
        df_trecho_ajust = df_escolhido.copy()
        df_trecho_ajust.index = pd.period_range(next_month,
                                                periods=len(df_trecho_ajust),
                                                freq='M')

        return df_trecho_ajust


class CorrelacaoAmplitude:
    """Modelo de previsão de vazões usando testes de correlação e amplitude."""

    # pylint: disable=too-many-instance-attributes

    def __init__(self,
                 coluna: int,
                 anos_ignorados: list[int],
                 max_lt_min: int = 80,
                 max_gt_max: int = 80,
                 ):
        """
        Criação do modelo.

        Parameters
        ----------
        coluna : int
            Coluna a ser usada para ordenação das maiores correlações.
        anos_ignorados : list
            Anos a serem rejeitados.
        max_lt_min : int, optional
            Número máximo de postos com amplitude menor que a min histórica.
            The default is 80.
        max_gt_max : int, optional
            Número máximo de postos com amplitude maior que a max histórica.
            The default is 80.

        """
        self.coluna = coluna
        self.anos_ignorados = anos_ignorados
        self.max_lt_min = max_lt_min
        self.max_gt_max = max_gt_max

        # Atributos que serão definidos apenas ao realizar o fit
        self.df_base = None
        self.df_correlacao = None
        self.ratio_mes = None
        self.correlacao_ = None
        self.correlacao_outros_ = None
        self.period_escolhido_ini_ = None
        self.ano_escolhido_ = None
        self.anos_rejeitados_ = None
        self.amplitudes_ = None
        self.gt_max_ = None
        self.lt_min_ = None
        self.posicao_ = None


    def fit(self, df_base: pd.DataFrame) -> 'CorrelacaoAmplitude':
        """
        Cálculo das correlações.

        Parameters
        ----------
        df_base : DataFrame
            Dados históricos para cálculo das correlações.

        """
        self.df_base = df_base.copy()
        self.df_correlacao = calc_corr_last12(df_base)

        # Melhores correlações para determinada coluna
        top_corr = self.df_correlacao[self.coluna].sort_values(ascending=False)

        last_period = self.df_base.index[-1]

        # Razão entre o valor atual e o valor do mês anterior
        df_ratio = self.df_base / self.df_base.shift(-1)
        df_ratio = df_ratio[(0 < df_ratio) & (df_ratio < np.Inf)]
        self.ratio_mes = df_ratio[df_ratio.index.month == last_period.month]

        self.amplitudes_ = pd.DataFrame()
        self.amplitudes_['min'] = self.ratio_mes.min()
        self.amplitudes_['max'] = self.ratio_mes.max()

        # Dados que serão usados para previsão
        self.anos_rejeitados_ = []
        for posicao in range(1, len(top_corr)):
            _period = top_corr.index[posicao]
            next_period = _period + 1

            candidato = self.df_base.loc[_period + 1]

            new_ratio = candidato / self.df_base.iloc[-1]

            gt_max = (new_ratio > self.amplitudes_['max']).sum()
            lt_min = (new_ratio < self.amplitudes_['min']).sum()

            # Verifica se passou o limite da quantidade de amplitudes
            # maior que a máxima histórica
            if gt_max > self.max_gt_max:
                self.anos_rejeitados_.append(
                    {'ano': next_period.year,
                     'correlacao': top_corr.iloc[posicao],
                     'motivo': f'gt_max = {gt_max} (> {self.max_gt_max})'})
                continue

            # Verifica se passou o limite da quantidade de amplitudes
            # menor que a mínima histórica
            if lt_min > self.max_lt_min:
                self.anos_rejeitados_.append(
                    {'ano': next_period.year,
                     'correlacao': top_corr.iloc[posicao],
                     'motivo': f'lt_min = {lt_min} (> {self.max_lt_min})'})
                continue

            # Verifica se o ano deve ser ignorado (por já ter sido utilizado)
            if next_period.year in self.anos_ignorados:
                self.anos_rejeitados_.append(
                    {'ano': next_period.year,
                     'correlacao': top_corr.iloc[posicao],
                     'motivo': 'ano utilizado em outro arquivo'})
                continue

            self.posicao_ = posicao
            self.period_escolhido_ini_ = next_period
            self.ano_escolhido_ = next_period.year
            self.amplitudes_['escolhido'] = new_ratio
            self.gt_max_ = gt_max
            self.lt_min_ = lt_min
            break

        # Outras informações sobre o modelo 'treinado'
        # Usando sufixo _ semelhante ao scikit-learn
        self.correlacao_ = top_corr.iloc[self.posicao_]
        self.correlacao_outros_ = self.df_correlacao.loc[top_corr.index[self.posicao_]]

        # Retorna o próprio objeto para o caso de ser encadeado com .predict()
        return self


    def predict(self,
                num_meses: Optional[int] = None,
                ) -> pd.DataFrame:
        """
        Previsão para os próximos 'num_meses'.

        Parameters
        ----------
        num_meses : int, optional
            Número de meses a serem previstos.
            Se não informado será feita a previsão até final do último ano informado.

        Returns
        -------
        DataFrame
            Previsão para os próximos meses.

        """
        # Mês selecionado pelo modelo para iniciar o preenchimento
        try:
            # Não havendo erro supomos que o fit foi realizado
            mes_escolhido_ini = self.period_escolhido_ini_
        except TypeError:
            # Podemos futuramente usar o erro sklearn.exceptions.NotFittedError,
            # mas para simplificar:
            raise Exception("Realizar o fit do modelo antes") from None

        # Primeiro mês a ser previsto
        next_month = self.df_base.index[-1] + 1

        # Se num_meses não for informado vai o final do ano
        num_meses = num_meses if num_meses else (13 - mes_escolhido_ini.month)

        # Dados do período escolhido
        df_escolhido = self.df_base.loc[mes_escolhido_ini:].iloc[:num_meses]

        # Ajusta o index para o novo período
        df_trecho_ajust = df_escolhido.copy()
        df_trecho_ajust.index = pd.period_range(next_month,
                                                periods=len(df_trecho_ajust),
                                                freq='M')

        return df_trecho_ajust
