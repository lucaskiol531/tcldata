import streamlit as st
from streamlit_login_auth_ui.widgets import __login__
import requests
import pandas as pd
import json
import sqlite3
import io
from datetime import datetime as dt
from datetime import timedelta 
import altair as alt

__login__obj = __login__(auth_token = "courier_auth_token",
                    company_name = "Shims",
                    width = 200, height = 250,
                    logout_button_name = 'Sair', hide_menu_bool = False,
                    hide_footer_bool = False,
                    lottie_url = 'https://assets2.lottiefiles.com/packages/lf20_jcikwtux.json')

LOGGED_IN= __login__obj.build_login_ui()
username= __login__obj.get_username()


if LOGGED_IN == True:
    data = st.session_state['data']
    topo1,topo2 = st.columns(2)
    with topo1:
        dias_analise = st.selectbox(
            'Qual o périodo de análise?',
            ('1D','7D','14D','28D','Personalizado')    
        )
    with topo2:
        canal_venda = st.multiselect(
            'Qual canal deseja analisar?',
            list(set(data['tipoIntegracao'])),
            default=list(set(data['tipoIntegracao']))
        )
    
    col1, col2, col3 = st.columns(3)
    
    
    
    if dias_analise == 'Personalizado':
        data_inicial = st.date_input('Data Inicial')    
        data_final = st.date_input('Data Final')
    
    def formatar_data(data_string):
        if isinstance(data_string, pd.Timestamp):
            # Converte Timestamp para string no formato '%Y-%m-%d'
            data_string = data_string.strftime("%Y-%m-%d")
        try:
            # Tenta converter a data para o formato '%Y-%m-%d'
            data_obj = dt.strptime(data_string, "%Y-%m-%d")
            return data_obj
        except ValueError:
            # Se não for possível converter, retorna a data original
            return data_string
    data['data'] = data['data'].apply(lambda x:formatar_data(x))
    data = data[['data','numero','totalvenda','item.precocusto','tipoIntegracao']]
    data = data.groupby('numero', as_index=False).agg({
    'data': 'first', 
    'totalvenda': 'sum', 
    'item.precocusto': 'sum',
    'tipoIntegracao': 'first'
})
    st.write(data)
    def data_analise(dias_analise,data_inicial = None,data_final = None):
        if dias_analise != 'Personalizado':
            data_analise =(dt.today() - timedelta(days=int(dias_analise.rstrip('D')))).strftime("%Y/%m/%d")
            analise = data[(data['data'] > str(data_analise))]
        else:
            data_inicial = data_inicial.strftime('%Y-%m-%d')
            data_final = data_final.strftime('%Y-%m-%d')

            # Filtra o DataFrame com base nas datas convertidas para strings
            analise = data[(data['data'] >= data_inicial) & (data['data'] <= data_final)]
        return analise
    if dias_analise != 'Personalizado':
        analise =  data_analise(dias_analise)
    else:
        analise = data_analise(dias_analise,data_inicial,data_final)
    
    def canal_analise(canal_venda):
        canal = analise[analise['tipoIntegracao'].isin(canal_venda)]
        return canal
    analise = canal_analise(canal_venda)
    
    with col1:
        st.metric('Faturamento', 'R$' + str(round(sum(analise['totalvenda']), 2)))
    with col2:
        st.metric('Quantidade de Vendas',len(analise['numero']))
    with col3:
        st.metric('Custos dos produtos','R$' + str(round(sum(analise['item.precocusto']), 2)))
    grafico = alt.Chart(analise).mark_bar().encode(
    x='data:T',
    y='totalvenda:Q',
    color=alt.Color('tipoIntegracao:N')).properties(width=600, height=400)

    # Mostrando o gráfico no Streamlit
    st.altair_chart(grafico)
            
        
        