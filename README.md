# 📸 Photo Geotagger with GPX Track Visualization

Easily geotag your JPEG images using a `.gpx` file from your GPS device or smartphone!  
This Streamlit app matches image timestamps with GPS coordinates and adds location data directly to the image metadata (EXIF).

## 🌟 Features

- Upload a `.gpx` file and multiple JPEG images
- Automatically match each photo with the nearest GPS trackpoint
- View photo thumbnails with timestamp and original GPS info
- Interactive map with GPX trail and photo locations (thumbnails in popup!)
- Download all geotagged images as a ZIP file

## 🛠️ How to Use

1. Upload your `.gpx` file (e.g., from your GPS tracker or Strava)
2. Upload one or more `.jpg` or `.jpeg` images
3. Click **"📍 Start Geotagging Process"**
4. Download your fixed images or view them on the map!

## 🔗 Hosted Version

> You can launch the app directly here:  
> `https://photo-gpx-geotagger.streamlit.app/`

## 📦 Dependencies

See `requirements.txt` for all Python packages used.

---

## 🤝 Credits

- Built with guidance and code assistance from **[ChatGPT by OpenAI](https://openai.com/chatgpt)**  
  _(prompted, tested, and deployed with care ❤️)_

---

Built with ❤️ using [Streamlit](https://streamlit.io), [Folium](https://python-visualization.github.io/folium/), and [EXIF tools](https://piexif.readthedocs.io/en/latest/).
