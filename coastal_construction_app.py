# Complete Streamlit App with Advanced Features
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from io import BytesIO
from fpdf import FPDF
import PyCO2SYS as pyco2
import pydeck as pdk
import plotly.express as px
import base64

# --- Background Styling ---
def set_background(image_url):
    st.markdown(f"""
        <style>
        html, body, [data-testid="stApp"] {{
            background-image: url('{image_url}');
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        [data-testid="stSidebar"], .main, .block-container {{
            background-color: rgba(255, 255, 255, 0.85);
            border-radius: 10px;
            padding: 1rem;
        }}
        </style>
    """, unsafe_allow_html=True)

# --- Core Functions ---
def compute_wave_energy(Hs, Tp):
    rho = 1025
    g = 9.81
    E = (1/8) * rho * g * Hs**2
    Cg = g * Tp / (4 * np.pi)
    return E * Cg

def estimate_sediment_transport(Hs, angle, Tp):
    K = 0.77
    return K * Hs**2 * np.sin(2 * np.radians(angle)) * Tp

def predict_shoreline_change(Q_sed):
    dx = 100
    dQdx = np.gradient(Q_sed, dx)
    return -dQdx

def carbonate_impact(TA, DIC, S=35, T=25, P=0):
    result = pyco2.sys(
        par1=TA, par2=DIC,
        par1_type=1, par2_type=2,
        salinity=S, temperature=T, pressure=P,
        opt_pH_scale=1
    )
    omega = result["output"]["OmegaAR"]
    return omega[0] if isinstance(omega, (list, np.ndarray)) else omega

def create_pdf(Hs, Tp, angle, TA, DIC, omega_value, fig):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt="Coastal & Ocean Engineering Report", ln=True, align="C")
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Wave Height (Hs): {Hs} m", ln=True)
    pdf.cell(200, 10, txt=f"Wave Period (Tp): {Tp} s", ln=True)
    pdf.cell(200, 10, txt=f"Wave Angle: {angle}°", ln=True)
    pdf.cell(200, 10, txt=f"TA: {TA} µmol/kg, DIC: {DIC} µmol/kg", ln=True)
    pdf.cell(200, 10, txt=f"Aragonite Saturation (Omega_a): {omega_value:.2f}", ln=True)
    buf = BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    pdf.image(buf, x=10, y=pdf.get_y() + 10, w=180)
    buf.close()
    return pdf.output(dest="S").encode("latin-1")

# --- App Structure ---
if 'started' not in st.session_state:
    st.session_state.started = False
if 'selected_module' not in st.session_state:
    st.session_state.selected_module = None

# --- Welcome Page ---
if not st.session_state.started:
    set_background("https://wallpaperaccess.com/full/124383.jpg")
    st.markdown("""
        <h1 style='text-align:center;'>Welcome to Coastal & Construction Modeling Suite</h1>
        <div style='text-align:center;'>
            <button onclick="window.location.reload();" style='font-size:20px;padding:10px 20px;'>Start</button>
        </div>
    """, unsafe_allow_html=True)
    if st.button("Start App"):
        st.session_state.started = True
    st.stop()

# --- Module Selection ---
if st.session_state.started and not st.session_state.selected_module:
    set_background("https://images.unsplash.com/photo-1581090700227-1e37b190418e")
    st.title("Select a Module")
    options = [
        "🌊 Wave & Sediment Modeling",
        "🧪 Carbonate Chemistry",
        "🗺️ Bathymetry Upload",
        "🚨 Risk Assessment",
        "📌 Mapping & Coastal Structures",
        "💰 Cost Estimator"
    ]
    choice = st.selectbox("Choose your task:", options)
    if st.button("Enter Module"):
        st.session_state.selected_module = choice
        st.experimental_rerun()
    st.stop()

# --- Set Clean Background ---
set_background("https://cdn.pixabay.com/photo/2017/08/06/03/42/architecture-2589577_1280.jpg")

# --- Modules ---
if st.session_state.selected_module == "🌊 Wave & Sediment Modeling":
    st.header("Wave & Sediment Module")
    Hs = st.slider("Wave Height (m)", 0.5, 5.0, 2.0)
    Tp = st.slider("Wave Period (s)", 4, 20, 8)
    angle = st.slider("Wave Angle (deg)", 0, 90, 30)

    Hs_array = np.linspace(max(0.1, Hs-0.5), Hs+0.5, 20)
    Tp_array = np.full_like(Hs_array, Tp)
    angle_array = np.linspace(max(0, angle-10), min(90, angle+10), 20)

    wave_energy = compute_wave_energy(Hs_array, Tp_array)
    Q_sed = estimate_sediment_transport(Hs_array, angle_array, Tp_array)
    shoreline_change = predict_shoreline_change(Q_sed)

    fig, ax = plt.subplots()
    ax.plot(shoreline_change, label="Shoreline Change", color='teal')
    ax.set_title("Predicted Shoreline Change")
    st.pyplot(fig)

    st.download_button("Download CSV", pd.DataFrame({
        "Hs": Hs_array,
        "Wave Energy": wave_energy,
        "Sediment Transport": Q_sed,
        "Shoreline Change": shoreline_change
    }).to_csv(index=False), file_name="wave_results.csv")

elif st.session_state.selected_module == "🧪 Carbonate Chemistry":
    st.header("Carbonate Chemistry")
    TA = st.number_input("Total Alkalinity", 2000, 2500, 2300)
    DIC = st.number_input("DIC", 1800, 2300, 2100)
    try:
        omega = carbonate_impact(TA, DIC)
        st.metric("Omega Aragonite", f"{omega:.2f}")
    except Exception as e:
        st.error(f"Error: {e}")

elif st.session_state.selected_module == "🗺️ Bathymetry Upload":
    st.header("Upload Bathymetry")
    uploaded_file = st.file_uploader("Upload bathymetry CSV", type="csv")
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.write(df.head())
        fig = px.imshow(df.values, color_continuous_scale='viridis')
        st.plotly_chart(fig)

elif st.session_state.selected_module == "🚨 Risk Assessment":
    st.header("Flood/Risk Assessment")
    st.write("Interactive tool coming soon...")

elif st.session_state.selected_module == "📌 Mapping & Coastal Structures":
    st.header("Mapping & Structures")
    st.map()
    lat = st.number_input("Latitude", value=28.5)
    lon = st.number_input("Longitude", value=77.0)
    st.pydeck_chart(pdk.Deck(
        initial_view_state=pdk.ViewState(latitude=lat, longitude=lon, zoom=10),
        layers=[
            pdk.Layer("ScatterplotLayer", data=pd.DataFrame({"lat":[lat], "lon":[lon]}),
                      get_position='[lon, lat]', get_color='[200, 30, 0, 160]', get_radius=200)
        ]
    ))

elif st.session_state.selected_module == "💰 Cost Estimator":
    st.header("Construction Cost Estimator")
    structure_type = st.selectbox("Structure Type", ["Seawall", "Jetty", "Breakwater"])
    length = st.number_input("Length (m)", 1, 1000, 100)
    height = st.number_input("Height (m)", 1, 50, 10)
    rate = {"Seawall": 1500, "Jetty": 2000, "Breakwater": 2500}[structure_type]
    cost = length * height * rate
    st.metric("Estimated Cost", f"${cost:,.2f}")

st.sidebar.button("🔙 Go Back", on_click=lambda: st.session_state.update({'selected_module': None}))
