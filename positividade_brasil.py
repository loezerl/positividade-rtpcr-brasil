import pandas as pd
import streamlit as st
import numpy as np
import altair as alt

FAIXA_ETARIA = {
    "0 a 4 anos": [False, 'pcr-positivo-0a4-final'],
    "5 a 9 anos": [False, 'pcr-positivo-5a9-final'],
    "10 a 14 anos": [False, 'pcr-positivo-10a14-final'],
    "15 a 19 anos": [False, 'pcr-positivo-15a19-final'],
    "20 a 29 anos": [False, 'pcr-positivo-20a29-final'],
    "30 a 39 anos": [False, 'pcr-positivo-30a39-final'],
    "40 a 49 anos": [False, 'pcr-positivo-40a49-final'],
    "50 a 59 anos": [False, 'pcr-positivo-50a59-final'],
    "60 a 69 anos": [False, 'pcr-positivo-60a69-final'],
    "70 a 79 anos": [False, 'pcr-positivo-70a79-final'],
    "Maior que 80 anos": [False, 'pcr-positivo-80a999-final']
}

st.title("PCR-Positivo do Brasil")
st.write("""
Esse relatório consiste em mostrar os testes positivos para covid-19 listados na API [e-SUS Notifica], SRAG2020 e SRAG2021.
As informações contidas no relatório são:
- Quantidade de RT-PCR positivos por dia
- Quantidade de RT-PCR negativos por dia.
- Quantidade de RT-PCR positivos nas faixas etárias: [0, 4], [5, 9], [10, 14], [15, 19], 
[20, 29], [30, 39], [40, 49], [50, 59] [60, 69], [70, 79], [80, 999].

Com base nessas informações é possível analisar graficamente quais faixas etárias estão testando positivo para o novo coronavírus.
Por enquanto, o gráfico é contemplando o território brasileiro.

Autor - Lucas Loezer (loezer.lucas@gmail.com) | https://github.com/loezerl/
""")
st.write("Abaixo o percentual de PCR-Positivo distribuído por data e faixas etárias")

df = pd.read_csv("eSUS_SRAG_Pronta_20210703.csv", sep=',')

df.replace(np.nan, 0, inplace=True)
df['Data'] = pd.to_datetime(df['Data'], format="%Y-%m-%d")
df = df[df['Data'] < pd.to_datetime("2021-06-30")]

col1, col2 = st.beta_columns(2)

col1.subheader("Deseja filtrar por alguma faixa etária?")
for k in FAIXA_ETARIA:
    FAIXA_ETARIA[k][0] = col1.checkbox(k)
filtro_idades = []
for k in FAIXA_ETARIA:
    if FAIXA_ETARIA[k][0]:
        filtro_idades.append(FAIXA_ETARIA[k][1])

col2.subheader("Deseja filtrar por algum período específico?")
d3 = col2.date_input("Período selecionado", [])
if len(d3) > 0:
    df = df[df['Data'] >= pd.to_datetime(str(d3[0]))]
    df = df[df['Data'] <= pd.to_datetime(str(d3[1]))]
    col2.write("Início: {} | Fim: {}".format(str(d3[0]), str(d3[1])))


df['pcr'] = df['pcr-positivo-final'] + df['pcr-negativo-final']
df = df[df['pcr-positivo-final'] != 0]
ignore_columns = [
    'Data',
    'pcr-positivo-final',
    'pcr-negativo-final',
    'pcr',
    'obito-final',
]
df = df[ignore_columns + filtro_idades]
st.write(df.tail(100))
drop_columns = []
plot_columns = []
## Percentual de positividade por faixa etária
for c in df.columns.values:
    if not(c in ignore_columns):
        df[c + "_percent"] = ((df[c]/df['pcr-positivo-final'])*100).round(3)
        drop_columns.append(c)
        plot_columns.append(c + "_percent")
## Percentual de positividade por teste realizado
df["positividade"] = ((df['pcr-positivo-final'] / df['pcr']) * 100).round(3)
df_plot = df.set_index('Data')
st.subheader("Gráfico de positivos (%) por faixa etária")
st.area_chart(df_plot[plot_columns])
st.subheader("Gráfico de positividade (%)")
df_plot['media_movel_7d'] = df_plot['positividade'].rolling(7).mean()
st.line_chart(df_plot[['positividade', 'media_movel_7d']])

df_plot = df.set_index('Data')
st.subheader("Gráfico de RT-PCRs realizados")
df_plot['media_movel_7d'] = df_plot['pcr'].rolling(7).mean()
st.line_chart(df_plot[['pcr', 'media_movel_7d']])

for pc in plot_columns:
    st.subheader("Percentual {}".format(pc[:-14]))
    df_plot = df.set_index('Data')
    df_plot = df_plot[[pc]]

    coefficients, residuals, _, _, _ = np.polyfit(range(len(df_plot.index)),df_plot,1,full=True)
    mse = residuals[0]/(len(df_plot.index))
    nrmse = np.sqrt(mse)/(df_plot.max() - df_plot.min())
    df_plot['trend_line'] = pd.Series(np.squeeze([coefficients[0]*x + coefficients[1] for x in range(len(df_plot))]), index=df_plot.index)
    df_plot['media_movel_7d'] = df_plot[pc].rolling(7).mean()

    st.line_chart(df_plot[[pc] + ['trend_line', 'media_movel_7d']])
