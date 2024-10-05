# pyright: basic

import json
import os
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
    port: int = 8001


st.set_page_config(layout="wide", initial_sidebar_state="expanded")

if "cart_color_map" not in st.session_state:
    st.session_state["cart_color_map"] = {}

if "carts_data" not in st.session_state:
    st.session_state["carts_data"] = {}

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
    api_url = os.getenv("API_URL", "http://localhost")
    api_port = int(os.getenv("API_PORT", "8000"))

    return Config(
        host=api_url,
        port=api_port,
    )


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
    trailing_length = 100
    if "slider_trails_length" in st.session_state:
        trailing_length = st.session_state["slider_trails_length"]

    response = requests.get(f"{forge_api_url()}/carts/today?count_by_cart={trailing_length}")
    all_carts_data = json.loads(response.text)

    # Initialize the map
    folium_map = folium.Map(
        # tiles="https://{s}.tile.openstreetmap.fr/osmfr/{z}/{x}/{y}.png",
        # attr='&copy; OpenStreetMap France | &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    )
    carts_feature_group = folium.FeatureGroup(name="Carts")
    marker_colors = get_marker_colors()
    cart_color_map = st.session_state["cart_color_map"]

    color_index = 0
    cart_color_map_changed = False
    sorted_carts = dict(sorted(all_carts_data.items(), key=lambda item: item[0].lower()))
    for cart_id, cart_info_list in sorted_carts.items():
        if cart_id not in cart_color_map:
            cart_color_map[cart_id] = marker_colors[color_index % len(marker_colors)]
            cart_color_map_changed = True
            print(f"Assigning color {cart_color_map[cart_id]} to cart {cart_id}")
        color_index += 1

    if cart_color_map_changed:
        st.session_state["cart_color_map"] = cart_color_map

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


         .low-battery-circle {
                background-color: #e78284;
                border-radius: 50%;
                width: 1.25em;
                height: 1.25em;

                display: flex;
                justify-content: center;
                align-items: center;
                margin-top: 1em;
            }

            .medium-battery-circle {
                background-color: #ef9f76;
                border-radius: 50%;
                width: 1.25em;
                height: 1.25em;

                display: flex;
                justify-content: center;
                align-items: center;
                margin-top: 1em;
            }

            .good-battery-circle {
                background-color: #a6d189;
                border-radius: 50%;
                width: 1.25em;
                height: 1.25em;

                display: flex;
                justify-content: center;
                align-items: center;
                margin-top: 1em;
            }

            .offline-circle {
                background-color: #737994;
                border-radius: 50%;
                width: 1.25em;
                height: 1.25em;

                display: flex;
                justify-content: center;
                align-items: center;
                margin-top: 1em;
            }

            .at-home-icon {
                background-color: #a6d189;
                border-radius: 50%;
                width: 1.25em;
                height: 1.25em;

                display: flex;
                justify-content: center;
                align-items: center;
                margin-top: 1em;
            }
        </style>""",
        unsafe_allow_html=True,
    )

    for cart_id, cart_info_list in sorted_carts.items():
        for cart_info in cart_info_list:
            latitude = cart_info["latitude"]
            longitude = cart_info["longitude"]
            status = cart_info["status"]
            battery = cart_info["battery"]

        # Get the latest position of the car
        latest_cart_info = cart_info_list[0]
        latest_latitude = latest_cart_info["latitude"]
        latest_longitude = latest_cart_info["longitude"]

        st.session_state["carts_data"][cart_id] = latest_cart_info

        carts_feature_group.add_child(
            folium.Marker(
                location=[latest_latitude, latest_longitude],
                popup=folium.Popup(
                    f"<p><bold>{cart_id}</bold>\nSTAT: {status}\n\nBAT: {round(battery, 2)}%</p>",
                    lazy=True,
                ),
                icon=folium.Icon(
                    color=cart_color_map[cart_id],
                    icon="car",
                    prefix="fa",
                ),
            )
        )

        # Draw the path of the car
        path_coordinates = [[car["latitude"], car["longitude"]] for car in cart_info_list]
        path_line = folium.PolyLine(
            locations=path_coordinates,
            color=cart_color_map[cart_id],
        )

        carts_feature_group.add_child(path_line)
        color_index += 1

    with st.sidebar:
        st.title("Carts tracking")

        with st.expander("Settings", expanded=True):
            st.session_state["slider_trails_length"] = st.slider("Carts trails length", 10, 500, 100, 10)
            st.session_state["app_refresh_secs"] = st.slider("App refresh time", 1, 60, 5, 1)

        st.subheader("Carts")
        for cart_id, color in cart_color_map.items():
            cart_info = st.session_state["carts_data"][cart_id]
            battery_col, exp = st.columns([0.1, 0.9])

            with battery_col:
                battery = cart_info["battery"]
                battery = round(battery, 2)

                if cart_info["status"] == 0:
                    st.markdown(
                        '<div class="offline-circle"></div>',
                        unsafe_allow_html=True,
                    )
                else:
                    if battery < 20:
                        st.markdown(
                            '<div class="low-battery-circle"></div>',
                            unsafe_allow_html=True,
                        )
                    elif battery < 40:
                        st.markdown(
                            '<div class="medium-battery-circle"></div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            '<div class="good-battery-circle"></div>',
                            unsafe_allow_html=True,
                        )

            with exp:
                # carts_battery_icon = "🔋" if carts_info["battery"] >= 20 else "🪫"
                with st.expander(f"{cart_id} ({color})", icon=":material/directions_car:"):
                    st.code(f"""
    Lat.: {round(cart_info['latitude'], 6)}
    Lon.: {round(cart_info['longitude'], 6)}
    Status: {cart_info['status']}
    Battery: {round(cart_info['battery'], 2)}%
    At home: {cart_info['at_home']}
                    """)
                    with stylable_container(
                        key=f"hint_color_{cart_id}",
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
            ).add_to(folium_map)

            # Save the geojson data in a file
            with open("forbidden.geojson", "w") as f:
                f.write(string_data)

            folium.LayerControl().add_to(folium_map)

    st_folium(
        folium_map,
        center=(45.75336519902591, 3.0314909254483497),
        zoom=20,
        feature_group_to_add=carts_feature_group,
        width=st.session_state["viewport_width"],
        height=2500,
    )

    time.sleep(st.session_state["app_refresh_secs"])
    st.rerun()


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError as e:
        st.error(f"Connection error: {e}\n\nPlease check the server, and click on the reload button.")
        button = st.button("Reload")

        if button:
            st.rerun()
