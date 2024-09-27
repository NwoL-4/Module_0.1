import time

import geopy.distance
import mat4py
import numpy as np

import plotly.graph_objs as go
from plotly.express.colors import named_colorscales

import streamlit as st
from st_screen_stats import ScreenData
from streamlit_plotly_events import plotly_events
from streamlit_theme import st_theme

from cpbynwol.utils import calculate as calc
from cpbynwol.utils import plotly_ as plt


# Функция для обработки смены карты
def on_map_change():
    st.session_state.current_map = selected_map
    st.session_state.points = []
    st.cache_data.clear()


@st.dialog("Последний полученный вектор", width="large")
def plot_depth():
    st.plotly_chart(st.session_state.fig_scatter)


st.set_page_config(layout="wide")

# Определение текущей темы
theme = st_theme()
bg_color = theme["backgroundColor"]
text_color = theme["textColor"]
font_theme = theme["font"]
points_color = theme["primaryColor"]

# Определение размера окна
screenD = ScreenData(setTimeout=1000)
screen_d = screenD.st_screen_data()
width_fig, height_fig = screen_d["innerWidth"], screen_d["innerHeight"]

st.markdown("<h1 style='text-align: center; margin-top: -50px;'>Модуль</h1>", unsafe_allow_html=True)
st.divider()

if 'first_start' not in st.session_state:
    st.session_state.first_start = True
    st.session_state.dF = calc.load_data("PrognosisDB.db")
    st.session_state.current_map = None

selected_map = st.selectbox("Выберите карту",
                            st.session_state.dF["LOCATION"],
                            on_change=on_map_change)

shared_layout = plt.create_shared_layout(current_map=selected_map,
                                         text=text_color,
                                         font=font_theme,
                                         bg=bg_color,
                                         width=height_fig)

# Первый контейнер
with st.container(border=False):
    col1, col2 = st.columns([1, 3])
    # Выбор карты
    with col1:
        plot_type = st.radio('Выбор визуализации', ['2D', '3D'], index=0, horizontal=True)
        if plot_type == '3D':
            nticks = st.slider('Число контуров в проекции',
                               min_value=1, max_value=30, value=10,
                               step=1)
    with col2:
        subcol1, subcol2 = st.columns(2)
        with subcol1:
            color_depth = st.selectbox('Выбор палитры для глубины',
                                       sorted(named_colorscales()),
                                       index=sorted(named_colorscales()).index('deep'))
            if st.toggle('Reversed color map', value=True):
                color_depth += '_r'
        with subcol2:
            color_land = st.color_picker('Выбор цвета для суши',
                                         value='#013B14')

# Обработка данных из dF
grid, x_range, y_range = calc.calculated_data(selected_map, st.session_state.dF)

container = st.container(
    height=int(height_fig * 0.7),
    border=True)

if 'points' not in st.session_state:
    st.session_state.points = []

# Второй контейнер
with st.container(border=False):
    col1, _, col2, _, col3 = st.columns([3, 0.1, 2.5, 0.3, 3])
    with col1:
        st.write("Выберите точки на карте или введите вручную")
        with st.form('input_form', clear_on_submit=True, border=False):
            sub_col1, _, sub_col2, _, subcol3 = st.columns([4, 1, 4, 1, 3])
            with sub_col1:
                lat = st.text_input('Lat', placeholder='Место ввода', label_visibility='collapsed')
                st.markdown('<center>Широта</center>',
                            unsafe_allow_html=True)
            with sub_col2:
                lon = st.text_input('Lon', placeholder='Место ввода', label_visibility='collapsed')
                st.markdown('<center>Долгота</center>',
                            unsafe_allow_html=True)
            with subcol3:
                submit = st.form_submit_button('Отправить',
                                               use_container_width=True
                                               )
            if lat and lon and submit:
                st.success('Данные добавлены')
                st.session_state.points.append([float(lon), float(lat)])
    with col3:
        len_vector_depth = st.number_input('Число точек для вектора глубин',
                                           min_value=2, max_value=1000, value=100, step=1,
                                           help='Диапазон значений: от 2 до 1000')
    with col2:
        plt.output_points(st.session_state.points)
        sub_col1, sub_col2 = st.columns(2, vertical_alignment='top', gap='medium')
        with sub_col1:
            if st.button('Remove last point', disabled=True if len(st.session_state.points) == 0 else False):
                with st.spinner('Удаление...'):
                    if st.session_state.points:
                        st.session_state.points.pop()
        with sub_col2:
            if st.button('Получить вектор', disabled=True if len(st.session_state.points) < 2 else False):
                start_time = time.time()
                with st.spinner('Пожалуйста подождите...Генерируются данные'):
                    st.session_state.data_to_load, line = calc.get_vector(
                        border=[(x_range[0], y_range[0]), (x_range[-1], y_range[-1])],
                        points=st.session_state.points,
                        grid=grid,
                        len_line=len_vector_depth)
                    mat4py.savemat('temp.mat', st.session_state.data_to_load)
                st.write(f'Готово, время выполнения: {time.time() - start_time :.4f} с')

                st.session_state.fig_scatter = go.Figure(data=[
                    go.Scatter(x=st.session_state.data_to_load['Range'],
                               y=-np.array(st.session_state.data_to_load['Bottom']),
                               mode='lines', )
                ])
                plot_depth()


with container:
    if len(st.session_state.points) == 2:
        distance = geopy.distance.geodesic(
            geopy.point.Point(st.session_state.points[0][1], st.session_state.points[0][0]),
            geopy.point.Point(st.session_state.points[1][1], st.session_state.points[1][0])
        ).kilometers
        st.text(f'Дистанция: {distance:.2f} км', help='Округлено до 2 знаков после запятой')

data = [grid, x_range, y_range, st.session_state.points]

preference = [[color_depth, color_land, points_color],  # 0
              [text_color, font_theme]]  # 1

match plot_type:
    case '2D':
        fig = go.Figure(data=[func(data=data,
                                   preference=preference)
                              for func in [
                                  plt.heatland,
                                  plt.heatmap,
                                  plt.line_2d
                              ]],
                        layout=plt.layout_2d(preference=preference),
                        )
    case '3D':
        if len(st.session_state.points) == 2:
            data_to_load, line = calc.get_vector(border=[(x_range[0], y_range[0]), (x_range[-1], y_range[-1])],
                                                 points=st.session_state.points,
                                                 grid=grid,
                                                 len_line=10000)
            data = [grid, x_range, y_range, [data_to_load['Bottom'], line]]

        preference.append(nticks)
        fig = go.Figure(data=[func(data=data,
                                   preference=preference)
                              for func in [
                                  plt.surfland,
                                  plt.surface,
                                  plt.line_3d
                              ]],
                        layout=plt.layout_3d(preference=preference, border=[(x_range[0], y_range[0]),
                                                                            (x_range[-1], y_range[-1])]))
    case _:
        fig = go.Figure()

fig.update_layout(shared_layout)

with container:
    match plot_type:
        case '2D':
            match len(st.session_state.points):
                case 2:
                    selected_points = plotly_events(fig,
                                                    click_event=False,
                                                    override_height=int(height_fig * 0.7 * 0.9))
                case _:
                    selected_points = plotly_events(fig,
                                                    click_event=True,
                                                    override_height=int(height_fig * 0.7 * 0.9))
        case '3D':
            selected_points = plotly_events(fig,
                                            click_event=False,
                                            override_height=int(height_fig * 0.7 * 0.9))

if selected_points:
    if len(st.session_state.points) < 2:
        st.session_state.points.append((selected_points[0]['x'], selected_points[0]['y']))

if 'fig_scatter' in st.session_state:
    if st.button('Вектор'):
        plot_depth()
