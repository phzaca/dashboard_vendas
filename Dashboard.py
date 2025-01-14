import streamlit as st 
import pandas as pd 
import plotly.express as px 
import requests 

st.set_page_config(layout= 'wide') #ocupar a página toda, tem q ser o primeiro código st. 
                                   # se não dá um erro com a barra lateral

def formata_numero(valor, prefixo = ''):                    #formatação do numero
    for unidade in ['', 'mil']:
        if valor<1000:
            return f'{prefixo} {valor:.2f} {unidade}'
        valor /=1000
    return f'{prefixo} {valor:.2f} milhões'


url = 'https://labdados.com/produtos'                       #importação da tabela
regioes = ['Brasil','Centro-Oeste','Nordeste','Norte','Sudeste','Sul']

                                                            #adicionando filtros direto na url
st.sidebar.title('Filtros')
regiao = st.sidebar.selectbox('Região', regioes)

if regiao == 'Brasil':
    regiao = ''

todos_anos = st.sidebar.checkbox('Dados de todo o Período', value=True)
if todos_anos:
    ano = ''
else:
    ano = st.sidebar.slider('Ano', 2020,2023)
    
query_strig = {'regiao': regiao.lower(), 'ano':ano}

                                #aplicação do filtro aqui
response = requests.get(url,params= query_strig)                #requests só entra pq o pandas n abre Json de url, só do local. 
dados = pd.DataFrame.from_dict(response.json())   #requests "baixa o arquivo na memória" para o pandas poder abrir como lista ou dicionário
dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format= '%d/%m/%Y') #ajustando  o formato da coluna para dt

filtro_vendedores = st.sidebar.multiselect('Vendedores', dados['Vendedor'].unique())
if filtro_vendedores:
    dados = dados[dados['Vendedor'].isin(filtro_vendedores)]

## tabelas receita
receita_estados = dados.groupby('Local da compra')[['Preço']].sum()
receita_estados = dados.drop_duplicates(subset= 'Local da compra')[['Local da compra','lat','lon']].merge(receita_estados, left_on='Local da compra', right_index= True).sort_values('Preço', ascending= False)
#-
receita_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq= 'M'))['Preço'].sum().reset_index()
receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
receita_mensal['Mes'] = receita_mensal['Data da Compra'].dt.month
#-
receita_categoria = dados.groupby('Categoria do Produto')[['Preço']].sum().sort_values('Preço', ascending= False)

## tabelas de quantidade de vendas 
#-estados
contagem_estados = dados.groupby('Local da compra')[['Preço']].count()
contagem_estados = dados.drop_duplicates(subset= 'Local da compra')[['Local da compra','lat','lon']].merge(contagem_estados, left_on='Local da compra', right_index= True).sort_values('Preço', ascending= False)
contagem_estados = contagem_estados.rename(columns={'Preço':'Quantidade de vendas'})
#-mensal
quantidade_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq= 'M'))['Preço'].count().reset_index()
quantidade_mensal['Ano'] = quantidade_mensal['Data da Compra'].dt.year
quantidade_mensal['Mes'] = quantidade_mensal['Data da Compra'].dt.month
quantidade_mensal = quantidade_mensal.rename(columns={'Preço':'Quantidade de vendas'})
#-categorias
quantidade_categoria = dados.groupby('Categoria do Produto')[['Preço']].count().sort_values('Preço', ascending= False)
quantidade_categoria = quantidade_categoria.rename(columns={'Preço':'Quantidade de vendas'})


## tabelas vendedores
vendedores = pd.DataFrame(dados.groupby('Vendedor')['Preço'].agg(['sum','count'])) #gerando uma tabela com 
                                                                                    #nome dos vendedores, soma e contagem
                                                                                    ## por isso q entrou uma lista no agg

## Gráficos 
#-
fig_map_receita = px.scatter_geo(receita_estados, 
                                 lat = 'lat',
                                 lon = 'lon',
                                 scope ='south america',
                                 size= 'Preço',
                                 template= 'seaborn',
                                 hover_name='Local da compra',
                                 hover_data={'lat':False, 'lon':False},
                                 title='Receita por estado')
#-
fig_receita_mensal = px.line(receita_mensal,
                             x = 'Mes',
                             y = 'Preço',
                             markers = True,
                             range_y=(0, receita_mensal.max()),
                             color ='Ano',                             
                             line_dash='Ano',
                             title='Receita mensal')
fig_receita_mensal.update_layout(yaxis_title = 'Receita')
#-
fig_receita_estados = px.bar(receita_estados.head(),
                            x='Local da compra',
                            y= 'Preço',
                            text_auto=True,
                            title='Top estados (receita)')
fig_receita_estados.update_layout(yaxis_title = 'Receita')
#-
fig_receita_categorias = px.bar(receita_categoria,
                                text_auto = True,
                                title = 'Receita por categoria')
fig_receita_categorias.update_layout(yaxis_title = 'Receita')
#-gráfico mapa quantidade
fig_map_contagem = px.scatter_geo(contagem_estados, 
                                 lat = 'lat',
                                 lon = 'lon',
                                 scope ='south america',
                                 size= 'Quantidade de vendas',
                                 template= 'seaborn',
                                 hover_name='Local da compra',
                                 hover_data={'lat':False, 'lon':False},
                                 title='Vendas por Estado')
#-gráfico de vendas mensais
fig_quantidade_mensal = px.line(quantidade_mensal,
                             x = 'Mes',
                             y = 'Quantidade de vendas',
                             markers = True,
                             range_y=(0, quantidade_mensal.max()),
                             color ='Ano',                             
                             line_dash='Ano',
                             title='Quantidade de vendas mensais')
fig_quantidade_mensal.update_layout(yaxis_title = 'Quantidade')
#-gráfico estados que mais venderam
fig_contagem_estados = px.bar(contagem_estados.sort_values('Quantidade de vendas', ascending = False).head(),
                              x = 'Local da compra',
                              y= 'Quantidade de vendas',
                              title = 'Estados que mais venderam')
fig_contagem_estados.update_layout(yaxis_title = 'Quantidade')
#-gráfico quantidade categoria
fig_quantidade_categoria = px.bar(quantidade_categoria,
                              x = quantidade_categoria.index,
                              y = 'Quantidade de vendas',
                              title = 'Quantidade de vendas por categoria')
fig_quantidade_categoria.update_layout(yaxis_title = 'Quantidade')




#vizualização no streamlit
##titulo
st.title("DASHBOARD DE VENDAS :shopping_trolley: ")
##abas
aba1, aba2, aba3 = st.tabs(['Receita', 'Quantidade de vendas ', 'Vendedores'])
##colunas dentro das abas
with aba1: #Receita
    coluna1, coluna2, = st.columns(2)
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_map_receita, use_container_width=True)
        st.plotly_chart(fig_receita_estados, use_container_width=True)
    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        st.plotly_chart(fig_receita_mensal, use_container_width= True)
        st.plotly_chart(fig_receita_categorias,use_container_width=True)

with aba2: #Qntd vendas 
    coluna1, coluna2, = st.columns(2)
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_map_contagem, use_container_width=True )
        st.plotly_chart(fig_contagem_estados, use_container_width=True)
    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        st.plotly_chart(fig_quantidade_mensal, use_container_width=True)
        st.plotly_chart(fig_quantidade_categoria, use_container_width=True)
        
with aba3: #vendedores
    qtd_vendedores = st.number_input('Quantidade de vendedores', 2,10,5)
    coluna1, coluna2, = st.columns(2)
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        fig_receita_vendedores = px.bar(vendedores[['sum']].sort_values('sum', ascending = False).head(qtd_vendedores),
                                        x='sum', y=vendedores[['sum']].sort_values('sum', ascending = False).head(qtd_vendedores).index,
                                        text_auto=True,
                                        title=f'Top {qtd_vendedores} vendedores (receita)')
        # fig_receita_vendedores.update_layout(
            # yaxis_title = 'Nomes',
            # xaxis = 'Receita')
        st.plotly_chart(fig_receita_vendedores)
    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        fig_vendas_vendedores = px.bar(vendedores[['count']].sort_values('count', ascending = False).head(qtd_vendedores),
                                        x='count', y=vendedores[['count']].sort_values('count', ascending = False).head(qtd_vendedores).index,
                                        text_auto=True,
                                        title=f'Top {qtd_vendedores} vendedores (quantidade de vendas)')
        # fig_vendas_vendedores.update_layout(
            # yaxis_title='Nomes',
            # xaxis_title='quantidade')
        st.plotly_chart(fig_vendas_vendedores)



##tabela
# st.dataframe(dados)



## MANUAL
####.\venv\Scripts/activate
###### para tornar on as coisas
### streamlit run Dashboard.py 
#### para iniciar a brincadeira