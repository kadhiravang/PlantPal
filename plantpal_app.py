import os
import tempfile
import streamlit as st
import requests
import ollama
from datetime import datetime, timedelta
from PIL import Image
import psycopg2
import io
import shutil
import cv2
import numpy as np
from matplotlib import pyplot as plt
# ---------------------- Helper Functions ----------------------

def suggest_placement_zone_3x3(img: Image.Image):
    img_arr = np.array(img)
    gray = cv2.cvtColor(img_arr, cv2.COLOR_RGB2GRAY)
    h, w = gray.shape
    grid_h, grid_w = h // 3, w // 3
    zones, labels = [], []
    pos, cols = ['TOP', 'MID', 'BOT'], ['LEFT', 'CENTER', 'RIGHT']

    for i in range(3):
        for j in range(3):
            y1, y2, x1, x2 = i * grid_h, (i + 1) * grid_h, j * grid_w, (j + 1) * grid_w
            crop = gray[y1:y2, x1:x2]
            brightness = np.mean(crop)
            zones.append(((x1, y1, x2, y2), brightness))
            labels.append(f"{cols[j]}-{pos[i]}")

    best_idx = np.argmax([b for (_, b) in zones])
    best_label = labels[best_idx]

    display_img = img_arr.copy()
    for idx, ((x1, y1, x2, y2), _) in enumerate(zones):
        color = (0, 255, 0) if idx == best_idx else (255, 255, 255)
        cv2.rectangle(display_img, (x1, y1), (x2, y2), color, 2)
        cv2.putText(display_img, labels[idx], (x1 + 5, y1 + 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

    # plt.figure(figsize=(10, 8))
    # plt.imshow(display_img)
    # plt.axis("off")
    # plt.title(f"Suggested Placement Zone: {best_label}")
    # plt.show()

    return best_label

def get_light_temperature(img: Image.Image):
    img_np = np.array(img)
    avg_color = np.mean(img_np, axis=(0, 1))  # RGB
    r, g, b = avg_color
    if b > r + 15:
        return "cool"
    elif r > b + 15:
        return "warm"
    else:
        return "neutral"

def get_user_location():
    # This function will fetch user's location, you can use geolocation APIs like geopy.
    return 37.7749, -122.4194  # Placeholder coordinates for San Francisco

def get_weather_data(lat, lon):
    # Function to get weather data using an API such as Open-Meteo or OpenWeatherMap
    # Sample mock-up return value
    return {
        "daily": {
            "temperature_2m_max": [25],
            "sunshine_duration": [120]
        }
    }

def run_inference_ollama(image, prompt):
    # Save the uploaded image to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
        temp_file.write(image.read())  # Use .read() to get the byte content of the uploaded file
        temp_path = temp_file.name  # Get the path of the temporary file
    
    # Pass the path of the saved image to Ollama for inference (no need for .getbuffer() here)
    response = ollama.chat(
        model='gemma3:12b',
        messages=[{
            'role': 'user',
            'content': prompt,
            'images': [temp_path]  # Pass the file path to Ollama (no .read() here)
        }]
    )
    return response['message']['content']

def get_weather_data(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,sunshine_duration&timezone=auto"
    response = requests.get(url)
    return response.json()

def get_user_location():
    url = "https://ipinfo.io/json"
    response = requests.get(url)
    data = response.json()
    loc = data.get("loc", "13.0827,80.2707")
    lat, lon = loc.split(",")
    return float(lat), float(lon)

def analyze_image_for_light_zones(image):
    # Convert image to grayscale
    image = np.array(image)
    gray_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    # Apply thresholding to detect areas with high brightness
    _, high_brightness = cv2.threshold(gray_image, 180, 255, cv2.THRESH_BINARY)
    _, medium_brightness = cv2.threshold(gray_image, 100, 180, cv2.THRESH_BINARY)
    low_brightness = cv2.bitwise_not(cv2.bitwise_or(high_brightness, medium_brightness))

    # Calculate percentage of pixels in each zone
    high_percentage = np.sum(high_brightness) / high_brightness.size * 100
    medium_percentage = np.sum(medium_brightness) / medium_brightness.size * 100
    low_percentage = np.sum(low_brightness) / low_brightness.size * 100

    # Classify light level
    if high_percentage > 50:
        light_level = "High"
    elif medium_percentage > 50:
        light_level = "Medium"
    else:
        light_level = "Low"

    return light_level, high_percentage, medium_percentage, low_percentage

# PostgreSQL connection setup
def get_db_connection():
    conn = psycopg2.connect(
        host="localhost",        # Update with your host, e.g., "localhost" or an external host
        database="ScarlettHacks",     # Update with your database name
        user="postgres",    # Update with your username
        password="test@123" # Update with your password
    )
    return conn

def save_plant_to_db(plant_name, health_status, watering_interval, watering_amount, next_watering):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Insert plant data
    cursor.execute(""" 
        INSERT INTO plants (name, health_status, watering_interval, watering_amount, next_watering, upload_date)
        VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
    """, (plant_name, health_status, watering_interval, watering_amount, next_watering, datetime.now()))
    plant_id = cursor.fetchone()[0]
    
    conn.commit()
    cursor.close()
    conn.close()
    return plant_id

def save_image_to_db(plant_id, image_data):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Insert plant image data into the database as binary
    cursor.execute(""" 
        INSERT INTO plant_images (plant_id, image_data, date)
        VALUES (%s, %s, %s)
    """, (plant_id, psycopg2.Binary(image_data), datetime.now()))  # Store the binary data and the current timestamp
    
    conn.commit()
    cursor.close()
    conn.close()

def get_plant_images_from_db(plant_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT image_data, date FROM plant_images WHERE plant_id = %s ORDER BY date DESC", (plant_id,))
    images = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return images

# ---------------------- Streamlit UI ----------------------
st.set_page_config(page_title="PlantPal", layout="wide")
st.title("🌿 PlantPal - Smart Plant Companion")

selection = st.sidebar.radio("Choose Feature", [
    "🌞 Indoor Plant Recommender",
    "🌳 Outdoor Growth Advisor",
    "⏰ Health & Reminder System"
])

# ---------------------- 1. Indoor Plant Recommender ----------------------
if selection == "🌞 Indoor Plant Recommender":
    st.header("Upload a photo of your indoor space")
    image = st.file_uploader("Upload room image", type=["jpg", "png"])

    has_ac = st.radio("Do you have an air conditioner (AC) in your room?", ("Yes", "No"))
    has_pet = st.radio("Do you own a pet?", ("Yes", "No"))  # New input for pet ownership

    if image:
        image_pil = Image.open(image)
        
        # Perform light zone detection and suggest placement zone
        zone = suggest_placement_zone_3x3(image_pil)  # Optimal placement zone
        light_temp = get_light_temperature(image_pil)

        # Ask for room temperature based on user's response
        if has_ac == "Yes":
            room_temp = st.number_input("Enter the room temperature (°C)", min_value=-50, max_value=50, value=22, step=1)
            prompt = f"""
            Analyze this indoor image and infer:
            1. Suggested light level: {light_temp}
            2. Room size: medium
            3. Room temperature: {room_temp}°C
            4. Optimal placement zone for the plant pot: {zone} (Please place the plant in this zone for best results.)
            5. Does the user own a pet? {has_pet}. (Make sure the plants you suggest are not poisonous if the owner has pets.)
            6. Recommend 3 indoor plants suited for this space with names and short care tips, considering pet safety.
            Format output as:
            Light Level: {light_temp}
            Room Size: medium
            Room Temperature: {room_temp}°C
            Does the user own a pet: {has_pet}
            Recommendations:
            - Plant 1: ...
            - Plant 2: ...
            - Plant 3: ...
            Write some good explanation for the suggestions with the observation you have
            """
        else:
            # Get weather data to estimate the room temperature
            lat, lon = get_user_location()
            weather = get_weather_data(lat, lon)
            if weather.get('error'):
                st.error("Failed to fetch weather data. Please try again later.")
            else:
                temp = weather['daily']['temperature_2m_max'][0]
                sunlight = weather['daily']['sunshine_duration'][0]
                prompt = f"""
                Analyze this indoor image and infer:
                1. Suggested light level: {light_temp}
                2. Room size: medium
                3. Outdoor weather conditions:
                - Max Temp: {temp}°C
                - Sunshine Duration: {sunlight} mins
                4. Optimal placement zone for the plant pot: {zone} (Please place the plant in this zone for best results.)
                5. Does the user own a pet? {has_pet}
                6. Recommend 3 indoor plants suited for this space with names and short care tips, considering pet safety.
                Format output as:
                Light Level: {light_temp}
                Room Size: medium
                Outdoor Weather:
                - Max Temp: {temp}°C
                - Sunshine Duration: {sunlight} mins
                Does the user own a pet: {has_pet} (Make sure the plants you suggest are not poisonous if the owner has pets.)
                Recommendations:
                - Plant 1: ...
                - Plant 2: ...
                - Plant 3: ...
                Write some good explanation for the suggestions with the observation you have
                """

        if st.button("Send"):
            with st.spinner("Generating plant recommendations..."):
                image.seek(0)
                # print(prompt)  # You can remove this after testing
                response = run_inference_ollama(image, prompt)
            st.markdown(response)

# ---------------------- 2. Outdoor Growth Advisor ----------------------
elif selection == "🌳 Outdoor Growth Advisor":
    st.header("Confined Outdoor Plant Advisor")
    image = st.file_uploader("Upload an outdoor space image (balcony, terrace)", type=["jpg", "png"])

    lat, lon = get_user_location()
    st.write(f"Using your location: Latitude: {lat}, Longitude: {lon}")

    if image:
        weather = get_weather_data(lat, lon)
        if weather.get('error'):
            st.error("Failed to fetch weather data. Please try again later.")
        else:
            temp = weather['daily']['temperature_2m_max'][0]
            sunlight = weather['daily']['sunshine_duration'][0]

            prompt = f"""
            Analyze this outdoor image to infer:
            - Available planting area (small/medium/large)
            - Shade and sunlight availability
            - Safety for nearby structures

            Based on the below weather data:
            - Max Temp: {temp}°C
            - Daily Sunshine Duration: {sunlight} mins
            See if there are buildings nearby and suggest trees that wont damage the concrete structures.
            Suggest 3 suitable plants that can be grown safely and thrive in this outdoor space.
            Include sunlight and water needs.
            """

            if st.button("Send"):
                with st.spinner("Generating outdoor plant recommendations..."):
                    response = run_inference_ollama(image, prompt)
                st.markdown(response)

# ---------------------- 3. Health & Reminder System ----------------------
elif selection == "⏰ Health & Reminder System":
    st.header("🌿 Plant Health Checker & Smart Reminder System")

    plant_name = st.text_input("🌱 Enter a name for your plant")
    image = st.file_uploader("📸 Upload a photo of your plant", type=["jpg", "png"])

    if 'health_response' not in st.session_state:
        st.session_state.health_response = ""
        st.session_state.interval = 3
        st.session_state.amount = 100

    if image and plant_name:
        # Save uploaded image as binary
        image_data = image.read()
        image.seek(0)
        # Store the uploaded date and health status
        upload_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        prompt = """
        Analyze this plant and provide the following:
        - Health status (healthy, underwatered, overwatered, pest issues)
        - Care tips based on visible condition
        - Recommended watering frequency (in days)
        - Suggested watering amount (in ml)
        Format:
        Health: ...
        Tips: ...
        Watering Interval: ...
        Watering Amount: ...
        """
        if st.button("Analyze Plant"):
            with st.spinner("Analyzing plant condition..."):
                response = run_inference_ollama(image, prompt)
                st.session_state.health_response = response

        if st.session_state.health_response:
            st.subheader("📊 Health Analysis & Care Tips")
            st.markdown(st.session_state.health_response)

            st.subheader("🔧 Customize Reminder Settings")
            reminder_days = st.slider("🕒 Water every X days", min_value=1, max_value=30, value=7)
            water_amount = st.slider("💧 Watering amount (ml)", min_value=250, max_value=10000, value=500)

            if st.button("💾 Save Reminder"):
                next_watering = (datetime.now() + timedelta(days=reminder_days)).strftime('%Y-%m-%d')

                plant_id = save_plant_to_db(
                    plant_name, 
                    st.session_state.health_response.split("\n")[0],  # Extract health status
                    reminder_days, 
                    water_amount, 
                    next_watering
                )
                save_image_to_db(plant_id, image_data)  # Save the image as binary data
                st.success(f"✅ Reminder for **{plant_name}** saved!")

    # Show existing pictures and allow user to upload new ones after watering
    st.divider()
    st.subheader("📅 Stored Plants & Watering Schedule")

    # Add scrollable container for stored plants
    st.markdown(""" 
    <style> 
        .scrollable { 
            max-height: 500px; 
            overflow-y: scroll; 
        } 
    </style> 
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="scrollable">', unsafe_allow_html=True)

        # Fetch reminders and images from DB
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM plants")
        plants = cursor.fetchall()

        for plant in plants:
            plant_id, name, health_status, interval, amount, next_watering, upload_date = plant
            with st.expander(f"🌱 {name}"):
                st.markdown(f"""
                - Health: **{health_status}**
                - Water every **{interval}** days  
                - Next watering on **{next_watering}**  
                - Amount: **{amount}ml**
                """)

                # Retrieve images from the DB and store them in a temp directory
                images = get_plant_images_from_db(plant_id)
                if images:
                    with tempfile.TemporaryDirectory() as temp_dir:
                        for i, (img_data, date) in enumerate(sorted(images, key=lambda x: x[1])):  # Sort images by date
                            # Save image to a temporary file with timestamped filename
                            timestamp = date.strftime('%Y-%m-%d_%H-%M-%S')
                            temp_img_path = os.path.join(temp_dir, f"plant_{plant_id}_img_{timestamp}.png")
                            with open(temp_img_path, "wb") as temp_img_file:
                                temp_img_file.write(img_data)

                            # Display image in a gallery
                            st.image(temp_img_path, caption=f"Uploaded on {timestamp}", use_container_width =True)

                else:
                    st.info("No progress images available for this plant.")

                # Upload a new picture after watering
                new_image = st.file_uploader(f"Upload new image for {name}", type=["jpg", "png"], key=f"new_image_{plant_id}")
                if new_image:
                    # Save the image with timestamp filename
                    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                    save_image_to_db(plant_id, new_image.read())  # Save the updated image with timestamp
                    st.success(f"📷 Updated image for **{name}** saved!")

        st.markdown('</div>', unsafe_allow_html=True)

    cursor.close()
    conn.close()
