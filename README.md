
# 🌿 PlantPal

**PlantPal** is an AI-powered plant care assistant built during **ScarlettHacks 2025**. It’s designed to help urban dwellers and plant lovers choose the right plants and keep them healthy with intelligent recommendations, live weather data, and computer vision analysis.

> ⚠️ Note: This project was built under a 24-hour hackathon constraint. The **tracking and reminder** system is a **work in progress** and will be updated in future commits.

---

## 🚀 Features

### 🪴 Indoor Plant Recommendation
- Analyzes room lighting and checks for AC presence and pet safety.
- Recommends plants that best suit your indoor environment.

### 🌞 Outdoor Plant Suggestion
- Suggests balcony-friendly plants based on real-time weather and spatial safety.

### 📸 Plant Health Check
- Uses image-based inference to detect plant health and suggest personalized care tips.

### ⏰ Growth Tracking + Reminders *(Coming Soon)*
- Allows storing plant images, health progress, and watering schedules.
- Future updates will include scheduling notifications and growth analysis.

---

## 🛠️ Tech Stack

| Category         | Technology                         |
|------------------|-------------------------------------|
| Frontend         | Streamlit                           |
| Backend          | Python                              |
| Database         | PostgreSQL                          |
| APIs             | Open-Meteo API, IP Geolocation API  |
| Computer Vision  | OpenCV (Brightness & Contour Analysis) |
| Language Model   | Ollama's Gemma 3:12B for multimodal inference |

---

## 💡 Motivation

Urban plant care can feel like guesswork. **PlantPal** aims to be your green buddy—helping you not only choose the right plants, but also understand how to take care of them with AI-powered insights.

---

## 📷 Demo (Screenshots)

*Coming soon!* Screenshots and GIFs will be added to show PlantPal in action.

---

## 📦 Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/plantpal.git
   cd plantpal
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the app:**
   ```bash
   streamlit run app.py
   ```

> 🔑 Ensure you configure your API keys and database credentials inside `.env` or a config file.

---

## 📬 Feedback & Contributions

This is an early-stage prototype. Feel free to submit issues, fork the repo, or suggest improvements via pull requests!

