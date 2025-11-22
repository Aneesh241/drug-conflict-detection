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
from utils import load_patients, load_drugs, load_rules, build_rules_kb, get_conflicts_cached
try:
    from audit_log import get_audit_logger, EventType, Severity
    AUDIT_ENABLED = True
except ImportError:
    AUDIT_ENABLED = False

# Page configuration
st.set_page_config(
    page_title="Drug Conflict Detection System",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    .conflict-major {
        background-color: #ffebee;
        padding: 0.5rem;
        border-left: 4px solid #f44336;
    }
    .conflict-moderate {
        background-color: #fff3e0;
        padding: 0.5rem;
        border-left: 4px solid #ff9800;
    }
    .conflict-minor {
        background-color: #fff9c4;
        padding: 0.5rem;
        border-left: 4px solid #fbc02d;
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
if 'cached_kb' not in st.session_state:
    st.session_state.cached_kb = None

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
            patients = load_patients(base_dir / "patients.csv")
        
        if st.session_state.custom_drugs is not None:
            drugs = st.session_state.custom_drugs
        else:
            drugs = load_drugs(base_dir / "drugs.csv")
        
        if st.session_state.custom_rules is not None:
            rules = st.session_state.custom_rules
        else:
            rules = load_rules(base_dir / "rules.csv")
        
        return patients, drugs, rules
    else:
        base_dir = Path(__file__).parent
        patients = load_patients(base_dir / "patients.csv")
        drugs = load_drugs(base_dir / "drugs.csv")
        rules = load_rules(base_dir / "rules.csv")
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
    st.image("https://img.icons8.com/color/96/000000/pill.png", width=80)
    st.title("🏥 Navigation")
    
    page = st.radio(
        "Select Page:",
        ["Dashboard", "Patients", "Prescription Simulator", "Conflicts", "Drug Database", "Rules Engine", "Manual Testing", "Import Data", "Audit Logs"]
    )
    
    st.divider()
    
    # Quick Actions
    st.subheader("Quick Actions")
    if st.button("🔄 Run Simulation", use_container_width=True, type="primary"):
        with st.spinner("Running simulation..."):
            run_simulation()
        st.success("Simulation completed!")
        st.rerun()
    
    if st.session_state.simulation_run:
        st.info(f"Last run: {st.session_state.last_run}")

# Main content area
st.markdown('<div class="main-header">💊 Drug Conflict Detection System</div>', unsafe_allow_html=True)

# ============= DASHBOARD PAGE =============
if page == "Dashboard":
    st.header("📊 Dashboard Overview")
    
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
elif page == "Patients":
    st.header("👥 Patient Management")
    
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
elif page == "Prescription Simulator":
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
elif page == "Conflicts":
    st.header("⚠️ Conflict Detection Results")
    
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
            
            # Export buttons
            st.subheader("📥 Export Options")
            
            col_e1, col_e2, col_e3 = st.columns(3)
            
            with col_e1:
                st.download_button(
                    label="📊 Download CSV",
                    data=filtered_df.to_csv(index=False),
                    file_name=f"conflicts_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col_e2:
                if st.button("📕 Generate PDF Report", use_container_width=True):
                    try:
                        from report_generator import ReportGenerator
                        
                        # Group conflicts by patient for comprehensive report
                        if len(filtered_df) > 0:
                            # Take first patient or generate summary
                            first_row = filtered_df.iloc[0]
                            patient_name = first_row['patient_name']
                            
                            # Get prescription details
                            prescription = first_row['prescription'].split(', ') if ', ' in first_row['prescription'] else [first_row['prescription']]
                            
                            # Prepare conflicts list
                            conflicts_list = []
                            for _, row in filtered_df.iterrows():
                                conflicts_list.append({
                                    'type': row['type'],
                                    'item_a': row['item_a'],
                                    'item_b': row['item_b'],
                                    'severity': row['severity'],
                                    'recommendation': row['recommendation'],
                                    'score': row['score']
                                })
                            
                            generator = ReportGenerator()
                            pdf_bytes = generator.generate_report_bytes(
                                format_type='pdf',
                                patient_name=patient_name,
                                patient_id=f"SIM-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                                conditions=[],
                                allergies=[],
                                prescription=prescription,
                                conflicts=conflicts_list
                            )
                            
                            filename = f"simulation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                            st.download_button(
                                label="💾 Save PDF",
                                data=pdf_bytes,
                                file_name=filename,
                                mime="application/pdf",
                                use_container_width=True,
                                key="pdf_download_conflicts"
                            )
                            st.success("✅ PDF report ready!")
                        
                    except ImportError:
                        st.error("📦 Install reportlab: `pip install reportlab`")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
            
            with col_e3:
                if st.button("📘 Generate Word Report", use_container_width=True):
                    try:
                        from report_generator import ReportGenerator
                        
                        if len(filtered_df) > 0:
                            first_row = filtered_df.iloc[0]
                            patient_name = first_row['patient_name']
                            prescription = first_row['prescription'].split(', ') if ', ' in first_row['prescription'] else [first_row['prescription']]
                            
                            conflicts_list = []
                            for _, row in filtered_df.iterrows():
                                conflicts_list.append({
                                    'type': row['type'],
                                    'item_a': row['item_a'],
                                    'item_b': row['item_b'],
                                    'severity': row['severity'],
                                    'recommendation': row['recommendation'],
                                    'score': row['score']
                                })
                            
                            generator = ReportGenerator()
                            word_bytes = generator.generate_report_bytes(
                                format_type='word',
                                patient_name=patient_name,
                                patient_id=f"SIM-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                                conditions=[],
                                allergies=[],
                                prescription=prescription,
                                conflicts=conflicts_list
                            )
                            
                            filename = f"simulation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
                            st.download_button(
                                label="💾 Save Word",
                                data=word_bytes,
                                file_name=filename,
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                use_container_width=True,
                                key="word_download_conflicts"
                            )
                            st.success("✅ Word report ready!")
                        
                    except ImportError:
                        st.error("📦 Install python-docx: `pip install python-docx`")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

# ============= DRUG DATABASE PAGE =============
elif page == "Drug Database":
    st.header("💊 Drug Database")
    
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
elif page == "Rules Engine":
    st.header("⚙️ Conflict Detection Rules")
    
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
elif page == "Manual Testing":
    st.header("🧪 Manual Prescription Testing")
    
    st.write("Test drug combinations for a patient manually. Conflicts are detected in real-time as you select drugs.")
    
    _, drugs_data, _ = load_data()
    
    # Initialize session state for real-time testing
    if 'rt_conditions' not in st.session_state:
        st.session_state.rt_conditions = []
    if 'rt_allergies' not in st.session_state:
        st.session_state.rt_allergies = ["None"]
    if 'rt_drugs' not in st.session_state:
        st.session_state.rt_drugs = []
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Patient Information")
        
        patient_name = st.text_input("Patient Name:", "Test Patient")
        
        all_conditions = ["Hypertension", "Diabetes", "Infection", "Pain", "Anticoagulation", "Heart Failure", "GERD"]
        selected_conditions = st.multiselect("Select Conditions:", all_conditions, key="manual_conditions")
        
        all_allergies = ["None", "Penicillin", "Aspirin", "Ibuprofen", "Sulfa"]
        selected_allergies = st.multiselect("Select Allergies:", all_allergies, default=["None"], key="manual_allergies")
    
    with col2:
        st.subheader("Prescription")
        
        drug_names = sorted([drug['drug'] for drug in drugs_data])
        selected_drugs = st.multiselect("Select Drugs:", drug_names, key="manual_drugs", 
                                       help="Conflicts are checked automatically as you select drugs",
                                       max_selections=15)
        
        if len(selected_drugs) > 10:
            st.info("💡 Large prescriptions may take a moment to analyze. Results are cached for better performance.")
    
    st.divider()
    
    # Real-time conflict checking with caching
    if selected_drugs:
        with st.spinner("🔍 Analyzing prescription..." if len(selected_drugs) > 5 else None):
            # Build KB once and cache it
            if st.session_state.cached_kb is None:
                base_dir = Path(__file__).parent
                rules = load_rules(base_dir / "rules.csv")
                st.session_state.cached_kb = build_rules_kb(rules)
            
            # Use optimized cached conflict detection
            from utils import make_condition_tokens
            conditions_tokens = make_condition_tokens(
                selected_conditions,
                selected_allergies if selected_allergies != ["None"] else []
            )
            
            conflicts_list = get_conflicts_cached(
                selected_drugs,
                conditions_tokens,
                st.session_state.cached_kb
            )
            
            # Convert Conflict objects to dicts for display
            conflicts = [
                {
                    'type': c.rtype,
                    'item_a': c.item_a,
                    'item_b': c.item_b,
                    'severity': c.severity,
                    'recommendation': c.recommendation,
                    'score': c.score
                }
                for c in conflicts_list
            ]
        
        # Display real-time results
        st.subheader("🔍 Real-Time Conflict Analysis")
        
        # Summary metrics
        col_a, col_b, col_c, col_d = st.columns(4)
        
        with col_a:
            st.metric("Drugs Selected", len(selected_drugs))
        
        with col_b:
            if conflicts:
                st.metric("Conflicts Found", len(conflicts), delta=f"-{len(conflicts)}", delta_color="inverse")
            else:
                st.metric("Conflicts Found", 0, delta="✓ Safe", delta_color="normal")
        
        with col_c:
            major_count = sum(1 for c in conflicts if c['severity'] == 'Major')
            if major_count > 0:
                st.metric("Major", major_count, delta="Critical", delta_color="inverse")
            else:
                st.metric("Major", 0)
        
        with col_d:
            moderate_count = sum(1 for c in conflicts if c['severity'] == 'Moderate')
            if moderate_count > 0:
                st.metric("Moderate", moderate_count, delta="Warning", delta_color="inverse")
            else:
                st.metric("Moderate", 0)
        
        st.divider()
        
        # Display conflicts with color coding
        if conflicts:
            st.error(f"⚠️ {len(conflicts)} conflict(s) detected in current prescription!")
            
            # Sort conflicts by severity
            severity_order = {'Major': 3, 'Moderate': 2, 'Minor': 1}
            conflicts.sort(key=lambda x: severity_order.get(x['severity'], 0), reverse=True)
            
            for conflict in conflicts:
                severity_class = f"conflict-{conflict['severity'].lower()}"
                
                # Color-coded emoji based on severity
                severity_emoji = {
                    'Major': '🔴',
                    'Moderate': '🟡',
                    'Minor': '🟢'
                }
                
                with st.container():
                    st.markdown(f'<div class="{severity_class}">', unsafe_allow_html=True)
                    
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"### {severity_emoji.get(conflict['severity'], '⚠️')} {conflict['severity']} Severity")
                        st.write(f"**Type:** {conflict['type']}")
                        st.write(f"**Conflict:** {conflict['item_a']} ↔️ {conflict['item_b']}")
                        st.write(f"**Recommendation:** {conflict['recommendation']}")
                    
                    with col2:
                        st.metric("Risk Score", conflict['score'])
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    st.write("")  # Spacing
        else:
            st.success("✅ No conflicts detected! This prescription is safe for the patient.")
            
            # Show safe prescription summary
            with st.expander("📋 Prescription Summary", expanded=True):
                st.write(f"**Patient:** {patient_name}")
                st.write(f"**Conditions:** {', '.join(selected_conditions) if selected_conditions else 'None'}")
                allergy_display = [a for a in selected_allergies if a != "None"]
                st.write(f"**Allergies:** {', '.join(allergy_display) if allergy_display else 'None'}")
                st.write(f"**Prescribed Drugs:**")
                for drug in selected_drugs:
                    st.markdown(f"- 💊 {drug}")
        
        # Export Report Section
        st.divider()
        st.subheader("📄 Export Report")
        
        col_exp1, col_exp2 = st.columns(2)
        
        with col_exp1:
            if st.button("📕 Download PDF Report", use_container_width=True):
                try:
                    from report_generator import ReportGenerator
                    
                    generator = ReportGenerator()
                    pdf_bytes = generator.generate_report_bytes(
                        format_type='pdf',
                        patient_name=patient_name,
                        patient_id=f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        conditions=selected_conditions if selected_conditions else [],
                        allergies=[a for a in selected_allergies if a != "None"],
                        prescription=selected_drugs,
                        conflicts=conflicts
                    )
                    
                    filename = f"conflict_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    st.download_button(
                        label="💾 Save PDF",
                        data=pdf_bytes,
                        file_name=filename,
                        mime="application/pdf",
                        use_container_width=True
                    )
                    st.success("✅ PDF report generated!")
                    
                except ImportError:
                    st.error("📦 Please install reportlab: `pip install reportlab`")
                except Exception as e:
                    st.error(f"❌ Error generating PDF: {str(e)}")
        
        with col_exp2:
            if st.button("📘 Download Word Report", use_container_width=True):
                try:
                    from report_generator import ReportGenerator
                    
                    generator = ReportGenerator()
                    word_bytes = generator.generate_report_bytes(
                        format_type='word',
                        patient_name=patient_name,
                        patient_id=f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        conditions=selected_conditions if selected_conditions else [],
                        allergies=[a for a in selected_allergies if a != "None"],
                        prescription=selected_drugs,
                        conflicts=conflicts
                    )
                    
                    filename = f"conflict_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
                    st.download_button(
                        label="💾 Save Word",
                        data=word_bytes,
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )
                    st.success("✅ Word report generated!")
                    
                except ImportError:
                    st.error("📦 Please install python-docx: `pip install python-docx`")
                except Exception as e:
                    st.error(f"❌ Error generating Word report: {str(e)}")
    else:
        st.info("👆 Select drugs above to begin real-time conflict checking")

# ============= IMPORT DATA PAGE =============
elif page == "Import Data":
    st.header("📁 Import Custom Data")
    
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
