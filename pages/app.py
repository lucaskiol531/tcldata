import streamlit as st
from streamlit_login_auth_ui.widgets import __login__
import requests
import pandas as pd
import json
import sqlite3
import io
__login__obj = __login__(auth_token = "courier_auth_token",
                    company_name = "Shims",
                    width = 200, height = 250,
                    logout_button_name = 'Logout', hide_menu_bool = False,
                    hide_footer_bool = False,
                    lottie_url = 'https://assets2.lottiefiles.com/packages/lf20_jcikwtux.json')

LOGGED_IN= __login__obj.build_login_ui()
username= __login__obj.get_username()

if LOGGED_IN == True:

   #st.markdown("Your Streamlit Application Begins here!")
   #st.markdown(st.session_state)
   #st.write(username)
   conn = sqlite3.connect('users.db')
   cursor = conn.cursor()
   cursor.execute('''
      CREATE TABLE IF NOT EXISTS users (
         id INTEGER PRIMARY KEY AUTOINCREMENT,
         username TEXT,
         apikey TEXT,
         data TEXT
      )
   ''')
   def verificar_apikey(username):
      conn = sqlite3.connect('users.db')
      cursor = conn.cursor()

      # Consulta SQL para verificar se existe um registro com o username fornecido
      cursor.execute('''
         SELECT apikey FROM users
         WHERE username = ?
      ''', (username,))

      # Obtendo o resultado da consulta
      resultado = cursor.fetchone()

      conn.close()

      # Se houver um resultado, significa que o username foi encontrado na tabela
      if resultado is not None:
         return True, resultado[0]  # Retorna True e a apikey associada ao username
      else:
         return ""  # Retorna False se o username não for encontr

   api_key1 = verificar_apikey(username)
   if type(api_key1) == str:
      api_key = st.text_input('Coloque aqui sua API KEY')
   else:
      api_key = st.text_input('Coloque aqui sua API KEY', value=api_key1[1])
   
   def pegar_dados_pedidos():
      data1 = {}
      data2 = []
      for i in range(1,300):
         url = f"https://bling.com.br/Api/v2/pedidos/page={i}/json/"
         apikey = api_key

         params = {
               "apikey": apikey
         }

         response = requests.get(url, params=params)

         data2.append(json.loads(response.text))

         if 'erros' in data2[i - 1]['retorno']:
            break
      data = data2
      #st.write(data)
      pedidos = pd.DataFrame()
      resultados_juncao = []
      df = []
      df1 = []
      df2 = []
      for j in range(len(data)):
         if 'erros' not in data[j]['retorno']:
            for i in range(1,len(data[j]['retorno']['pedidos'])):
               if 'itens' in data[j]['retorno']['pedidos'][i]['pedido'].keys():
                  df0 = pd.json_normalize(data[j]['retorno']['pedidos'][i])
                  df = pd.json_normalize(data[j]['retorno']['pedidos'][i] , record_path = ['pedido', 'itens'], meta = ['pedido'])
                  df1 = pd.json_normalize(df['pedido'])
                  if 'parcelas' in list(data[j]['retorno']['pedidos'][i]['pedido']):
                     df2 = pd.json_normalize(df['pedido'], record_path = ['parcelas'])
                  juncao = df1.join(df).join(df2)
                  resultados_juncao.append(juncao)
         

      pedidos = pd.concat(resultados_juncao)
      pedidos = pedidos.drop(columns=['itens', 'parcelas', 'pedido'])
      return pedidos 
   
   def insert_data(username, apikey, data):
    # Verificar se o usuário já existe na tabela
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    existing_user = cursor.fetchone()
    
    if existing_user is None:
        # O usuário não existe, então inserir os dados
        cursor.execute('''
            INSERT INTO users (username, apikey, data)
            VALUES (?, ?, ?)
        ''', (username, apikey, data))
        conn.commit()
        print("Dados inseridos com sucesso!")
    else:
        # O usuário já existe, então atualizar a coluna 'data'
        cursor.execute('''
            UPDATE users
            SET data = ?
            WHERE username = ?
        ''', (data, username))
        conn.commit()
        print("Dados atualizados com sucesso!")


   def consultar_dados(username, apikey):
      conn = sqlite3.connect('users.db')
      cursor = conn.cursor()
      cursor.execute('''
         SELECT data FROM users
         WHERE username = ? AND apikey = ?
      ''', (username, apikey))
      resultado = cursor.fetchone()
      conn.close()
      if resultado is not None:
         return resultado[0]
      else:
         return None
                             
   
   def pegar_dados_produtos():
      global df 
      data1 = {}
      data2 = []
      for i in range(1,10):
         url = f"https://bling.com.br/Api/v2/produtos/page={i}/json/"
         apikey = api_key

         params = {
               "apikey": apikey
         }

         response = requests.get(url, params=params)

         data2.append(json.loads(response.text))
         if 'erros' in data2[i - 1]['retorno']:
            break
      data = data2
      lista_produtos = [pd.json_normalize(data[k]['retorno']['produtos']) for k in range(len(data)-1)]
      produtos = pd.concat(lista_produtos, ignore_index=True)  
      return produtos
   
   
   
   if st.button('Atualizar'):
      data = pegar_dados_pedidos()
      produtos = pegar_dados_produtos()
      st.write(data)
      st.write(produtos) 
      insert_data(username, api_key, data.to_csv(index=False))
   
   if st.button('Salvar'):
      if consultar_dados(username,api_key) == None:
         insert_data(username, api_key, data.to_csv(index=False))
         data = pegar_dados_pedidos() 
         produtos = pegar_dados_produtos()
         st.write(data) 
         st.write(produtos)
         insert_data(username, api_key, data.to_csv(index=False))
      else:
         data = consultar_dados(username,api_key)
         data = pd.read_csv(io.StringIO(data))
         produtos = pegar_dados_produtos()
         st.write(data) 
         st.write(produtos)
         insert_data(username, api_key, data.to_csv(index=False))
   if api_key != None:
      data = consultar_dados(username,api_key)
      data = pd.read_csv(io.StringIO(data))
      st.session_state['data'] = data
   