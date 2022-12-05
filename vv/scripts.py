
# -*- coding: utf-8 -*-
"""Funções para uso direto dos scripts."""
from pathlib import Path
import pandas as pd
from tqdm import tqdm
from extensor_vazoes.vazoes_txt import VazoesTxt
from extensor_vazoes.modelos import CorrelacaoAmplitude
def vaz20(pasta_entrada: Path,
          max_lt_min: int = 80,
          max_gt_max: int = 80) -> dict:
    """
    Completa os arquivos de vazões usando CorrelacaoAmplitude.
    Parameters
    ----------
    pasta_entrada : Path
        Pasta onde estão os arquivos a serem analisados.
    max_lt_min : int, optional
        Número máximo de postos com amplitude menor que a min histórica.
        The default is 80.
    max_gt_max : int, optional
        Número máximo de postos com amplitude maior que a max histórica.
        The default is 80.
    Returns
    -------
    dict
        Dicionário com os objetos 'modelo' utilizados.
    """
    # Postos a verificar as correlações
    postos_corr = {
        6: 'FURNAS',
        74: 'GBM',
        169: 'SOBRADINHO',
        275: 'TUCURUI',
        }
    pasta_saida = pasta_entrada / 'saida_vaz20'
    try:
        # Criação da pasta de saída
        pasta_saida.mkdir()
    except FileExistsError:
        # Limpeza da pasta de saída se ela já existia
        for arquivo in pasta_saida.glob('*.txt'):
            if arquivo.is_file():
                arquivo.unlink()
    # Arquivos que serão analisados
    # (posteriormente pode ser ordenado conforme preferência)
    arquivos = list(pasta_entrada.glob('*.txt'))
    # Armazena dados de anos já usados para não repetir
    anos_usados = []
    # Armazena os resultados dos modelos
    result_models = {}
    # Barra de progresso
    with tqdm(total=len(arquivos) * len(postos_corr)) as pbar:
        for arquivo in arquivos:
            # Criação do objeto de vazões
            vazoes = VazoesTxt(arquivo)
            for posto, nome_posto in postos_corr.items():
                # Criação do modelo.
                model = CorrelacaoAmplitude(posto,
                                            anos_usados,
                                            max_lt_min,
                                            max_gt_max,
                                            )
                # Parametrização do modelo
                try:
                    model.fit(vazoes.df_period)
                except Exception:
                    print(f'Não foi possível o fit para {arquivo.stem}'
                          f'-{nome_posto}')
                    continue
                # Predição para um novo período
                novo_trecho = model.predict()
                # Junção do período do arquivo com o período previsto
                vazoes_new = vazoes.add_novo_periodo(novo_trecho)
                # Salva novo arquivo de vazões no formato txt
                newfile = (f'{arquivo.stem}-{nome_posto}'
                           f'-{model.ano_escolhido_}.txt')
                vazoes_new.salvar_txt(pasta_saida / newfile)
                # Guarda ano usado para não repetir na próxima iteração
                anos_usados.append(model.ano_escolhido_)
                # Salva modelo utilizado para relatório
                result_models[newfile] = model
                # Atualiza barra de progresso
                pbar.update(1)
    # Dados principais dos modelos usados, para registro em log
    dados = []
    for nome, model in result_models.items():
        dado = {'arquivo': nome,
                'pos_topn_corr': model.posicao_,
                'correlacao': model.correlacao_,
                'lt_min': model.lt_min_,
                'gt_max': model.gt_max_,
                }
        dados.append(dado)
    relatorio = pd.DataFrame(dados).set_index('arquivo')
    # Escreve os resultados principais dos modelos em arquivo
    with open(pasta_entrada / 'vaz20.log', 'w') as file:
        file.write(str(relatorio))
        file.write('\n')
    # Mostra na tela
    print(relatorio)
    return result_models
