import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from io import BytesIO
from fpdf import FPDF
import PyCO2SYS as pyco2
import plotly.express as px

# --- Background Styling ---
def set_background(image_url):
    st.markdown(
        f"""
        <style>
        html, body, [data-testid="stApp"] {{
            background-image: url("{image_url}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            background-repeat: no-repeat;
        }}
        [data-testid="stSidebar"], .main, .block-container {{
            background-color: rgba(255, 255, 255, 0.85);
            padding: 1rem;
            border-radius: 10px;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

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
        par1=TA,
        par2=DIC,
        par1_type=1,
        par2_type=2,
        salinity=S,
        temperature=T,
        pressure=P,
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
    pdf.cell(200, 10, txt=f"Total Alkalinity (TA): {TA} µmol/kg", ln=True)
    pdf.cell(200, 10, txt=f"Dissolved Inorganic Carbon (DIC): {DIC} µmol/kg", ln=True)
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, txt=f"Aragonite Saturation State (Ωₐ): {omega_value:.2f}", ln=True)

    buf = BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    pdf.image(buf, x=10, y=pdf.get_y() + 10, w=180)
    buf.close()
    return pdf.output(dest="S").encode("latin-1")

# --- Session State ---
if "page" not in st.session_state:
    st.session_state.page = "welcome"

# --- Welcome Page ---
if st.session_state.page == "welcome":
    set_background("https://images.unsplash.com/photo-1507525428034-b723cf961d3e")  # Ocean background
    st.markdown("<h1 style='text-align: center;'>🌊 Welcome to Coastal & Construction Engineering App</h1>", unsafe_allow_html=True)
    st.image("https://cdn.pixabay.com/photo/2017/10/02/19/47/beach-2819975_1280.jpg", use_column_width=True)
    st.markdown("<h3 style='text-align: center;'>Click below to get started</h3>", unsafe_allow_html=True)
    if st.button("🚀 Start"):
        st.session_state.page = "menu"

# --- Main Menu ---
elif st.session_state.page == "menu":
    set_background("https://images.unsplash.com/photo-1570129477492-45c003edd2be")  # Construction background
    st.markdown("<h2 style='text-align: center;'>🔧 Choose a Module to Begin</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)

    with col1:
        st.image("https://cdn-icons-png.flaticon.com/512/899/899702.png", width=80)
        if st.button("🌊 Wave & Sediment Modeling"):
            st.session_state.page = "wave"

    with col2:
        st.image("https://cdn-icons-png.flaticon.com/512/1095/1095114.png", width=80)
        if st.button("🧪 Carbonate Chemistry"):
            st.session_state.page = "chemistry"

    with col3:
        st.image("https://cdn-icons-png.flaticon.com/512/2933/2933894.png", width=80)
        if st.button("📥 Bathymetry Upload"):
            st.session_state.page = "bathymetry"

    col4, col5, col6 = st.columns(3)
    with col4:
        st.image("https://cdn-icons-png.flaticon.com/512/684/684908.png", width=80)
        if st.button("⚠️ Risk Assessment"):
            st.session_state.page = "risk"

    with col5:
        st.image("https://cdn-icons-png.flaticon.com/512/3103/3103501.png", width=80)
        if st.button("📍 Mapping & Structures"):
            st.session_state.page = "mapping"

    with col6:
        st.image("https://cdn-icons-png.flaticon.com/512/3132/3132072.png", width=80)
        if st.button("💰 Cost Estimator"):
            st.session_state.page = "cost"

# --- Wave Modeling Page ---
elif st.session_state.page == "wave":
    st.title("🌊 Wave & Sediment Modeling")
    Hs = st.slider("Significant Wave Height (m)", 0.5, 5.0, 2.0)
    Tp = st.slider("Peak Wave Period (s)", 4, 20, 8)
    angle = st.slider("Wave Angle (degrees)", 0, 90, 20)

    Hs_array = np.linspace(max(0.1, Hs - 0.5), Hs + 0.5, 20)
    Tp_array = np.full_like(Hs_array, Tp)
    angle_array = np.linspace(max(0, angle - 10), min(angle + 10, 90), 20)

    wave_energy = compute_wave_energy(Hs_array, Tp_array)
    Q_sed = estimate_sediment_transport(Hs_array, angle_array, Tp_array)
    shoreline_change = predict_shoreline_change(Q_sed)

    st.subheader("📉 Predicted Shoreline Change")
    fig, ax = plt.subplots()
    ax.plot(shoreline_change, label="Shoreline Change Rate", color="teal")
    ax.set_xlabel("Grid Index")
    ax.set_ylabel("Shoreline Change (m/s)")
    ax.grid(True)
    ax.legend()
    st.pyplot(fig)

    st.subheader("⬇️ Download Data")
    df = pd.DataFrame({
        "Hs": Hs_array,
        "Wave Energy": wave_energy,
        "Sediment Transport": Q_sed,
        "Shoreline Change": shoreline_change
    })
    st.download_button("Download CSV", df.to_csv(index=False).encode("utf-8"), "wave_model.csv", "text/csv")
    if st.button("← Back"):
        st.session_state.page = "menu"

# --- Carbonate Chemistry Page ---
elif st.session_state.page == "chemistry":
    st.title("🧪 Carbonate Chemistry Impact")
    TA = st.number_input("Total Alkalinity (µmol/kg)", min_value=2000, max_value=2500, value=2300)
    DIC = st.number_input("Dissolved Inorganic Carbon (µmol/kg)", min_value=1800, max_value=2300, value=2100)

    try:
        omega = carbonate_impact(TA, DIC)
        st.metric("Ωₐ Aragonite Saturation", f"{omega:.2f}")
    except Exception as e:
        st.error(f"Error in carbonate calculation: {e}")

    if st.button("← Back"):
        st.session_state.page = "menu"

# --- Bathymetry Upload Page ---
elif st.session_state.page == "bathymetry":
    st.title("📥 Bathymetry Upload")
    uploaded = st.file_uploader("Upload Bathymetry CSV", type=["csv"])
    if uploaded:
        df = pd.read_csv(uploaded)
        st.dataframe(df)
        if 'latitude' in df.columns and 'longitude' in df.columns:
            fig = px.scatter_mapbox(df, lat="latitude", lon="longitude", zoom=4)
            fig.update_layout(mapbox_style="open-street-map")
            st.plotly_chart(fig)
    if st.button("← Back"):
        st.session_state.page = "menu"

# --- Risk Assessment Page ---
elif st.session_state.page == "risk":
    st.title("⚠️ Risk Assessment")
    erosion = st.slider("Erosion Risk (1-10)", 1, 10, 5)
    flood = st.slider("Flood Risk (1-10)", 1, 10, 5)
    exposure = st.slider("Infrastructure Exposure (1-10)", 1, 10, 5)
    risk_index = round((erosion + flood + exposure) / 3, 2)
    st.metric("Composite Risk Index", risk_index)
    if st.button("← Back"):
        st.session_state.page = "menu"

# --- Mapping & Structures Page ---
elif st.session_state.page == "mapping":
    st.title("📍 Mapping & Coastal Structures")
    st.info("Future: Annotate coastal structures like groynes, breakwaters, jetties, seawalls using uploaded shapefiles or coordinates.")
    if st.button("← Back"):
        st.session_state.page = "menu"

# --- Cost Estimator Page ---
elif st.session_state.page == "cost":
    st.title("💰 Construction Cost Estimator")
    area = st.number_input("Enter Area (sq.m)", value=1000)
    cost_per_m2 = st.number_input("Cost per m² ($)", value=1200)
    total_cost = area * cost_per_m2
    st.metric("Estimated Cost", f"${total_cost:,.2f}")
    if st.button("← Back"):
        st.session_state.page = "menu"

