import sqlite3

import geopy.distance
import numpy as np
import pandas as pd
import streamlit
# import streamlit as st
from scipy.interpolate import griddata


# Загрузка карты
# @st.cache_resource
def load_data(db_name):
    with sqlite3.connect(db_name) as con:
        df = pd.read_sql_query('SELECT * FROM prg_location_grid', con)
    return df


# Манипуляции с данными по текущей карте
# @st.cache_data
def calculated_data(selected_map, df):
    map_data = df[df['LOCATION'] == selected_map].iloc[0]
    grid_str = map_data['GRID'][2:-2]
    grid: np.ndarray = np.array([np.fromstring(row, sep=', ') for row in grid_str.split('], [')])
    max_lat, min_lon = tuple(map(float, map_data['UP_LEFT_ANGLE_LAT_LON'].split(',')))
    min_lat, max_lon = tuple(map(float, map_data['DOWN_RIGHT_ANGLE_LAT_LON'].split(',')))

    x_range = np.linspace(min_lon, max_lon, grid.shape[1], endpoint=True)
    y_range = np.linspace(min_lat, max_lat, grid.shape[0], endpoint=True)

    return grid, x_range, y_range


# @st.cache_data
def get_vector(
        border: list,
        points: list,
        grid: np.ndarray,
        len_line: int = 1000,
):
    """
    border: list[(min_lon, min_lat), (max_lon, max_lat)]
    """

    [(min_lon, min_lat), (max_lon, max_lat)] = border

    y1, x1 = points[0][1], points[0][0]
    y2, x2 = points[1][1], points[1][0]

    line_y, line_x = np.linspace(y1, y2, len_line, endpoint=True), np.linspace(x1, x2, len_line, endpoint=True)

    distance: np.ndarray = np.array([
        geopy.distance.geodesic(
            geopy.point.Point(y1, x1),
            geopy.point.Point(lat, lon)
        ).kilometers
        for lat, lon in zip(line_y, line_x)
    ])
    x_range = np.linspace(min_lon, max_lon, grid.shape[1], endpoint=True)
    y_range = np.linspace(min_lat, max_lat, grid.shape[0], endpoint=True)

    x, y = np.meshgrid(x_range, y_range)

    line_z: np.ndarray = interpol(points=(line_x, line_y), grid=[(x.flatten(), y.flatten()), grid.flatten()])
    line_z = np.where(line_z <= 0, np.nan, line_z)

    save_data = {
        'Bonder': [(min_lon, min_lat), (max_lon, max_lat)],
        'Range':  distance.astype(float).tolist(),
        'Bottom': line_z.astype(float).tolist(),
        'Top':    np.zeros_like(distance, dtype=int).tolist()}

    return save_data, [line_x, line_y]


# @st.cache_data
def interpol(points: np.ndarray,
             grid: list):
    """
    :param points: Точки в которых ищем (Lon, Lat)
    :param grid: list[Координаты сетки[Lon, Lat], Сама сетка с данными]
    :return:
    """
    vector = griddata((grid[0][0], grid[0][1]), grid[1], points,
                      method='nearest')
    return vector
