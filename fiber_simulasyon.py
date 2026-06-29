import streamlit as st
import numpy as np
import plotly.graph_objects as go

# ---------------------------------------------------------
# SIFIR AYARLAR: SAYFA VE TEMA YAPILANDIRMASI
# ---------------------------------------------------------
st.set_page_config(
    page_title="Fiber Optik Simülasyonu",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Slate & Cyber Indigo: Üst Düzey Görsel Estetik CSS
st.markdown("""
    <style>
        /* Ana arka plan: Derin Gece Mavisi / Slate Black */
        .stApp {
            background-color: #0B0F19; 
            color: #D1D5DB; 
        }
        /* Yan menü (Sidebar) arka planı: Mat Grafit */
        section[data-testid="stSidebar"] {
            background-color: #111827; 
        }
        /* Başlıklar: Net, pürüzsüz saf beyaz */
        h1, h2, h3 {
            color: #F9FAFB !important; 
            font-weight: 500;
            letter-spacing: -0.5px;
        }
        /* Metrik Sayıları: Premium Teknoloji Mavisi Vurgusu */
        div[data-testid="stMetricValue"] {
            color: #6366F1;
            font-weight: 600;
        }
        /* Slider (Kaydırıcı) çizgilerini minimalist hale getirme */
        .stSlider [data-baseweb="slider"] {
            background-color: transparent;
        }
        div[data-testid="stThumbValue"] {
            color: #6366F1 !important;
        }
        /* Sabit Footer Alanı */
        .footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: #111827;
            color: #9CA3AF;
            text-align: center;
            padding: 10px;
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 13px;
            font-weight: 500;
            border-top: 1px solid #1F2937;
            z-index: 100;
        }
    </style>
""", unsafe_allow_html=True)

st.title("Fiber Optik Kabloda Tam İç Yansıma (TIR) Simülasyonu")

# ---------------------------------------------------------
# YAN MENÜ: PARAMETRELER (SIDEBAR)
# ---------------------------------------------------------
st.sidebar.header("Fiziksel Parametreler")
n1 = st.sidebar.slider("Çekirdek Kırılma İndisi (n₁)", 1.45, 1.60, 1.48, step=0.01)
n2 = st.sidebar.slider("Dış Kılıf Kırılma İndisi (n₂)", 1.40, 1.47, 1.44, step=0.01)
theta_in_deg = st.sidebar.slider("Başlangıç Giriş Açısı (derece)", 0.0, 45.0, 11.0, step=0.5)

st.sidebar.header("Gelişmiş Parametreler")
wavelength_nm = st.sidebar.slider("Dalga Boyu (nm)", 400, 1600, 850, step=50)
radius_um = st.sidebar.slider("Gerçek Çekirdek Yarıçapı (µm)", 5.0, 50.0, 25.0, step=1.0)
alpha_db_km = st.sidebar.slider("Sönümleme (dB/km)", 0.1, 2.0, 0.2, step=0.1)
length_km = st.sidebar.slider("Gerçek Fiber Uzunluğu (km)", 1.0, 20.0, 15.5, step=0.5)

# ---------------------------------------------------------
# HESAPLAMALAR
# ---------------------------------------------------------
if n1 <= n2:
    st.error("Hata: Çekirdek kırılma indisi ($n_1$), dış kılıf kırılma indisinden ($n_2$) büyük olmalıdır!")
    st.stop()

critical_angle_rad = np.arcsin(n2 / n1)
critical_angle_deg = np.degrees(critical_angle_rad)
NA = np.sqrt(n1**2 - n2**2)

if NA <= 1.0:
    theta_max_rad = np.arcsin(NA)
    theta_max_deg = np.degrees(theta_max_rad)
else:
    theta_max_deg = 90.0

delta = (n1**2 - n2**2) / (2 * n1**2)
wavelength_m = wavelength_nm * 1e-9
radius_m = radius_um * 1e-6
V_number = (2 * np.pi * radius_m / wavelength_m) * NA
mode_count = int(np.floor((V_number**2) / 2))

pin_dbm = 0.0
attenuation_loss_db = alpha_db_km * length_km
pout_dbm = pin_dbm - attenuation_loss_db
pout_mw = 10**(pout_dbm / 10)

# ---------------------------------------------------------
# SONUÇLAR PANELİ
# ---------------------------------------------------------
st.subheader("Sonuçlar ve Durum")

col1, col2, col3 = st.columns(3)
col1.metric("Kritik Açı ($θ_c$)", f"{critical_angle_deg:.2f}°")
col2.metric("Kabul Açısı ($θ_{max}$)", f"{theta_max_deg:.2f}°")
col3.metric("Sayısal Açıklık (NA)", f"{NA:.4f}")

col4, col5, col6 = st.columns(3)
col4.metric("Kısmi Kırılma İndisi Değişimi ($Δ$)", f"{delta:.4f}")
col5.metric("V-Sayısı", f"{V_number:.2f}")
col6.metric("Mod Sayısı", f"{mode_count:,}")

is_within_acceptance = theta_in_deg <= theta_max_deg

if is_within_acceptance:
    st.success(f"Giriş açısı olan {theta_in_deg}°, Kabul Konisi (<= {theta_max_deg:.2f}°) içindedir. Fiber içinde Tam İç Yansıma gerçekleşir.")
else:
    st.error(f"Giriş açısı olan {theta_in_deg}°, Kabul Konisi (<= {theta_max_deg:.2f}°) dışındadır! Işık kılıfa sızar.")

st.write("---")
col_p1, col_p2, col_p3 = st.columns(3)
col_p1.metric("Zayıflama Kaybı", f"{attenuation_loss_db:.1f} dB")
col_p2.metric("Giriş Gücü", "0.0 dBm (1.0 mW)")
col_p3.metric("Çıkış Gücü", f"{pout_dbm:.2f} dBm ({pout_mw:.3f} mW)")

# ---------------------------------------------------------
# GRAFİKSEL SİMÜLASYON
# ---------------------------------------------------------
st.write("---")
st.subheader("Işın İzleme (Ray Tracing) Simülasyonu")

fiber_length_display = 200  
y_core = radius_um

fig = go.Figure()

# Çekirdek Alanı: Opaklığı (transparanlığını) artırdık, kablo içi netleşti
fig.add_shape(type="rect", x0=0, y0=-y_core, x1=fiber_length_display, y1=y_core,
              fillcolor="rgba(99, 102, 241, 0.15)", line=dict(color="rgba(0,0,0,0)"), name="Çekirdek")

# --- YENİLİK: KESİKLİ ÇİZGİLER YERİNE DÜZ, NET VE KALIN DUVARLAR ---
fig.add_trace(go.Scatter(x=[0, fiber_length_display], y=[y_core, y_core], mode='lines',
                         line=dict(color='#94A3B8', width=2.5), name='Kablonun Üst Kenarı (Sınır)'))
fig.add_trace(go.Scatter(x=[0, fiber_length_display], y=[-y_core, -y_core], mode='lines',
                         line=dict(color='#94A3B8', width=2.5), showlegend=False))
# -------------------------------------------------------------------

# Kabul Konisi Görselleştirmesi
if theta_max_deg < 90:
    cone_length = 30
    cone_y = cone_length * np.tan(np.radians(theta_max_deg))
    fig.add_trace(go.Scatter(
        x=[-cone_length, 0, -cone_length], y=[cone_y, 0, -cone_y],
        fill='toself', fillcolor='rgba(99, 102, 241, 0.04)',
        line=dict(color='rgba(99, 102, 241, 0.2)', dash='dot'), name='Kabul Konisi'
    ))

theta_in_rad = np.radians(theta_in_deg)

if theta_in_deg > 0:
    sin_ref = np.sin(theta_in_rad) / n1
    theta_ref_rad = np.arcsin(sin_ref)
else:
    theta_ref_rad = 0.0

x_points = [-40, 0]
y_points = [-40 * np.tan(theta_in_rad), 0]

if theta_in_deg == 0:
    x_points.append(fiber_length_display)
    y_points.append(0)
elif is_within_acceptance:
    current_x = 0
    current_y = 0
    delta_x = y_core / np.tan(theta_ref_rad)
    direction = 1  
    
    while current_x < fiber_length_display:
        current_x += delta_x
        current_y = y_core * direction
        
        if current_x >= fiber_length_display:
            overshoot = current_x - fiber_length_display
            current_y = current_y - (direction * overshoot * np.tan(theta_ref_rad))
            current_x = fiber_length_display
            x_points.append(current_x)
            y_points.append(current_y)
            break
            
        x_points.append(current_x)
        y_points.append(current_y)
        direction *= -1
else:
    delta_x = y_core / np.tan(theta_ref_rad)
    x_points.append(delta_x)
    y_points.append(y_core)
    
    alpha_normal_rad = np.pi/2 - theta_ref_rad
    sin_clad = (n1 * np.sin(alpha_normal_rad)) / n2
    if sin_clad <= 1.0:
        theta_clad_rad = np.arcsin(sin_clad)
        clad_ray_angle = np.pi/2 - theta_clad_rad
        x_points.append(delta_x + 40)
        y_points.append(y_core + 40 * np.tan(clad_ray_angle))
    else:
        x_points.append(fiber_length_display)
        y_points.append(y_core + (fiber_length_display - delta_x) * np.tan(theta_ref_rad))

# Lazer Işını Rengi
fig.add_trace(go.Scatter(x=x_points, y=y_points, mode='lines+markers',
                         line=dict(color='#6366F1', width=3), name='Işık Işını',
                         marker=dict(size=4, color='#FFFFFF')))

fig.update_layout(
    xaxis=dict(title="Fiber Boyunca Mesafe (x)", range=[-50, fiber_length_display], gridcolor="#1F2937"),
    yaxis=dict(title="Çekirdek Ekseni (y)", range=[-y_core * 1.8, y_core * 1.8], gridcolor="#1F2937"),
    margin=dict(l=20, r=20, t=20, b=20),
    showlegend=True,
    template="plotly_dark",
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    height=500
)

st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------
# SABİT FOOTER İMZA ALANI
# ---------------------------------------------------------
st.markdown('<div class="footer">🚀 Developed by Fatma Sena</div>', unsafe_allow_html=True)