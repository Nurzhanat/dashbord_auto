import streamlit as st
import pandas as pd
import plotly.express as px

# Загрузка данных
df = pd.read_csv("jul-07_17-55-24.csv")
df.columns = df.columns.str.strip()  # Убираем пробелы в названиях колонок

# Объединённое поле "Марка Модель"
df["model_full"] = df["Марка"].astype(str) + " " + df["Модель"].astype(str)

# Заголовок
st.title("🚘 Дашборд по авто на перепродажу")

# Фильтры
brands = st.multiselect("Марка", df["Марка"].dropna().unique(), default=None)
cities = st.multiselect("Город", df["Город"].dropna().unique(), default=None)
years = st.slider("Год выпуска", int(df["Год выпуска"].min()), int(df["Год выпуска"].max()), (2015, 2023))


# Применение фильтров
filtered_df = df.copy()
if brands:
    filtered_df = filtered_df[filtered_df["Марка"].isin(brands)]
if cities:
    filtered_df = filtered_df[filtered_df["Город"].isin(cities)]
filtered_df = filtered_df[
    (filtered_df["Год выпуска"] >= years[0]) & (filtered_df["Год выпуска"] <= years[1])
]
# Приведение "Пробег" и "Цена" к числу
filtered_df["Пробег_чисто"] = (
    filtered_df["Пробег"]
    .astype(str)
    .str.replace("км", "", regex=False)
    .str.replace(" ", "")
    .str.replace(",", "")
    .astype(float)
)

filtered_df["Цена"] = (
    filtered_df["Цена"]
    .astype(str)
    .str.replace("₸", "", regex=False)
    .str.replace(" ", "")
    .str.replace(",", "")
    .astype(float)
)

filtered_df["Цена"] = (
    filtered_df["Цена"]
    .astype(str)
    .str.replace("₸", "", regex=False)   # убираем символ тенге (если есть)
    .str.replace("тг", "", regex=False)  # на всякий случай
    .str.replace(" ", "")                # убираем пробелы
    .str.replace(",", "")                # убираем запятые (если 1,000,000)
    .astype(float)
)

# График 1: Гистограмма цен
st.subheader("📉 Распределение цен")
fig1 = px.histogram(filtered_df, x="Цена", nbins=30, title="Цены на авто")
st.plotly_chart(fig1)


# Группировка по оригинальному "Пробег"
grouped = (
    filtered_df.groupby("Пробег")
    .agg({"Цена": "mean", "Пробег_чисто": "first"})
    .sort_values("Пробег_чисто")
    .reset_index()
)

# Категориальная ось X
grouped["Пробег"] = pd.Categorical(grouped["Пробег"], categories=grouped["Пробег"], ordered=True)

# Bar-график
st.subheader("📊 Средняя цена по пробегу (категориально отсортировано)")
fig3 = px.bar(grouped, x="Пробег", y="Цена", title="Средняя цена в зависимости от пробега")
st.plotly_chart(fig3)

from datetime import datetime

# Преобразуем дату публикации в datetime
filtered_df["Дата публикации"] = pd.to_datetime(filtered_df["Дата публикации"], errors="coerce")
filtered_df["Дата публикации"] = filtered_df["Дата публикации"].dt.tz_localize(None)
filtered_df["Дней в продаже"] = (pd.Timestamp.now() - filtered_df["Дата публикации"]).dt.days

# Группировка по "Марка Модель"
top_models = (
    filtered_df.groupby("model_full")
    .agg(
        Кол_во_объявлений=("model_full", "count"),
        Сред_цена=("Цена", "mean"),
        Мин_цена=("Цена", "min"),
        Макс_цена=("Цена", "max"),
        Сред_дней_в_продаже=("Дней в продаже", "mean"),
        Сред_пробег=("Пробег_чисто", "mean"),
    )
    .sort_values("Кол_во_объявлений", ascending=False)
    .head(10)
    .reset_index()
)

# Округляем значения
top_models[["Сред_цена", "Мин_цена", "Макс_цена", "Сред_дней_в_продаже", "Сред_пробег"]] = (
    top_models[["Сред_цена", "Мин_цена", "Макс_цена", "Сред_дней_в_продаже", "Сред_пробег"]].round(0)
)

# Отображение
st.subheader("🏆 Топ-10 моделей по количеству публикаций")
st.dataframe(top_models)

# Таблица
st.subheader("📋 Детали")
st.dataframe(filtered_df.reset_index(drop=True))
