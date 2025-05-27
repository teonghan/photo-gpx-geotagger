import streamlit as st
import gpxpy
import piexif
from PIL import Image
from io import BytesIO
from datetime import datetime
import folium
from streamlit_folium import st_folium
import zipfile
from folium.plugins import MarkerCluster
import base64

# === Helper Functions ===

def deg_to_dms_rational(deg):
    d = int(deg)
    m = int((abs(deg) - abs(d)) * 60)
    s = round((abs(deg) - abs(d) - m / 60) * 3600 * 100)
    return ((abs(d), 1), (m, 1), (s, 100))

def dms_to_deg(dms, ref):
    d, m, s = dms
    deg = d[0]/d[1] + (m[0]/m[1])/60 + (s[0]/s[1])/3600
    return deg if ref in ['N', 'E'] else -deg

def get_image_timestamp(image_file):
    img = Image.open(image_file)
    if "exif" not in img.info:
        return None, None, None
    exif_data = piexif.load(img.info["exif"])
    if piexif.ExifIFD.DateTimeOriginal not in exif_data["Exif"]:
        return None, None, None
    time_str = exif_data["Exif"][piexif.ExifIFD.DateTimeOriginal].decode()
    return datetime.strptime(time_str, "%Y:%m:%d %H:%M:%S"), exif_data, img

def find_closest_gpx_point(image_time, gpx_points):
    return min(gpx_points, key=lambda p: abs(p[0] - image_time))

def extract_gps_from_exif(exif_data):
    try:
        gps = exif_data.get("GPS", {})
        if piexif.GPSIFD.GPSLatitude in gps and piexif.GPSIFD.GPSLongitude in gps:
            lat = dms_to_deg(gps[piexif.GPSIFD.GPSLatitude], gps[piexif.GPSIFD.GPSLatitudeRef].decode())
            lon = dms_to_deg(gps[piexif.GPSIFD.GPSLongitude], gps[piexif.GPSIFD.GPSLongitudeRef].decode())
            return lat, lon
    except:
        pass
    return None, None

def embed_gps(exif_data, lat, lon):
    gps_ifd = {
        piexif.GPSIFD.GPSLatitudeRef: b'N' if lat >= 0 else b'S',
        piexif.GPSIFD.GPSLatitude: deg_to_dms_rational(lat),
        piexif.GPSIFD.GPSLongitudeRef: b'E' if lon >= 0 else b'W',
        piexif.GPSIFD.GPSLongitude: deg_to_dms_rational(lon),
    }
    exif_data["GPS"] = gps_ifd
    return piexif.dump(exif_data)

# === Streamlit UI ===

st.set_page_config(page_title="Geotag Photos with GPX", layout="wide")
st.title("📸 Geotag Photos Using GPX Track")
st.markdown("""
> 🌍 **Welcome to your Photo Time Machine!**  
>  
> Ever wondered *where* exactly you took those beautiful travel photos?  
> Just upload your **GPX track** and your **camera photos**, and this app will magically geotag each image with its matching GPS location!  
>
> You'll get:
> - 🖼️ Thumbnails of your images with timestamps  
> - 🧭 Auto-matched coordinates from your GPX file  
> - 🗺️ An interactive map with a trail and photo markers  
> - 📦 A ZIP download of all your fixed images  
>
> **Let’s bring your adventures back to the map!**
""")


# Initialize session state
if "start_processing" not in st.session_state:
    st.session_state.start_processing = False

# Uploaders
gpx_file = st.file_uploader("Upload a GPX File", type=["gpx"])
image_files = st.file_uploader("Upload JPEG Images", type=["jpg", "jpeg"], accept_multiple_files=True)

# Trigger button
if gpx_file and image_files and not st.session_state.start_processing:
    if st.button("📍 Start Geotagging Process"):
        st.session_state.start_processing = True
        st.rerun()

# Reset button
if st.session_state.start_processing:
    if st.button("🔄 Reset App"):
        st.session_state.start_processing = False
        st.rerun()

# Processing logic
if gpx_file and image_files and st.session_state.start_processing:
    st.success("✅ Geotagging started...")

    gpx = gpxpy.parse(gpx_file)
    gpx_points = [(p.time.replace(tzinfo=None), p.latitude, p.longitude)
                  for trk in gpx.tracks
                  for seg in trk.segments
                  for p in seg.points]
    trail_coords = [(p.latitude, p.longitude)
                    for trk in gpx.tracks
                    for seg in trk.segments
                    for p in seg.points]

    if not gpx_points or not trail_coords:
        st.error("❌ No GPS points found in the GPX file.")
    else:
        output_files = []
        map_points = []

        for file in image_files:
            st.markdown(f"---\n### 📷 `{file.name}`")
            image_time, exif_data, img = get_image_timestamp(file)
            if image_time is None:
                st.warning("⚠️ Skipping: No EXIF timestamp.")
                continue

            orig_lat, orig_lon = extract_gps_from_exif(exif_data)
            closest = find_closest_gpx_point(image_time, gpx_points)

            st.image(img.copy().resize((150, 150)))
            st.write(f"🕒 **Image time**: `{image_time}`")
            st.write(f"📍 **Closest GPX point**: `{closest[0]}` → (Lat: {closest[1]}, Lon: {closest[2]})")
            st.write(f"📌 **Original GPS**: {orig_lat}, {orig_lon}")

            new_exif = embed_gps(exif_data, closest[1], closest[2])
            buffer = BytesIO()
            img.save(buffer, "jpeg", exif=new_exif)
            buffer.seek(0)
            output_files.append((file.name, buffer))

            map_points.append({
                "name": file.name,
                "lat": closest[1],
                "lon": closest[2],
                "buffer": buffer
            })

        # Download
        if output_files:
            st.markdown("### 📦 Download Geotagged Images")
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zf:
                for fname, file_io in output_files:
                    file_io.seek(0)
                    zf.writestr(fname, file_io.read())
            zip_buffer.seek(0)

            st.download_button(
                label="📥 Download All Fixed Images (ZIP)",
                data=zip_buffer,
                file_name="geotagged_images.zip",
                mime="application/zip"
            )

        # Map
        if map_points:
            st.markdown("---\n### 🗺️ GPX Trail and Photo Locations Map")

            avg_lat = sum(p["lat"] for p in map_points) / len(map_points)
            avg_lon = sum(p["lon"] for p in map_points) / len(map_points)

            m = folium.Map(location=[avg_lat, avg_lon], zoom_start=14)
            folium.PolyLine(trail_coords, color="blue", weight=3, tooltip="GPX Trail").add_to(m)

            cluster = MarkerCluster().add_to(m)
            for p in map_points:
                p["buffer"].seek(0)
                encoded = base64.b64encode(p["buffer"].read()).decode("utf-8")
                img_html = f'<img src="data:image/jpeg;base64,{encoded}" width="150"/>'
                popup_html = f"<b>{p['name']}</b><br>{img_html}"
                popup = folium.Popup(popup_html, max_width=200)
                folium.Marker([p["lat"], p["lon"]], tooltip=p["name"], popup=popup).add_to(cluster)

            st_folium(m, width=700, height=500, return_last_map_state=False)
