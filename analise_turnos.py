import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.linear_model import LinearRegression

turno1 = pd.read_csv('tse_data2.csv',dtype='str')
turno2 = pd.read_excel('resultados_eleicoes_2022_turno2.xlsx')
turno2.rename(columns={'qnt_votos':'votos_validos'},inplace=True)
turno2.rename(columns={'municipio':'cidade'},inplace=True)
turno1['cidade']=turno1['cidade'].str.upper()
turno2['cidade']=turno2['cidade'].str.upper()
turno1['cidade'] = turno1['cidade'].str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')
turno2['cidade'] = turno2['cidade'].str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')
turno1['chave'] = turno1['uf']+"_"+turno1['cidade']
turno2['chave'] = turno2['uf']+"_"+turno2['cidade']

turno1['candidato'] = turno1['candidato'].str.upper()
turno2['candidato'] = turno2['candidato'].str.upper()

turno1['votos_validos'] = turno1['votos_validos'].astype(int)
turno2['votos_validos'] = turno2['votos_validos'].astype(int)

def intersection(lst1, lst2):
    return list(set(lst1) & set(lst2))

cidades = intersection(turno1.chave.unique().tolist(),turno2.chave.unique().tolist())

comparativo=pd.DataFrame(cidades,columns=['chave'])
comparativo['votos_concorrentes']=comparativo.merge(turno1.loc[turno1.candidato=='JAIR BOLSONARO'], on='chave', how='left')['votos_concorrentes'].astype(int)
comparativo['bolsonaro_turno1']=comparativo.merge(turno1.loc[turno1.candidato=='JAIR BOLSONARO'],on='chave', how='left')['votos_validos']
comparativo['bolsonaro_turno2']=comparativo.merge(turno2.loc[turno2.candidato=='JAIR BOLSONARO'],on='chave', how='left')['votos_validos']
comparativo['lula_turno1']=comparativo.merge(turno1.loc[turno1.candidato=='LULA'],on='chave', how='left')['votos_validos']
comparativo['lula_turno2']=comparativo.merge(turno2.loc[turno2.candidato=='LULA'],on='chave', how='left')['votos_validos']

comparativo['pct_bolsonaro_turno1']=comparativo['bolsonaro_turno1']/comparativo['votos_concorrentes']
comparativo['pct_bolsonaro_turno2']=comparativo['bolsonaro_turno2']/comparativo['votos_concorrentes']
comparativo['pct_lula_turno1']=comparativo['lula_turno1']/comparativo['votos_concorrentes']
comparativo['pct_lula_turno2']=comparativo['lula_turno2']/comparativo['votos_concorrentes']

comparativo['diff_bolsonaro']=comparativo['bolsonaro_turno2']-comparativo['bolsonaro_turno1']
comparativo['diff_lula']=comparativo['lula_turno2']-comparativo['lula_turno1']
comparativo['pct_diff_bolsonaro']=comparativo['pct_bolsonaro_turno2']-comparativo['pct_bolsonaro_turno1']
comparativo['pct_diff_lula']=comparativo['pct_lula_turno2']-comparativo['pct_lula_turno1']

comparativo.insert(loc=0, column='uf', value=comparativo['chave'].str.split('_',expand=True)[0])
comparativo.insert(loc=1, column='cidade', value=comparativo['chave'].str.split('_',expand=True)[1])

aggregate=[#'min',
           #'max',
           #'mean',
           'median'
           ]

comparativo_uf = comparativo.groupby('uf').agg({'diff_bolsonaro':aggregate,
                                                'diff_lula':aggregate})

comparativo_uf.columns = ["_".join(col) for col in comparativo_uf.columns]

#em quantas cidades os principais candidatos tiveram conversão de votos superior aos de candidatos coadjuvantes no primeiro turno?
#turno1.candidato.unique()
coadjuvantes=turno1.loc[(turno1.candidato!='JAIR BOLSONARO')&(turno1.candidato!='LULA')].groupby('chave',as_index=False)['votos_validos'].sum()
comparativo['sum_coadjuvantes']=comparativo.merge(coadjuvantes,on='chave', how='left')['votos_validos']
comparativo['check_bolsonaro']=np.where((comparativo['diff_bolsonaro']>comparativo['sum_coadjuvantes'])&(comparativo['diff_bolsonaro']>comparativo['diff_lula']),1,0)
comparativo['check_lula']=np.where((comparativo['diff_lula']>comparativo['sum_coadjuvantes'])&(comparativo['diff_bolsonaro']<comparativo['diff_lula']),1,0)
del comparativo['chave']

comparativo['check_bolsonaro'].sum()
comparativo['check_lula'].sum()

comparativo['abstencao_turno1'] = comparativo['votos_concorrentes']-(comparativo['bolsonaro_turno1']-comparativo['lula_turno1'])
comparativo['abstencao_turno2'] = comparativo['votos_concorrentes']-(comparativo['bolsonaro_turno2']-comparativo['lula_turno2'])
comparativo['variacao_abstencao'] = (comparativo['abstencao_turno2']-comparativo['abstencao_turno1'])/comparativo['abstencao_turno1']




comparativo_uf = comparativo.groupby('uf', as_index=False).agg({'check_bolsonaro':'sum',
                                                                'check_lula':'sum',
                                                                'cidade':'nunique'
                                                                })

comparativo_uf['check_bolsonaro']=comparativo_uf['check_bolsonaro']/comparativo_uf['cidade']
comparativo_uf['check_lula']=comparativo_uf['check_lula']/comparativo_uf['cidade']


#regressao linear
reg_bolsonaro = LinearRegression()
reg_bolsonaro = reg_bolsonaro.fit(np.array(comparativo.variacao_abstencao).reshape(-1,1), np.array(np.array(comparativo.pct_diff_bolsonaro)))
reg_bolsonaro = reg_bolsonaro.predict(np.array(comparativo.variacao_abstencao).reshape(-1,1))
reg_lula = LinearRegression()
reg_lula = reg_lula.fit(np.array(comparativo.variacao_abstencao).reshape(-1,1), np.array(np.array(comparativo.pct_diff_lula)))
reg_lula = reg_lula.predict(np.array(comparativo.variacao_abstencao).reshape(-1,1))


fig = make_subplots(rows=1, cols=2, subplot_titles=('Bolsonaro',  'Lula'))
fig.add_trace(go.Scatter(x=comparativo.variacao_abstencao,
                         y=comparativo.pct_diff_bolsonaro,
                         mode = "markers",
                         name="Bolsonaro",
                         showlegend=False,
                         marker_symbol=1,
                         marker_color = "green"), row=1, col=1)

fig.add_trace(go.Scatter(x=comparativo.variacao_abstencao,
                         y=comparativo.pct_diff_lula,
                         mode = "markers",
                         name="Lula",
                         showlegend=False,
                         marker_symbol=1,
                         marker_color = "red"), row=1, col=2)

#adionanando trendlines
fig.add_trace(go.Scatter(x=comparativo.variacao_abstencao,
                         y=reg_bolsonaro,
                         mode = "lines",
                         name="Bolsonaro",
                         showlegend=False,
                         marker_symbol=1,
                         marker_color = "green"), row=1, col=1)

fig.add_trace(go.Scatter(x=comparativo.variacao_abstencao,
                         y=reg_lula,
                         mode = "lines",
                         name="Lula",
                         showlegend=False,
                         marker_symbol=1,
                         marker_color = "red"), row=1, col=2)

fig.update_layout(#title="Dispersao Entre Variacao de Abstencao e Variacao Entre Turnos",
                  yaxis_title="variacao entre turnos (%)",
                  font=dict(size=16))

fig['layout']['xaxis']['title']='variacao de abstencao (%)'
fig['layout']['xaxis2']['title']='variacao de abstencao (%)'

fig.write_html('charts/scatter_variacao_abstencao.html')
