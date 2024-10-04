# pyright: basic


import json
import time
from io import StringIO

import folium
import requests
import streamlit as st
from pydantic import BaseModel
from streamlit_extras.stylable_container import stylable_container
from streamlit_folium import st_folium
from streamlit_js_eval import streamlit_js_eval


class Config(BaseModel):
    host: str = "http://localhost"
    port: int = 8000


st.set_page_config(layout="wide", initial_sidebar_state="expanded")

if "car_color_map" not in st.session_state:
    st.session_state["car_color_map"] = {}

if "cars_data" not in st.session_state:
    st.session_state["cars_data"] = {}

if "forbidden_geojson" not in st.session_state:
    st.session_state["forbidden_geojson"] = None

    try:
        with open("forbidden.geojson", "r") as f:
            st.session_state["forbidden_geojson"] = json.load(f)
    except FileNotFoundError:
        print("No forbidden.geojson file found")
        pass

st.session_state["viewport_width"] = streamlit_js_eval(js_expressions="window.innerWidth", key="ViewportWidth")


@st.cache_data()
def get_config():
    # lit le fichier de configuration en json
    with open("config.json", "r") as f:
        return Config(**json.load(f))


@st.cache_data()
def get_marker_colors():
    """Returns a list of colors for the markers."""
    return [
        "darkblue",
        "purple",
        "cadetblue",
        "green",
        "red",
        "black",
        "blue",
        "gray",
        "darkred",
        "lightred",
        "darkgreen",
        "darkblue",
        "orange",
        "beige",
    ]


def forge_api_url():
    return f"{get_config().host}:{get_config().port}"


def main():
    # Fetch car data from the server
    response = requests.get(f"{forge_api_url()}/cars/today?count_by_car=100")
    all_cars_data = json.loads(response.text)

    # Initialize the map
    map = folium.Map(
        # tiles="https://{s}.tile.openstreetmap.fr/osmfr/{z}/{x}/{y}.png",
        # attr='&copy; OpenStreetMap France | &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    )
    feature_group = folium.FeatureGroup(name="Cars")
    marker_colors = get_marker_colors()
    car_color_map = st.session_state["car_color_map"]

    color_index = 0
    for car_id, car_info_list in all_cars_data.items():
        if car_id not in car_color_map:
            car_color_map[car_id] = marker_colors[color_index % len(marker_colors)]
            print(f"Assigning color {car_color_map[car_id]} to car {car_id}")
        color_index += 1

    st.session_state["car_color_map"] = car_color_map

    st.markdown(
        """
        <style>
            [data-testid="stDecoration"] {
                display: none;
            }

            [data-testid="stToolbar"] {
                display: none;
            }

            [data-testid="stAppViewBlockContainer"] {
                padding: 0;
            }

            [data-testid="stHeader"] {
                padding: 0;
            }

            [data-testid="element-container"] {
                padding: 0;
            }

            [data-testid="stSidebarCollapseButton"] {
                display: none;
            }
        </style>""",
        unsafe_allow_html=True,
    )

    for car_id, car_info_list in all_cars_data.items():
        for car_info in car_info_list:
            latitude = car_info["latitude"]
            longitude = car_info["longitude"]
            status = car_info["status"]
            battery = car_info["battery"]

        # Get the latest position of the car
        latest_car_info = car_info_list[0]
        latest_latitude = latest_car_info["latitude"]
        latest_longitude = latest_car_info["longitude"]

        st.session_state["cars_data"][car_id] = latest_car_info

        # Add a marker for the car
        feature_group.add_child(
            folium.Marker(
                location=[latest_latitude, latest_longitude],
                popup=folium.Popup(
                    f"<p><bold>{car_id}</bold>\nSTAT: {status}\n\nBAT: {battery}%</p>",
                    lazy=True,
                ),
                icon=folium.Icon(
                    color=car_color_map[car_id],
                    icon="car",
                    prefix="fa",
                ),
            )
        )

        # Draw the path of the car
        path_coordinates = [[car["latitude"], car["longitude"]] for car in car_info_list]
        path_line = folium.PolyLine(
            locations=path_coordinates,
            color=car_color_map[car_id],
        )

        feature_group.add_child(path_line)
        color_index += 1
        color_index += 1

    with st.sidebar:
        st.title("Cars tracking")
        st.subheader("Cars")
        for car_id, color in car_color_map.items():
            car_info = st.session_state["cars_data"][car_id]
            car_battery_icon = "🔋" if car_info["battery"] >= 20 else "🪫"

            with st.expander(f"**Car {car_id}** ({color})  {car_battery_icon} {car_info['battery']}%"):
                st.code(f"""
Lat.: {car_info['latitude']}
Lon.: {car_info['longitude']}
Status: {car_info['status']}
At home: {car_info['at_home']}
                """)
                with stylable_container(
                    key=f"hint_color_{car_id}",
                    css_styles=f"""
                        {{
                            background-color: {color};
                            color: {color};
                            width: 100%;
                            height: 5px;
                            border-radius: 0.8em;
                            padding: 0.2em;
                            margin: 0em;
                        }}
                        """,
                ):
                    pass

        uploaded_file = st.file_uploader("Choose a file")
        if uploaded_file is not None:
            # To read file as string:
            stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
            string_data = stringio.read()

            geojson_data = json.loads(string_data)

            folium.GeoJson(
                geojson_data,
                name="forbidden places",
                tooltip="Forbidden Places",
                style_function=lambda x: {
                    "fillColor": "red",
                    "color": "red",
                },
                highlight_function=lambda x: {
                    "weight": 5,
                    "fillColor": "red",
                    "color": "red",
                },
            ).add_to(map)

            # Save the geojson data in a file
            with open("forbidden.geojson", "w") as f:
                f.write(string_data)

            folium.LayerControl().add_to(map)

    st_folium(
        map,
        center=(45.75336519902591, 3.0314909254483497),
        zoom=20,
        feature_group_to_add=feature_group,
        width=st.session_state["viewport_width"],
        height=2500,
    )

    # Refresh the Streamlit app
    time.sleep(5)
    st.rerun()


if __name__ == "__main__":
    main()
