import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from cpbynwol.utils.calculate import interpol


# @st.cache_data
def heatmap(data, preference):
    mapping = go.Heatmap(
        z=-np.where(data[0] <= 0, np.nan, data[0]),
        x=data[1],
        y=data[2],
        colorscale=preference[0][0],
        colorbar=dict(
            title=dict(
                text='Depth'),
            titlefont=dict(color=preference[1][0]),
            tickfont=dict(color=preference[1][0])
        ),
        hovertemplate='<br>Глубина: %{z:.3f}<br>' +
                      '<i> Широта: </i>: %{y:.3f}' +
                      '<i> Долгота: </i>: %{x:.3f} <extra></extra>',
    )
    return mapping


# @st.cache_data
def heatland(data, preference):
    mapping = go.Heatmap(
        z=-np.where(data[0] != -1, np.nan, data[0]),
        x=data[1],
        y=data[2],
        colorscale=[[0, preference[0][1]], [1, preference[0][1]]],
        showscale=False,
        showlegend=False
    )
    return mapping


# @st.cache_data
def line_2d(data, preference):
    line_ = go.Scatter(
        x=np.array([point[0] for point in data[3]]),
        y=np.array([point[1] for point in data[3]]),
        name='Точки',
        mode='lines+markers',
        line=dict(color=preference[0][2]),
        marker=dict(color=preference[0][2]),
        hovertemplate='<i> Широта: </i>: %{y:.3f}' +
                      '<i> Долгота: </i>: %{x:.3f} <extra></extra>',
    )
    return line_


# @st.cache_data
def line_3d(data, preference):
    """

    :param data: [grid, x_range, y_range, [depth, [line_x, line_y]]] or default
    :param preference:
    :return:
    """
    if len(data[-1]) == 2:
        points_x = data[-1][1][0]
        points_y = data[-1][1][1]
        points_z = data[-1][0]

    else:
        points_x = [point[0] for point in data[-1]]
        points_y = [point[1] for point in data[-1]]
        points_z = [0 for _ in data[-1]]

    line_ = go.Scatter3d(
        x=points_x,
        y=points_y,
        z=-np.array(points_z),
        mode='lines',
        line=dict(color=preference[0][2],
                  width=5),
        hovertemplate='<br><b>Глубина</b>: %{z:.3f}<br>' +
                      '<i> Широта: </i>: %{y:.3f}' +
                      '<i> Долгота: </i>: %{x:.3f} <extra></extra>',
    )
    return line_


# @st.cache_data
def surface(data, preference):
    mapping = go.Surface(
        z=-np.where(data[0] < 0, 0.1, data[0]),
        x=data[1],
        y=data[2],
        name='Поверхность дна',
        colorscale=preference[0][0],
        colorbar=dict(title='Depth',
                      titlefont=dict(color=preference[1][0]),
                      tickfont=dict(color=preference[1][0])),
        contours=dict(z=dict(
            show=True,
            usecolormap=True,
            highlightcolor='limegreen',
            project_z=True)),
        showscale=True,
        hovertemplate='<br><b>Глубина</b>: %{z:.3f}<br>' +
                      '<i> Широта: </i>: %{y:.3f}' +
                      '<i> Долгота: </i>: %{x:.3f} <extra></extra>',
    )
    return mapping


# @st.cache_data
def surfland(data, preference):
    mapping = go.Surface(
        z=-np.where(data[0] >= 0, np.nan, -0),
        x=data[1],
        y=data[2],
        name='Поверхность дна',
        colorscale=[[0, preference[0][1]], [1, preference[0][1]]],
        showlegend=False,
        showscale=False,
        contours=dict(z=dict(
            show=True,
            usecolormap=True,
            highlightcolor='limegreen',
            project_z=True)),
        hovertemplate='<br><b>Глубина</b>: %{z:.3f}<br>' +
                      '<i> Широта: </i>: %{y:.3f}' +
                      '<i> Долгота: </i>: %{x:.3f} <extra></extra>',
    )
    return mapping


# @st.cache_data
def layout_2d(preference):
    layout = go.Layout(
        xaxis=dict(
            title=dict(text='Долгота',
                       font=dict(color=preference[1][0])),
            tickfont=dict(color=preference[1][0])),
        yaxis=dict(
            title=dict(text='Широта',
                       font=dict(color=preference[1][0])),
            tickfont=dict(color=preference[1][0]))
    )
    return layout


# @st.cache_data
def layout_3d(preference, border):
    [(min_lon, min_lat), (max_lon, max_lat)] = border
    fraction = np.abs(min_lon - max_lon) / np.abs(max_lat - min_lat)
    distance = 1.5
    angle = np.deg2rad(-90)
    layout = go.Layout(
        scene=dict(
            camera=dict(
                up=dict(x=0, y=0, z=0.5),
                center=dict(x=0, y=0, z=0),
                eye=dict(
                    x=distance * np.cos(angle),
                    y=distance * np.sin(angle),
                    z=distance * np.sin(-angle * 4 / 3)
                )
            ),
            camera_projection_type='perspective',
            aspectratio=dict(x=1 * fraction, y=1, z=0.5),
            xaxis=dict(
                title=dict(text='Долгота',
                           font=dict(color=preference[1][0])),
                tickfont=dict(color=preference[1][0])),
            yaxis=dict(
                title=dict(text='Широта',
                           font=dict(color=preference[1][0])),
                tickfont=dict(color=preference[1][0])),
            zaxis=dict(
                nticks=preference[-1],
                title=dict(text='Глубина',
                           font=dict(color=preference[1][0])),
                tickfont=dict(color=preference[1][0]))
        ),
    )
    return layout


# @st.cache_data
def create_shared_layout(current_map, text, font, bg, width):
    return go.Layout(
        showlegend=False,
        title=current_map,
        titlefont=dict(
            color=text,
            family=font,
            size=32),
        font=dict(
            family=font,
            size=20),
        hovermode='closest',
        hoverlabel_align='right',
        hoverlabel=dict(
            bgcolor=bg,
            font_family=font),
        xaxis=dict(
            title=dict(text='Долгота',
                       font=dict(color=text)),
            tickfont=dict(color=text),
        ),
        yaxis=dict(
            title=dict(text='Широта',
                       font=dict(color=text)),
            tickfont=dict(color=text),
        ),
        paper_bgcolor=bg,
        plot_bgcolor=bg,
        autosize=True,
        height=int(width * 0.7 * 0.9 * 0.99)
    )


# @st.cache_data
def output_points(points):
    output_container = st.container(border=True)
    with output_container:
        st.write("Выбранные точки: ")
        match len(points):
            case 1:
                value: np.ndarray = np.array(points)[:, ::-1]
                st.dataframe(
                    pd.DataFrame(value, columns=['Широта', 'Долгота'], index=['Начальная точка']),
                    use_container_width=True
                )
            case 2:
                value: np.ndarray = np.array(points)[:, ::-1]
                st.dataframe(
                    pd.DataFrame(value, columns=['Широта', 'Долгота'], index=['Начальная точка', 'Конечная точка']),
                    use_container_width=True
                )
