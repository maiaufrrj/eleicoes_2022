import requests
import pandas as pd

def consulta_por_estado(uf):
    r = requests.get(f'https://infograficos-eleicoes-oglobo.s3.amazonaws.com/2022/1-turno/mapa/presidente/municipios/{uf}.json')
    data = r.json().get('m')
    lista_municipio = []
    lista_candidato = []
    lista_voto = []
    for cidade in range(len(data)):
        for cand in range(len(data[cidade].get('c'))):
            lista_municipio.append(data[cidade].get('nm'))
            lista_candidato.append(data[cidade].get('c')[cand].get('nc'))
            lista_voto.append(data[cidade].get('c')[cand].get('v'))
    data= pd.DataFrame()
    data['municipio']=lista_municipio
    data['candidato']=lista_candidato
    data['qnt_votos']=lista_voto
    return data

def create_dataframe():
    lista_uf = ['AC','AL','AP','AM',
                'BA','CE','DF','ES',
                'GO','MA','MT','MS',
                'MG','PA','PB','PR',
                'PE','PI','RJ','RN',
                'RS','RO','RR','SC',
                'SP','SE','TO']
    data= pd.DataFrame()
    for uf in lista_uf:
        df=consulta_por_estado(uf=uf)
        df.insert(loc=0,column='uf', value=uf)
        data=pd.concat([data,df],axis=0)
    return data

data=create_dataframe()
data.to_excel('resultados_eleicoes_2022_turno1.xlsx', index=False)