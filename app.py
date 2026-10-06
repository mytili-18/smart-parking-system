import streamlit as st
import requests
import math

st.set_page_config(
    page_title="Smart Parking Management System",
    page_icon="🚗",
    layout="wide"
)

st.title("🚗 Smart Parking Management System")
st.write("Find nearby parking places based on your location.")

st.subheader("📍 Find Nearby Parking")

location = st.text_input(
    "Enter your location",
    placeholder="Example: Gachibowli, Hyderabad"
)

radius = st.selectbox(
    "Search radius",
    ["1 km", "2 km", "5 km"]
)

if st.button("🔍 Find Nearby Parking"):

    if not location.strip():
        st.warning("Please enter your location.")

    else:

        # Find latitude and longitude
        with st.spinner("Finding your location..."):

            try:
                geocode_url = "https://nominatim.openstreetmap.org/search"

                params = {
                    "q": location,
                    "format": "json",
                    "limit": 1
                }

                headers = {
                    "User-Agent": "SmartParkingManagementSystem/1.0"
                }

                response = requests.get(
                    geocode_url,
                    params=params,
                    headers=headers,
                    timeout=15
                )

                if response.status_code != 200:
                    st.error("Location service is temporarily unavailable.")
                    st.stop()

                data = response.json()

                if not data:
                    st.error("Location not found. Please enter a valid location.")
                    st.stop()

                latitude = float(data[0]["lat"])
                longitude = float(data[0]["lon"])

                st.success(f"📍 Location found: {location}")

                st.write(
                    f"Latitude: {latitude:.5f} | "
                    f"Longitude: {longitude:.5f}"
                )

            except Exception:
                st.error(
                    "Unable to find the location right now. "
                    "Please try again."
                )
                st.stop()

        # Search radius
        radius_km = int(radius.split()[0])
        radius_meters = radius_km * 1000

        # Overpass servers
        overpass_servers = [
            "https://overpass-api.de/api/interpreter",
            "https://overpass.kumi.systems/api/interpreter",
            "https://overpass.private.coffee/api/interpreter"
        ]

        query = f"""
        [out:json][timeout:25];

        (
          node["amenity"="parking"]
            (around:{radius_meters},{latitude},{longitude});

          way["amenity"="parking"]
            (around:{radius_meters},{latitude},{longitude});

          relation["amenity"="parking"]
            (around:{radius_meters},{latitude},{longitude});
        );

        out center;
        """

        parking_data = None

        # Find nearby parking
        with st.spinner("Searching nearby parking places..."):

            for server in overpass_servers:

                try:
                    parking_response = requests.post(
                        server,
                        data=query,
                        headers={
                            "User-Agent":
                            "SmartParkingManagementSystem/1.0"
                        },
                        timeout=35
                    )

                    if parking_response.status_code == 200:

                        content_type = parking_response.headers.get(
                            "Content-Type",
                            ""
                        )

                        if "json" in content_type.lower():
                            parking_data = parking_response.json()
                            break

                except Exception:
                    continue

        if parking_data is None:

            st.error(
                "Parking search service is temporarily unavailable."
            )

            st.info(
                "Please wait a few seconds and try again."
            )

            st.stop()

        # Process parking places
        parking_places = []

        for element in parking_data.get("elements", []):

            tags = element.get("tags", {})

            name = tags.get(
                "name",
                "Parking Area"
            )

            if element["type"] == "node":

                lat = element.get("lat")
                lon = element.get("lon")

            else:

                center = element.get("center", {})

                lat = center.get("lat")
                lon = center.get("lon")

            if lat is None or lon is None:
                continue

            # Calculate distance
            R = 6371

            lat1 = math.radians(latitude)
            lat2 = math.radians(lat)

            dlat = math.radians(lat - latitude)
            dlon = math.radians(lon - longitude)

            a = (
                math.sin(dlat / 2) ** 2
                + math.cos(lat1)
                * math.cos(lat2)
                * math.sin(dlon / 2) ** 2
            )

            c = 2 * math.atan2(
                math.sqrt(a),
                math.sqrt(1 - a)
            )

            distance = R * c

            parking_places.append({
                "name": name,
                "latitude": lat,
                "longitude": lon,
                "distance": distance
            })

        # Sort by nearest
        parking_places.sort(
            key=lambda x: x["distance"]
        )

        # Display results
        if not parking_places:

            st.warning(
                f"No mapped parking places found within {radius}."
            )

        else:

            st.subheader("🅿️ Nearby Parking Places")

            st.write(
                f"Found {len(parking_places)} parking place(s) "
                f"within {radius}."
            )

            for i, parking in enumerate(
                parking_places[:10],
                start=1
            ):

                st.markdown(
                    f"""
                    ### 🅿️ {i}. {parking["name"]}

                    📏 Distance: **{parking["distance"]:.2f} km**

                    📍 Coordinates:
                    **{parking["latitude"]:.5f}, {parking["longitude"]:.5f}**
                    """
                )

                map_url = (
                    "https://www.google.com/maps/dir/?api=1"
                    f"&destination={parking['latitude']},"
                    f"{parking['longitude']}"
                )

                st.link_button(
                    "🗺️ Get Directions",
                    map_url
                )

                st.divider()

            # Map
            st.subheader("🗺️ Parking Map")

            map_data = []

            for parking in parking_places[:10]:

                map_data.append({
                    "latitude": parking["latitude"],
                    "longitude": parking["longitude"]
                })

            st.map(map_data)

st.divider()

st.info(
    "📌 This system finds mapped parking locations near your location. "
    "Real-time free/occupied slots require live camera or sensor data."
)

st.caption(
    "Smart Parking Management System | Python + Streamlit + OpenStreetMap"
)