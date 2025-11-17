"""
Streamlit Web Interface for Drug Conflict Detection System
"""
import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json

from model import HealthcareModel
from agents import PatientAgent
from utils import read_csv_records

# Page configuration
st.set_page_config(
    page_title="🎀 Kitty Drug Checker 🐱",
    page_icon="🐱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - Hello Kitty Theme
st.markdown("""
    <style>
    /* Import cute fonts */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
    
    /* Global styling */
    * {
        font-family: 'Poppins', sans-serif !important;
    }
    
    /* Background and main colors */
    .stApp {
        background: linear-gradient(135deg, #FFE5E5 0%, #FFF0F5 50%, #FFE5F5 100%) !important;
    }
    
    /* Animated floating hearts background */
    .stApp::before {
        content: "💕 🎀 🐱 ✨ 💖 🌸 🎀 🐱";
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        font-size: 2rem;
        opacity: 0.1;
        animation: float 20s infinite;
        z-index: -1;
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-20px); }
    }
    
    /* Header styling */
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(45deg, #FF69B4, #FFB6C1, #FF1493);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(255, 105, 180, 0.3);
        animation: bounce 2s infinite;
    }
    
    @keyframes bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-10px); }
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #FFB6C1 0%, #FFE5E5 100%) !important;
        border-right: 3px solid #FF69B4;
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #FFE5F5, #FFF0F5);
        padding: 1.5rem;
        border-radius: 20px;
        text-align: center;
        border: 3px solid #FFB6C1;
        box-shadow: 0 8px 16px rgba(255, 105, 180, 0.2);
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: scale(1.05) rotate(2deg);
        box-shadow: 0 12px 24px rgba(255, 105, 180, 0.3);
    }
    
    /* Conflict cards with cat images from http.cat */
    .conflict-major {
        background: linear-gradient(135deg, #FFE5E5, #FFD5D5);
        padding: 1rem;
        border-left: 6px solid #FF1493;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(255, 20, 147, 0.2);
        margin: 1rem 0;
    }
    
    .conflict-moderate {
        background: linear-gradient(135deg, #FFF5E5, #FFE5D5);
        padding: 1rem;
        border-left: 6px solid #FFB6C1;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(255, 182, 193, 0.2);
        margin: 1rem 0;
    }
    
    .conflict-minor {
        background: linear-gradient(135deg, #FFFAE5, #FFF5E5);
        padding: 1rem;
        border-left: 6px solid #FFD700;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(255, 215, 0, 0.2);
        margin: 1rem 0;
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(45deg, #FF69B4, #FF1493) !important;
        color: white !important;
        border-radius: 25px !important;
        border: none !important;
        padding: 0.5rem 2rem !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 12px rgba(255, 105, 180, 0.4) !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton>button:hover {
        transform: scale(1.1) !important;
        box-shadow: 0 6px 20px rgba(255, 105, 180, 0.6) !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
        background-color: #FFE5F5;
        border-radius: 15px;
        padding: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: linear-gradient(135deg, #FFB6C1, #FFE5E5);
        border-radius: 15px;
        color: #FF1493;
        font-weight: 600;
        border: 2px solid #FF69B4;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #FF69B4, #FF1493) !important;
        color: white !important;
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #FFE5F5, #FFF0F5) !important;
        border-radius: 15px !important;
        border: 2px solid #FFB6C1 !important;
        font-weight: 600 !important;
    }
    
    /* Input fields */
    .stTextInput>div>div>input, .stSelectbox>div>div>div {
        border-radius: 15px !important;
        border: 2px solid #FFB6C1 !important;
        background-color: #FFF0F5 !important;
    }
    
    /* Dataframe */
    .dataframe {
        border-radius: 15px !important;
        border: 3px solid #FFB6C1 !important;
    }
    
    /* Radio buttons */
    .stRadio>div {
        background: linear-gradient(135deg, #FFE5F5, #FFF0F5);
        padding: 1rem;
        border-radius: 15px;
        border: 2px solid #FFB6C1;
    }
    
    /* Multiselect */
    .stMultiSelect>div>div>div {
        background-color: #FFF0F5 !important;
        border-radius: 15px !important;
        border: 2px solid #FFB6C1 !important;
    }
    
    /* Success/Error/Info boxes */
    .stSuccess, .stError, .stWarning, .stInfo {
        border-radius: 15px !important;
        border-left: 6px solid #FF69B4 !important;
    }
    
    /* Sparkles effect */
    @keyframes sparkle {
        0%, 100% { opacity: 0; }
        50% { opacity: 1; }
    }
    
    .sparkle {
        animation: sparkle 1.5s infinite;
    }
    
    /* Cat paw prints */
    .paw-print {
        font-size: 1.5rem;
        opacity: 0.3;
        position: absolute;
        animation: fadeInOut 3s infinite;
    }
    
    @keyframes fadeInOut {
        0%, 100% { opacity: 0.1; }
        50% { opacity: 0.3; }
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'model' not in st.session_state:
    st.session_state.model = None
if 'conflicts_df' not in st.session_state:
    st.session_state.conflicts_df = None
if 'simulation_run' not in st.session_state:
    st.session_state.simulation_run = False
if 'custom_data_uploaded' not in st.session_state:
    st.session_state.custom_data_uploaded = False
if 'custom_patients' not in st.session_state:
    st.session_state.custom_patients = None
if 'custom_drugs' not in st.session_state:
    st.session_state.custom_drugs = None
if 'custom_rules' not in st.session_state:
    st.session_state.custom_rules = None

# Helper functions
def load_data():
    """Load CSV data files"""
    # Use custom data if uploaded, otherwise use default files
    if st.session_state.custom_data_uploaded:
        base_dir = Path(__file__).parent
        
        # Load custom or default data
        if st.session_state.custom_patients is not None:
            patients = st.session_state.custom_patients
        else:
            patients = read_csv_records(base_dir / "patients.csv")
        
        if st.session_state.custom_drugs is not None:
            drugs = st.session_state.custom_drugs
        else:
            drugs = read_csv_records(base_dir / "drugs.csv")
        
        if st.session_state.custom_rules is not None:
            rules = st.session_state.custom_rules
        else:
            rules = read_csv_records(base_dir / "rules.csv")
        
        return patients, drugs, rules
    else:
        base_dir = Path(__file__).parent
        patients = read_csv_records(base_dir / "patients.csv")
        drugs = read_csv_records(base_dir / "drugs.csv")
        rules = read_csv_records(base_dir / "rules.csv")
        return patients, drugs, rules

def save_uploaded_file(uploaded_file, file_type):
    """Process and save uploaded CSV file to session state"""
    try:
        # Read the uploaded file
        df = pd.read_csv(uploaded_file)
        
        # Convert DataFrame to list of dictionaries
        data = df.to_dict('records')
        
        # Process based on file type
        if file_type == "patients":
            # Process conditions and allergies fields
            for record in data:
                if 'conditions' in record and isinstance(record['conditions'], str):
                    record['conditions'] = record['conditions'].split(';')
                if 'allergies' in record and isinstance(record['allergies'], str):
                    record['allergies'] = record['allergies'].split(';')
            st.session_state.custom_patients = data
            
        elif file_type == "drugs":
            st.session_state.custom_drugs = data
            
        elif file_type == "rules":
            st.session_state.custom_rules = data
        
        st.session_state.custom_data_uploaded = True
        return True, f"{file_type.capitalize()} data uploaded successfully!"
    
    except Exception as e:
        return False, f"Error uploading {file_type}: {str(e)}"

def run_simulation():
    """Run the drug conflict detection simulation"""
    base_dir = Path(__file__).parent
    
    # Save custom data to temporary CSV files if uploaded
    if st.session_state.custom_data_uploaded:
        temp_dir = base_dir / "temp_data"
        temp_dir.mkdir(exist_ok=True)
        
        # Save custom data to temp files
        if st.session_state.custom_patients is not None:
            temp_patients = pd.DataFrame(st.session_state.custom_patients)
            # Convert lists back to semicolon-separated strings
            if 'conditions' in temp_patients.columns:
                temp_patients['conditions'] = temp_patients['conditions'].apply(
                    lambda x: ';'.join(x) if isinstance(x, list) else x
                )
            if 'allergies' in temp_patients.columns:
                temp_patients['allergies'] = temp_patients['allergies'].apply(
                    lambda x: ';'.join(x) if isinstance(x, list) else x
                )
            temp_patients.to_csv(temp_dir / "patients.csv", index=False)
        else:
            # Copy default file
            import shutil
            shutil.copy(base_dir / "patients.csv", temp_dir / "patients.csv")
        
        if st.session_state.custom_drugs is not None:
            pd.DataFrame(st.session_state.custom_drugs).to_csv(temp_dir / "drugs.csv", index=False)
        else:
            import shutil
            shutil.copy(base_dir / "drugs.csv", temp_dir / "drugs.csv")
        
        if st.session_state.custom_rules is not None:
            pd.DataFrame(st.session_state.custom_rules).to_csv(temp_dir / "rules.csv", index=False)
        else:
            import shutil
            shutil.copy(base_dir / "rules.csv", temp_dir / "rules.csv")
        
        # Run model with temp data
        model = HealthcareModel(data_dir=temp_dir)
    else:
        # Run model with default data
        model = HealthcareModel(data_dir=base_dir)
    
    model.run(steps=1)
    
    st.session_state.model = model
    st.session_state.conflicts_df = model.conflicts_dataframe()
    st.session_state.simulation_run = True
    st.session_state.last_run = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_severity_color(severity):
    """Return color based on severity"""
    colors = {
        'Major': '#f44336',
        'Moderate': '#ff9800',
        'Minor': '#fbc02d'
    }
    return colors.get(severity, '#757575')

# Sidebar
with st.sidebar:
    # Hello Kitty image
    st.markdown("""
        <div style='text-align: center;'>
            <img src='https://http.cat/200' width='150' style='border-radius: 20px; border: 3px solid #FF69B4;'/>
            <h2 style='color: #FF1493; margin-top: 1rem;'>🎀 Kitty Menu 🐱</h2>
        </div>
    """, unsafe_allow_html=True)
    
    page = st.radio(
        "🌸 Navigate:",
        ["🏠 Dashboard", "🐱 Patients", "💊 Prescription Simulator", "⚠️ Conflicts", "🎀 Drug Database", "⚙️ Rules Engine", "🧪 Manual Testing", "📁 Import Data"]
    )
    
    st.divider()
    
    # Quick Actions
    st.subheader("✨ Quick Actions ✨")
    if st.button("🔄 Run Simulation 🎀", use_container_width=True, type="primary"):
        with st.spinner("🐱 Meow! Running simulation..."):
            run_simulation()
        st.success("🎉 Simulation completed! Nya~ 🐱")
        st.rerun()
    
    if st.session_state.simulation_run:
        st.info(f"🕐 Last run: {st.session_state.last_run}")
    
    # Add cute cat facts
    st.markdown("---")
    st.markdown("""
        <div style='background: linear-gradient(135deg, #FFE5F5, #FFF0F5); padding: 1rem; border-radius: 15px; border: 2px solid #FFB6C1;'>
            <p style='text-align: center; font-size: 0.9rem; color: #FF1493;'>
                😸 Did you know? Cats spend 70% of their lives sleeping! 💤
            </p>
        </div>
    """, unsafe_allow_html=True)

# Main content area with animated header
st.markdown("""
    <div class="main-header">
        🎀 Kitty Drug Checker 🐱✨
        <div style='font-size: 1rem; color: #FF69B4; font-weight: normal; margin-top: 0.5rem;'>
            Making healthcare kawaii, one prescription at a time! 💕
        </div>
    </div>
""", unsafe_allow_html=True)

# ============= DASHBOARD PAGE =============
if page == "🏠 Dashboard":
    st.markdown("## 📊 Dashboard Nya~verview 🐱")
    
    # Load basic data
    patients_data, drugs_data, rules_data = load_data()
    
    # Top metrics with cat images
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
            <div class="metric-card">
                <img src='https://http.cat/100' width='60' style='border-radius: 10px;'/>
                <h3 style='color: #FF1493; margin: 0.5rem 0;'>{len(patients_data)}</h3>
                <p style='color: #FF69B4; font-weight: 600;'>Total Patients 🐱</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div class="metric-card">
                <img src='https://http.cat/201' width='60' style='border-radius: 10px;'/>
                <h3 style='color: #FF1493; margin: 0.5rem 0;'>{len(drugs_data)}</h3>
                <p style='color: #FF69B4; font-weight: 600;'>Available Drugs 💊</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
            <div class="metric-card">
                <img src='https://http.cat/202' width='60' style='border-radius: 10px;'/>
                <h3 style='color: #FF1493; margin: 0.5rem 0;'>{len(rules_data)}</h3>
                <p style='color: #FF69B4; font-weight: 600;'>Active Rules ⚙️</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        if st.session_state.simulation_run:
            st.markdown(f"""
                <div class="metric-card">
                    <img src='https://http.cat/203' width='60' style='border-radius: 10px;'/>
                    <h3 style='color: #FF1493; margin: 0.5rem 0;'>{len(st.session_state.conflicts_df)}</h3>
                    <p style='color: #FF69B4; font-weight: 600;'>Conflicts Detected ⚠️</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class="metric-card">
                    <img src='https://http.cat/404' width='60' style='border-radius: 10px;'/>
                    <h3 style='color: #FF1493; margin: 0.5rem 0;'>?</h3>
                    <p style='color: #FF69B4; font-weight: 600;'>Run simulation 🔄</p>
                </div>
            """, unsafe_allow_html=True)
    
    st.divider()
    
    # Simulation results
    if st.session_state.simulation_run and st.session_state.conflicts_df is not None:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📈 Conflict Analysis")
            
            df = st.session_state.conflicts_df
            if len(df) > 0:
                # Severity distribution
                sev_counts = df['severity'].value_counts()
                
                fig = px.pie(
                    values=sev_counts.values,
                    names=sev_counts.index,
                    title="Conflicts by Severity",
                    color=sev_counts.index,
                    color_discrete_map={'Major': '#f44336', 'Moderate': '#ff9800', 'Minor': '#fbc02d'}
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Conflict type distribution
                type_counts = df['type'].value_counts()
                fig2 = px.bar(
                    x=type_counts.index,
                    y=type_counts.values,
                    title="Conflicts by Type",
                    labels={'x': 'Conflict Type', 'y': 'Count'},
                    color=type_counts.values,
                    color_continuous_scale='Blues'
                )
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.success("✅ No conflicts detected! All prescriptions are safe.")
        
        with col2:
            st.subheader("📋 Summary Statistics")
            
            if len(df) > 0:
                st.metric("Total Conflicts", len(df))
                
                st.write("**By Severity:**")
                for sev in ['Major', 'Moderate', 'Minor']:
                    count = len(df[df['severity'] == sev])
                    if count > 0:
                        st.markdown(f"- **{sev}**: {count}")
                
                st.write("**By Type:**")
                for ctype in df['type'].unique():
                    count = len(df[df['type'] == ctype])
                    st.markdown(f"- {ctype}: {count}")
                
                # Patient risk ranking
                st.write("**Patients at Risk:**")
                patient_conflicts = df.groupby('patient_name').size().sort_values(ascending=False)
                for patient, count in patient_conflicts.items():
                    st.markdown(f"- {patient}: {count} conflict(s)")
            else:
                st.info("No conflicts to display")
    else:
        st.info("👆 Click 'Run Simulation' in the sidebar to see results")

# ============= PATIENTS PAGE =============
elif page == "🐱 Patients":
    st.markdown("## 🐱 Meow-nagement (Patient Profiles) 💕")
    
    patients_data, _, _ = load_data()
    
    # Display patients table
    st.subheader("Patient Records")
    
    # Convert to DataFrame for display
    patients_df = pd.DataFrame(patients_data)
    
    # Format lists for display
    if not patients_df.empty:
        patients_df['conditions'] = patients_df['conditions'].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)
        patients_df['allergies'] = patients_df['allergies'].apply(lambda x: ', '.join(x) if isinstance(x, list) and x != ['None'] else 'None')
    
    st.dataframe(patients_df, use_container_width=True, height=400)
    
    st.divider()
    
    # Patient details cards
    st.subheader("Patient Details")
    
    for patient in patients_data:
        with st.expander(f"👤 {patient['name']} (ID: {patient['id']})"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Conditions:**")
                conditions = patient.get('conditions', [])
                # Handle different data types for conditions
                if isinstance(conditions, list):
                    conditions = [str(c) for c in conditions if c]
                elif conditions and str(conditions).lower() not in ['none', 'nan']:
                    conditions = [str(conditions)]
                else:
                    conditions = []
                
                if conditions:
                    for cond in conditions:
                        st.markdown(f"- {cond}")
                else:
                    st.write("None")
            
            with col2:
                st.write("**Allergies:**")
                allergies = patient.get('allergies', [])
                # Handle different data types and filter out None, 'None', and NaN values
                if isinstance(allergies, list):
                    allergies = [str(a) for a in allergies if a and str(a).lower() not in ['none', 'nan']]
                elif allergies and str(allergies).lower() not in ['none', 'nan']:
                    allergies = [str(allergies)]
                else:
                    allergies = []
                
                if allergies:
                    for allergy in allergies:
                        st.markdown(f"- {allergy}")
                else:
                    st.write("None")
            
            # Show prescription if simulation has run
            if st.session_state.model:
                patient_obj = next((p for p in st.session_state.model.patients if p.patient_id == str(patient['id'])), None)
                if patient_obj and patient_obj.prescription:
                    st.write("**Current Prescription:**")
                    for drug in patient_obj.prescription:
                        st.markdown(f"- 💊 {drug}")

# ============= PRESCRIPTION SIMULATOR PAGE =============
elif page == "💊 Prescription Simulator":
    st.markdown("## 💊 Kitty's Prescription Lab 🧪✨")
    
    if not st.session_state.simulation_run:
        st.warning("No simulation has been run yet. Click 'Run Simulation' in the sidebar.")
    else:
        model = st.session_state.model
        
        st.subheader("Prescription Results")
        
        for patient in model.patients:
            with st.expander(f"👤 {patient.name}", expanded=True):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.write("**Patient Profile:**")
                    st.write(f"- ID: {patient.patient_id}")
                    st.write(f"- Conditions: {', '.join(patient.conditions) if isinstance(patient.conditions, list) else patient.conditions}")
                    allergies = patient.allergies if isinstance(patient.allergies, list) else [patient.allergies]
                    # Convert all items to strings to handle any float/NaN values
                    allergies = [str(a) for a in allergies if a and str(a).lower() not in ['none', 'nan']]
                    st.write(f"- Allergies: {', '.join(allergies) if allergies else 'None'}")
                
                with col2:
                    st.write("**Prescribed Drugs:**")
                    if patient.prescription:
                        for drug in patient.prescription:
                            st.markdown(f"💊 **{drug}**")
                    else:
                        st.write("No prescription")
                
                with col3:
                    # Count conflicts for this patient
                    if st.session_state.conflicts_df is not None:
                        patient_conflicts = st.session_state.conflicts_df[
                            st.session_state.conflicts_df['patient_id'] == patient.patient_id
                        ]
                        conflict_count = len(patient_conflicts)
                        
                        if conflict_count > 0:
                            st.error(f"⚠️ {conflict_count} conflict(s)")
                        else:
                            st.success("✅ Safe")

# ============= CONFLICTS PAGE =============
elif page == "⚠️ Conflicts":
    st.markdown("## ⚠️ Conflict Meow-nitoring 🐱💔")
    
    if not st.session_state.simulation_run:
        st.warning("No simulation has been run yet. Click 'Run Simulation' in the sidebar.")
    else:
        df = st.session_state.conflicts_df
        
        if len(df) == 0:
            st.success("✅ No conflicts detected! All prescriptions are safe.")
        else:
            # Filters
            col1, col2, col3 = st.columns(3)
            
            with col1:
                severity_filter = st.multiselect(
                    "Filter by Severity:",
                    options=df['severity'].unique(),
                    default=None,
                    placeholder="All severities"
                )
            
            with col2:
                type_filter = st.multiselect(
                    "Filter by Type:",
                    options=df['type'].unique(),
                    default=None,
                    placeholder="All types"
                )
            
            with col3:
                patient_filter = st.multiselect(
                    "Filter by Patient:",
                    options=df['patient_name'].unique(),
                    default=None,
                    placeholder="All patients"
                )
            
            # Apply filters - if empty, show all
            filtered_df = df.copy()
            if severity_filter:
                filtered_df = filtered_df[filtered_df['severity'].isin(severity_filter)]
            if type_filter:
                filtered_df = filtered_df[filtered_df['type'].isin(type_filter)]
            if patient_filter:
                filtered_df = filtered_df[filtered_df['patient_name'].isin(patient_filter)]
            
            st.divider()
            
            # Display filtered conflicts
            st.subheader(f"Showing {len(filtered_df)} conflict(s)")
            
            for idx, row in filtered_df.iterrows():
                severity_class = f"conflict-{row['severity'].lower()}"
                
                with st.container():
                    st.markdown(f'<div class="{severity_class}">', unsafe_allow_html=True)
                    
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.write(f"**Patient:** {row['patient_name']}")
                        st.write(f"**Type:** {row['type']}")
                        st.write(f"**Conflict:** {row['item_a']} ↔️ {row['item_b']}")
                    
                    with col2:
                        st.write(f"**Prescription:** {row['prescription']}")
                        st.write(f"**Recommendation:** {row['recommendation']}")
                    
                    with col3:
                        st.write(f"**Severity:** {row['severity']}")
                        st.write(f"**Score:** {row['score']}")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    st.divider()
            
            # Export button
            st.download_button(
                label="📥 Download Conflicts Report (CSV)",
                data=filtered_df.to_csv(index=False),
                file_name=f"conflicts_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

# ============= DRUG DATABASE PAGE =============
elif page == "🎀 Drug Database":
    st.markdown("## 🎀 Kitty's Medicine Cabinet 💊✨")
    
    _, drugs_data, _ = load_data()
    
    # Search
    search_term = st.text_input("🔍 Search drugs by name, condition, or category:", "")
    
    drugs_df = pd.DataFrame(drugs_data)
    
    if search_term:
        drugs_df = drugs_df[
            drugs_df.apply(lambda row: search_term.lower() in str(row).lower(), axis=1)
        ]
    
    st.dataframe(drugs_df, use_container_width=True, height=400)
    
    st.divider()
    
    # Drug details
    st.subheader("Drug Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**By Category:**")
        category_counts = drugs_df['category'].value_counts()
        for cat, count in category_counts.items():
            st.markdown(f"- {cat}: {count} drug(s)")
    
    with col2:
        st.write("**By Condition:**")
        condition_counts = drugs_df['condition'].value_counts()
        for cond, count in condition_counts.items():
            st.markdown(f"- {cond}: {count} drug(s)")

# ============= RULES ENGINE PAGE =============
elif page == "⚙️ Rules Engine":
    st.markdown("## ⚙️ Kitty's Rule Book 📖🐱")
    
    _, _, rules_data = load_data()
    
    rules_df = pd.DataFrame(rules_data)
    
    # Convert all columns to strings to avoid Arrow serialization issues
    for col in rules_df.columns:
        rules_df[col] = rules_df[col].astype(str)
    
    # Search
    search_term = st.text_input("🔍 Search rules:", "")
    
    if search_term:
        rules_df = rules_df[
            rules_df.apply(lambda row: search_term.lower() in str(row).lower(), axis=1)
        ]
    
    st.dataframe(rules_df, use_container_width=True, height=400)
    
    st.divider()
    
    # Rule statistics
    if st.session_state.conflicts_df is not None and len(st.session_state.conflicts_df) > 0:
        st.subheader("📊 Rule Trigger Statistics")
        
        conflicts_df = st.session_state.conflicts_df
        
        # Count how many times each rule was triggered
        rule_triggers = {}
        for _, conflict in conflicts_df.iterrows():
            key = f"{conflict['item_a']} - {conflict['item_b']}"
            rule_triggers[key] = rule_triggers.get(key, 0) + 1
        
        if rule_triggers:
            fig = px.bar(
                x=list(rule_triggers.keys()),
                y=list(rule_triggers.values()),
                title="Most Frequently Triggered Rules",
                labels={'x': 'Rule', 'y': 'Trigger Count'}
            )
            st.plotly_chart(fig, use_container_width=True)

# ============= MANUAL TESTING PAGE =============
elif page == "🧪 Manual Testing":
    st.markdown("## 🧪 Kitty's Test Lab 🔬✨")
    
    st.write("Test drug combinations for a patient manually to check for conflicts.")
    
    _, drugs_data, _ = load_data()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Patient Information")
        
        patient_name = st.text_input("Patient Name:", "Test Patient")
        
        all_conditions = ["Hypertension", "Diabetes", "Infection", "Pain", "Anticoagulation"]
        selected_conditions = st.multiselect("Select Conditions:", all_conditions)
        
        all_allergies = ["None", "Penicillin", "Aspirin", "Sulfa"]
        selected_allergies = st.multiselect("Select Allergies:", all_allergies, default=["None"])
    
    with col2:
        st.subheader("Prescription")
        
        drug_names = [drug['drug'] for drug in drugs_data]
        selected_drugs = st.multiselect("Select Drugs:", drug_names)
    
    st.divider()
    
    if st.button("🔍 Check for Conflicts", type="primary"):
        if not selected_drugs:
            st.warning("Please select at least one drug.")
        else:
            with st.spinner("Checking for conflicts..."):
                # Create temporary model and test
                base_dir = Path(__file__).parent
                model = HealthcareModel(data_dir=base_dir)
                
                conflicts = model.rule_engine.check_conflicts(
                    prescription=selected_drugs,
                    conditions=selected_conditions,
                    allergies=selected_allergies if selected_allergies != ["None"] else []
                )
                
                st.subheader("Results")
                
                if conflicts:
                    st.error(f"⚠️ {len(conflicts)} conflict(s) detected!")
                    
                    for conflict in conflicts:
                        severity_class = f"conflict-{conflict['severity'].lower()}"
                        
                        with st.container():
                            st.markdown(f'<div class="{severity_class}">', unsafe_allow_html=True)
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write(f"**Type:** {conflict['type']}")
                                st.write(f"**Conflict:** {conflict['item_a']} ↔️ {conflict['item_b']}")
                                st.write(f"**Severity:** {conflict['severity']}")
                            
                            with col2:
                                st.write(f"**Score:** {conflict['score']}")
                                st.write(f"**Recommendation:** {conflict['recommendation']}")
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.success("✅ No conflicts detected! This prescription is safe.")

# ============= IMPORT DATA PAGE =============
elif page == "📁 Import Data":
    st.markdown("## 📁 Kitty's Data Import Nya~ 🐱📊")
    
    st.write("""
    Upload your own CSV files to customize the database. The files should follow the same format as the default files.
    After uploading, run the simulation to see results with your custom data.
    """)
    
    st.divider()
    
    # Create tabs for different file types
    tab1, tab2, tab3 = st.tabs(["📋 Patients", "💊 Drugs", "⚙️ Rules"])
    
    with tab1:
        st.subheader("Upload Patients Database")
        
        st.write("**Required columns:** `id`, `name`, `conditions`, `allergies`")
        st.write("**Format:** Use semicolons (;) to separate multiple conditions or allergies")
        
        st.code("""id,name,conditions,allergies
1,John Doe,Hypertension;Diabetes,Penicillin
            2,Jane Smith,Infection,None""", language="csv")
        
        patients_file = st.file_uploader("Choose patients CSV file", type=['csv'], key="patients_upload")
        
        if patients_file is not None:
            # Show preview
            preview_df = pd.read_csv(patients_file)
            st.write("**Preview:**")
            st.dataframe(preview_df.head(), use_container_width=True)
            
            # Reset file pointer
            patients_file.seek(0)
            
            if st.button("✅ Upload Patients Data", key="upload_patients_btn"):
                success, message = save_uploaded_file(patients_file, "patients")
                if success:
                    st.success(message)
                    st.session_state.simulation_run = False  # Reset simulation
                else:
                    st.error(message)
        
        # Show current status
        if st.session_state.custom_patients is not None:
            st.info(f"✓ Custom patients data loaded ({len(st.session_state.custom_patients)} patients)")
        else:
            st.info("Using default patients database")
        
        # Reset button
        if st.session_state.custom_patients is not None:
            if st.button("🔄 Reset to Default", key="reset_patients"):
                st.session_state.custom_patients = None
                st.session_state.simulation_run = False
                st.success("Reset to default patients data")
                st.rerun()
    
    with tab2:
        st.subheader("Upload Drugs Database")
        
        st.write("**Required columns:** `drug`, `condition`, `category`, `replacements`")
        
        st.code("""drug,condition,category,replacements
Lisinopril,Hypertension,ACE Inhibitor,Losartan
Metformin,Diabetes,Biguanide,Glipizide""", language="csv")
        
        drugs_file = st.file_uploader("Choose drugs CSV file", type=['csv'], key="drugs_upload")
        
        if drugs_file is not None:
            # Show preview
            preview_df = pd.read_csv(drugs_file)
            st.write("**Preview:**")
            st.dataframe(preview_df.head(), use_container_width=True)
            
            # Reset file pointer
            drugs_file.seek(0)
            
            if st.button("✅ Upload Drugs Data", key="upload_drugs_btn"):
                success, message = save_uploaded_file(drugs_file, "drugs")
                if success:
                    st.success(message)
                    st.session_state.simulation_run = False
                else:
                    st.error(message)
        
        # Show current status
        if st.session_state.custom_drugs is not None:
            st.info(f"✓ Custom drugs data loaded ({len(st.session_state.custom_drugs)} drugs)")
        else:
            st.info("Using default drugs database")
        
        # Reset button
        if st.session_state.custom_drugs is not None:
            if st.button("🔄 Reset to Default", key="reset_drugs"):
                st.session_state.custom_drugs = None
                st.session_state.simulation_run = False
                st.success("Reset to default drugs data")
                st.rerun()
    
    with tab3:
        st.subheader("Upload Rules Database")
        
        st.write("**Required columns:** `type`, `item_a`, `item_b`, `severity`, `recommendation`, `notes`")
        
        st.code("""type,item_a,item_b,severity,recommendation,notes
drug-drug,Aspirin,Warfarin,Major,Avoid combination,Bleeding risk
drug-condition,Hypertension,Ibuprofen,Moderate,Prefer Paracetamol,May raise BP""", language="csv")
        
        rules_file = st.file_uploader("Choose rules CSV file", type=['csv'], key="rules_upload")
        
        if rules_file is not None:
            # Show preview
            preview_df = pd.read_csv(rules_file)
            st.write("**Preview:**")
            st.dataframe(preview_df.head(), use_container_width=True)
            
            # Reset file pointer
            rules_file.seek(0)
            
            if st.button("✅ Upload Rules Data", key="upload_rules_btn"):
                success, message = save_uploaded_file(rules_file, "rules")
                if success:
                    st.success(message)
                    st.session_state.simulation_run = False
                else:
                    st.error(message)
        
        # Show current status
        if st.session_state.custom_rules is not None:
            st.info(f"✓ Custom rules data loaded ({len(st.session_state.custom_rules)} rules)")
        else:
            st.info("Using default rules database")
        
        # Reset button
        if st.session_state.custom_rules is not None:
            if st.button("🔄 Reset to Default", key="reset_rules"):
                st.session_state.custom_rules = None
                st.session_state.simulation_run = False
                st.success("Reset to default rules data")
                st.rerun()
    
    st.divider()
    
    # Download templates
    st.subheader("📥 Download Templates")
    st.write("Download the current database files as templates for your custom data:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        patients_data, _, _ = load_data()
        patients_df = pd.DataFrame(patients_data)
        if not patients_df.empty and 'conditions' in patients_df.columns:
            patients_df['conditions'] = patients_df['conditions'].apply(
                lambda x: ';'.join(x) if isinstance(x, list) else x
            )
        if not patients_df.empty and 'allergies' in patients_df.columns:
            patients_df['allergies'] = patients_df['allergies'].apply(
                lambda x: ';'.join(x) if isinstance(x, list) else x
            )
        st.download_button(
            label="📋 Download Patients Template",
            data=patients_df.to_csv(index=False),
            file_name="patients_template.csv",
            mime="text/csv"
        )
    
    with col2:
        _, drugs_data, _ = load_data()
        drugs_df = pd.DataFrame(drugs_data)
        st.download_button(
            label="💊 Download Drugs Template",
            data=drugs_df.to_csv(index=False),
            file_name="drugs_template.csv",
            mime="text/csv"
        )
    
    with col3:
        _, _, rules_data = load_data()
        rules_df = pd.DataFrame(rules_data)
        st.download_button(
            label="⚙️ Download Rules Template",
            data=rules_df.to_csv(index=False),
            file_name="rules_template.csv",
            mime="text/csv"
        )
    
    st.divider()
    
    # Reset all
    if st.session_state.custom_data_uploaded:
        st.subheader("🔄 Reset All Data")
        if st.button("⚠️ Reset All to Default", type="secondary"):
            st.session_state.custom_patients = None
            st.session_state.custom_drugs = None
            st.session_state.custom_rules = None
            st.session_state.custom_data_uploaded = False
            st.session_state.simulation_run = False
            st.success("All data reset to defaults!")
            st.rerun()

# Footer
st.divider()
st.markdown("""
    <div style='text-align: center; padding: 2rem; background: linear-gradient(135deg, #FFE5F5, #FFF0F5); border-radius: 20px; border: 3px solid #FFB6C1;'>
        <img src='https://http.cat/200' width='100' style='border-radius: 15px; margin-bottom: 1rem;'/>
        <p style='color: #FF1493; font-size: 1.2rem; font-weight: 600; margin: 0;'>
            🎀 Kitty Drug Checker 🐱
        </p>
        <p style='color: #FF69B4; font-size: 0.9rem; margin: 0.5rem 0 0 0;'>
            Powered by Mesa, Streamlit & Lots of Kawaii Love 💕✨
        </p>
        <p style='color: #FFB6C1; font-size: 0.8rem; margin: 0.5rem 0 0 0;'>
            Made with 💖 by Aneesh | Cat images from http.cat 🐱
        </p>
    </div>
""", unsafe_allow_html=True)
