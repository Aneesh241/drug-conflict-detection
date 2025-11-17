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
    page_title="🐱 Kawaii Drug Checker Nyan~ 💊",
    page_icon="🎀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - Hello Kitty Dark Mode Theme
st.markdown("""
    <style>
    /* Dark mode background with kawaii colors */
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #1a1a2e 100%);
        background-attachment: fixed;
    }
    
    /* Animated floating hearts */
    @keyframes float {
        0%, 100% { transform: translateY(0px) rotate(0deg); }
        50% { transform: translateY(-20px) rotate(5deg); }
    }
    
    @keyframes bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-10px); }
    }
    
    @keyframes sparkle {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(1.2); }
    }
    
    /* Main header with kawaii pink gradient */
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(45deg, #ff69b4, #ffb6c1, #ff69b4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
        animation: sparkle 2s ease-in-out infinite;
        text-shadow: 0 0 20px rgba(255, 105, 180, 0.5);
        font-family: 'Comic Sans MS', cursive;
    }
    
    /* Kawaii metric cards */
    .metric-card {
        background: linear-gradient(135deg, #2d2d44 0%, #3d3d5c 100%);
        padding: 1.5rem;
        border-radius: 20px;
        text-align: center;
        border: 2px solid #ff69b4;
        box-shadow: 0 8px 16px rgba(255, 105, 180, 0.3);
        animation: float 3s ease-in-out infinite;
    }
    
    /* Conflict cards with cat theme */
    .conflict-major {
        background: linear-gradient(135deg, #4a1f2e 0%, #3d1a26 100%);
        padding: 1rem;
        border-left: 6px solid #ff69b4;
        border-radius: 15px;
        margin: 0.5rem 0;
        box-shadow: 0 4px 8px rgba(255, 105, 180, 0.4);
    }
    .conflict-moderate {
        background: linear-gradient(135deg, #4a3a1f 0%, #3d2f1a 100%);
        padding: 1rem;
        border-left: 6px solid #ffb6c1;
        border-radius: 15px;
        margin: 0.5rem 0;
        box-shadow: 0 4px 8px rgba(255, 182, 193, 0.4);
    }
    .conflict-minor {
        background: linear-gradient(135deg, #3a4a1f 0%, #2f3d1a 100%);
        padding: 1rem;
        border-left: 6px solid #dda0dd;
        border-radius: 15px;
        margin: 0.5rem 0;
        box-shadow: 0 4px 8px rgba(221, 160, 221, 0.4);
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #2d2d44 0%, #1a1a2e 100%);
        border-right: 3px solid #ff69b4;
    }
    
    /* Buttons with kawaii style */
    .stButton > button {
        background: linear-gradient(45deg, #ff1493, #ff69b4) !important;
        color: #000000 !important;
        border-radius: 20px;
        border: none;
        padding: 0.5rem 2rem;
        font-weight: bold;
        box-shadow: 0 4px 12px rgba(255, 105, 180, 0.4);
        transition: all 0.3s ease;
        font-family: 'Comic Sans MS', cursive;
    }
    
    .stButton > button:hover {
        transform: scale(1.05);
        background: linear-gradient(45deg, #ff69b4, #ff1493) !important;
        box-shadow: 0 6px 20px rgba(255, 105, 180, 0.6);
        animation: bounce 0.5s ease;
        color: #000000 !important;
    }
    
    .stButton > button p {
        color: #000000 !important;
    }
    
    /* Text colors for dark mode */
    h1, h2, h3, h4, h5, h6, p, span, div, label {
        color: #ffb6c1 !important;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #2d2d44 0%, #3d3d5c 100%);
        border-radius: 15px;
        border: 2px solid #ff69b4;
        color: #ffb6c1 !important;
        font-family: 'Comic Sans MS', cursive;
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #1a1a2e;
        border-radius: 15px;
        padding: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #ffb6c1 !important;
        background-color: #2d2d44;
        border-radius: 10px;
        font-family: 'Comic Sans MS', cursive;
        padding: 0.5rem 1rem;
        margin: 0.2rem;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(45deg, #c71585, #ff1493) !important;
        color: #ffffff !important;
        font-weight: bold;
    }
    
    /* Dataframe styling */
    .stDataFrame {
        border: 2px solid #ff69b4;
        border-radius: 15px;
        overflow: hidden;
    }
    
    /* Input fields */
    .stTextInput > div > div > input,
    .stSelectbox > div > div,
    .stMultiSelect > div > div {
        background-color: #2d2d44 !important;
        color: #ffb6c1 !important;
        border: 2px solid #ff69b4 !important;
        border-radius: 10px !important;
    }
    
    /* Bongo Cat Container */
    .bongo-cat {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 999;
        animation: bounce 2s ease-in-out infinite;
    }
    
    /* Floating decorations */
    .kawaii-decoration {
        position: fixed;
        font-size: 2rem;
        animation: float 4s ease-in-out infinite;
        opacity: 0.6;
        pointer-events: none;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 12px;
    }
    
    ::-webkit-scrollbar-track {
        background: #1a1a2e;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #ff69b4, #ffb6c1);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #ffb6c1, #ff69b4);
    }

    /* Recolor external Hello Kitty SVG in sidebar to theme pink without inline SVG */
    [data-testid="stSidebar"] img[src*="443128/brand-hello-kitty.svg"] {
        /* Filter chain tuned to approximate #ff69b4 */
        filter: brightness(0) saturate(100%) invert(72%) sepia(40%) saturate(746%) hue-rotate(294deg) brightness(103%) contrast(102%);
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

# Add floating kawaii decorations
st.markdown("""
    <div class="kawaii-decoration" style="top: 10%; left: 5%;">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M8 4C8 2.89543 7.10457 2 6 2C4.89543 2 4 2.89543 4 4C4 5.10457 4.89543 6 6 6C7.10457 6 8 5.10457 8 4Z" fill="#ff69b4"/>
            <path d="M20 4C20 2.89543 19.1046 2 18 2C16.8954 2 16 2.89543 16 4C16 5.10457 16.8954 6 18 6C19.1046 6 20 5.10457 20 4Z" fill="#ff69b4"/>
            <path d="M12 22C16.4183 22 20 18.4183 20 14V8C20 7.44772 19.5523 7 19 7H5C4.44772 7 4 7.44772 4 8V14C4 18.4183 7.58172 22 12 22Z" fill="#ff69b4"/>
            <circle cx="9" cy="12" r="1" fill="#1a1a2e"/>
            <circle cx="15" cy="12" r="1" fill="#1a1a2e"/>
            <path d="M10 15C10 15.5523 10.4477 16 11 16H13C13.5523 16 14 15.5523 14 15" stroke="#1a1a2e" stroke-width="1.5" stroke-linecap="round"/>
            <ellipse cx="7" cy="13" rx="0.5" ry="1" fill="#ffb6c1"/>
            <ellipse cx="17" cy="13" rx="0.5" ry="1" fill="#ffb6c1"/>
        </svg>
    </div>
    <div class="kawaii-decoration" style="top: 15%; right: 8%; animation-delay: 0.5s;">💕</div>
    <div class="kawaii-decoration" style="top: 25%; left: 10%; animation-delay: 1s;">🎀</div>
    <div class="kawaii-decoration" style="top: 40%; right: 5%; animation-delay: 1.5s;">✨</div>
    <div class="kawaii-decoration" style="top: 60%; left: 3%; animation-delay: 2s;">🌸</div>
    <div class="kawaii-decoration" style="top: 70%; right: 10%; animation-delay: 2.5s;">🐾</div>
    <div class="kawaii-decoration" style="top: 85%; left: 8%; animation-delay: 3s;">💊</div>
""", unsafe_allow_html=True)

# Bongo Cat Animation
st.markdown("""
    <div class="bongo-cat">
        <img src="https://tenor.com/bRUoc.gif" width="150" alt="Bongo Cat">
    </div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://www.svgrepo.com/show/443128/brand-hello-kitty.svg", width=100)
    st.title("🐱 Meow Navigation Nyan~")
    
    page = st.radio(
        "Select Page:",
        ["🏠 Dashboard", "👥 Patients", "💉 Prescription Simulator", "⚠️ Conflicts", "💊 Drug Database", "⚙️ Rules Engine", "🧪 Manual Testing", "📁 Import Data"]
    )
    
    st.divider()
    
    # Quick Actions
    st.subheader("✨ Quick Actions")
    if st.button("🔄 Run Simulation Nyan~", use_container_width=True, type="primary"):
        with st.spinner("Running simulation... 🐱✨"):
            run_simulation()
        st.success("Simulation completed! ฅ^•ﻌ•^ฅ")
        st.rerun()
    
    if st.session_state.simulation_run:
        st.info(f"💕 Last run: {st.session_state.last_run}")
    
    # Add cute cat image
    st.divider()
    st.image("https://http.cat/200", caption="Everything is purr-fect! 🐱", use_column_width=True)

# Main content area
st.markdown('<div class="main-header">🐱💊 Kawaii Drug Conflict Checker Nyan~ 💕✨</div>', unsafe_allow_html=True)

# ============= DASHBOARD PAGE =============
if page == "🏠 Dashboard":
    st.header("📊 Dashboard Overview ฅ^•ﻌ•^ฅ")
    
    # Load basic data
    patients_data, drugs_data, rules_data = load_data()
    
    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Patients", len(patients_data))
    
    with col2:
        st.metric("Available Drugs", len(drugs_data))
    
    with col3:
        st.metric("Active Rules", len(rules_data))
    
    with col4:
        if st.session_state.simulation_run:
            st.metric("Conflicts Detected", len(st.session_state.conflicts_df))
        else:
            st.metric("Conflicts Detected", "Run simulation")
    
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
elif page == "👥 Patients":
    st.header("👥 Patient Meow-nagement 🐾")
    
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
elif page == "💉 Prescription Simulator":
    st.header("💉 Prescription Simulation")
    
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
    st.header("⚠️ Conflict Detection Results 🐱💔")
    
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
elif page == "💊 Drug Database":
    st.header("💊 Drug Database Meow~ 🐾")
    
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
    st.header("⚙️ Conflict Detection Rules Nyan~ ✨")
    
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
    st.header("🧪 Manual Prescription Testing 🐱💕")
    
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
    st.header("📁 Import Custom Data Nyan~ 📂✨")
    
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
    <div style='text-align: center; color: #666; padding: 1rem;'>
        <p>Drug Conflict Detection System | Powered by Mesa & Streamlit</p>
    </div>
""", unsafe_allow_html=True)
