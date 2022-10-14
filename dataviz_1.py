#usar o kepler.gl para gerar mapas das eleicoes

import pandas as pd
import numpy as np

#-------------------------------------------
# #carregando geolocalizacao de cada municipio
# geodata=pd.read_csv('geodata_municipios.csv')

# #list(geodata)
# #renomear colunas


# cols={'nome':'cidade',
#       'latitude':'lat',
#       'longitude':'lon',
#       }
# geodata.rename(columns=cols,inplace=True)
# geodata=geodata[['cidade','lat','lon']]

# #tratar nomes dos municipios para facilitar merge com os dados do TSE
# geodata['cidade'] = geodata['cidade'].str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')

# #letra maúscula e aparando espaços sobressalentes
# geodata['cidade'] = geodata['cidade'].str.upper().str.strip()

#-------------------------------------------
#carregando dados do TSE
tse_data = pd.read_csv('resultado-município_presidente_2022.csv',encoding='latin1',delimiter=';')

#list(tse_data)
#renomear colunas
cols={'sg_uf':'uf',
      'nm_municipio':'cidade',
      'nm_urna_candidato':'candidato',
      'qt_votos_nom_validos':'votos_validos', #votos em cada candidato
      'qt_votos_concorrentes':'votos_concorrentes', #votos que totais esperados por cidade
      }

tse_data.rename(columns=cols,inplace=True)
tse_data=tse_data[['uf','cidade','candidato','votos_validos','votos_concorrentes']]

#tratar nomes dos municipios para facilitar merge com os dados de localização
#tse_data['cidade'] = tse_data['cidade'].str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')

#letra maúscula e aparando espaços sobressalentes
#tse_data['cidade'] = tse_data['cidade'].str.upper().str.strip()

#data=tse_data.merge(geodata,on='cidade',how='left')

#data.lat.isna().sum()
#data.lat.notna().sum()

#data_na=data.loc[data.lat.isna()]
#data_na=data_na.cidade.unique()


# como percebemos que há uma quantidade grande de cidades que não há um merge perfeito,
# vamos explorar uma tentativa com o geopy, mas utilizando os nomes de cidades originais do TSE
lista_cidades=tse_data[['uf','cidade']]

#chave para evitar perder cidades com nomes iguais em estados diferentes
lista_cidades['chave']=lista_cidades.uf+'_'+lista_cidades.cidade
lista_cidades.drop_duplicates(subset='chave',inplace=True)
lista_cidades=lista_cidades[['uf','cidade']]

from geopy.geocoders import Nominatim

# inicializando a API Nominatim
geolocator = Nominatim(user_agent="MyApp")

def localizacao_cidades(data=lista_cidades):
    '''
    Parameters
    ----------
    data : dataframe com lista de cidades 
           a serem pesquisadas

    Returns
    -------
    data: dataframe com colunas 'lat' e 'lon' resultantes da pesquisa

    '''
    lista_lat=[]
    lista_lon=[]    
    for i in range(len(data)):
        print(i)
        if data.uf.iloc[i]!='ZZ':
            try:
                location = geolocator.geocode(f'{data.cidade.iloc[i]}, {data.uf.iloc[i]}, Brazil')
                lista_lat.append(location.latitude)
                lista_lon.append(location.longitude)
            except:
                lista_lat.append(np.nan)
                lista_lon.append(np.nan)
        else:
            try:
                location = geolocator.geocode(f'{data.cidade.iloc[i]}')
                lista_lat.append(location.latitude)
                lista_lon.append(location.longitude)
            except:
                lista_lat.append(np.nan)
                lista_lon.append(np.nan)
                
    data['lat']=lista_lat
    data['lon']=lista_lon
    return data

lista_cidades=localizacao_cidades(lista_cidades)


# quantificar dados não localizados
lista_cidades.lat.isna().sum()
lista_cidades.loc[lista_cidades.lat.isna()]['cidade']

#consultas manuais no google maps
def atualizar_geolocalizacao(data, city_dict):
    mask=data.loc[data.cidade==list(city_dict.keys())[0]]        
    mask['lat'] = list(city_dict.values())[0][0]
    mask['lon'] = list(city_dict.values())[0][1]
    data = data.loc[data.cidade!='KUAITE']
    data = pd.concat([data,mask],axis=0)
    return data

lista_cidades = atualizar_geolocalizacao(data=lista_cidades,
                                         city_dict={'KUAITE':[29.376781916563314, 47.97722248732804]})
lista_cidades = atualizar_geolocalizacao(data=lista_cidades, 
                                         city_dict={'ST GEORGES DE LOYAPOCK':[3.8878237432043137,-51.80264910224718]})

lista_cidades['chave']=lista_cidades.uf+'_'+lista_cidades.cidade
lista_cidades.drop_duplicates(subset=['chave'],inplace=True)
del lista_cidades['chave']


city_frame = {'62205': ['ZZ','KUAITE', 29.376781916563314, 47.97722248732804]}
city_frame = pd.DataFrame.from_dict(city_frame, orient='index',columns=['uf','cidade','lat','lon'])
lista_cidades = pd.concat([lista_cidades,city_frame],axis=0)


lista_cidades.dropna(inplace=True)
city_frame = {'62920': ['ZZ','ST GEORGES DE LOYAPOCK', 3.8878237432043137,-51.80264910224718]}
city_frame = pd.DataFrame.from_dict(city_frame, orient='index',columns=['uf','cidade','lat','lon'])
lista_cidades = pd.concat([lista_cidades,city_frame],axis=0)
lista_cidades.index=lista_cidades.index.astype(int)
lista_cidades.sort_index(inplace=True)
lista_cidades.to_excel('geolocation_cidades.xlsx',index=False)

lista_cidades.to_csv('geolocation_cidades.csv',index=False)


lista_cidades['chave']=lista_cidades.uf+'_'+lista_cidades.cidade
tse_data['chave']=tse_data.uf+'_'+tse_data.cidade
tse_data2 = tse_data.merge(lista_cidades[['chave','lat','lon']],on='chave',how='left')
del tse_data2['chave']

tse_data2.to_csv('tse_data2.csv',index=False)


# carregar dados processados e tratar
data=pd.read_csv('detalhe_votacao.csv',encoding='latin1',delimiter=';')
cols={'sg_uf':'uf',
      'nm_municipio':'cidade',
      'qt_aptos_tot':'aptos',
      'qt_comparecimento':'comparecimento',
      'qt_votos_brancos':'votos_brancos',
      'qt_votos_nulos':'votos_nulos',
      'qt_votos_validos':'votos_validos'
      }

data.rename(columns=cols,inplace=True)
data=data[['uf','cidade','aptos','comparecimento','votos_validos','votos_brancos','votos_nulos']]
data['abstencao']=data['aptos']-data['comparecimento']
data['pct_abstencao']=data['abstencao']/(data['aptos'])

data['chave']=data['uf']+'_'+data['cidade']
tse_data2['chave']=tse_data2['uf']+'_'+tse_data2['cidade']

list(data)

data=data.merge(tse_data2[['chave','lat','lon']].groupby('chave').first(),on='chave',how='left')
del data['chave']

data.to_csv('abstencao_cidades_turno1.csv',index=False)

# função para testar se dados de cidades com uf!='ZZ'
# estao conforme limites do território nacional

#ponto mais ao setentrional brasil:
#max_lat = 5.277714261725679
#max_lon = -60.202784632252666

#ponto mais ao norte brasil: arroio do chuí
# min_lat = -33.750931435813015
# min_lon = -53.39444814631504

#ponto mais a oeste brasil: Nascente do Rio Moa
#-7.533092404498265, -73.98273842289896

#ponto mais a leste do brasil: ponta do seixas
#-7.148266006617044, -34.796213862425525





