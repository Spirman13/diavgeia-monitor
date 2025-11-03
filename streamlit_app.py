import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import requests
import json

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="Ενοποιημένο Dashboard - ΚΗΜΔΗΣ & Διαύγεια",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# ΚΗΜΔΗΣ API CONFIGURATION
# ============================================================================
KHMDHS_BASE_URL = "https://cerpp.eprocurement.gov.gr"

# ============================================================================
# DATA LOADING FUNCTIONS
# ============================================================================

@st.cache_data
def load_aaht_list():
    """Load AAHT list from Excel"""
    try:
        df = pd.read_excel('AAHTList.xlsx')
        return df
    except Exception as e:
        st.warning(f"⚠️ Δεν βρέθηκε το AAHTList.xlsx: {e}")
        return pd.DataFrame()

# ============================================================================
# ΚΗΜΔΗΣ API FUNCTIONS
# ============================================================================

def fetch_khmdhs_notices(filters):
    """Fetch active tenders from ΚΗΜΔΗΣ API"""
    url = f"{KHMDHS_BASE_URL}/khmdhs-opendata/notice"
    
    # Prepare request body
    payload = {
        "title": filters.get("title", ""),
        "cpvItems": filters.get("cpvItems", []),
        "organizations": filters.get("organizations", []),
        "contractType": filters.get("contractType", ""),
        "dateFrom": filters.get("dateFrom", ""),
        "dateTo": filters.get("dateTo", ""),
        "totalCostFrom": filters.get("totalCostFrom", 0),
        "totalCostTo": filters.get("totalCostTo", 0),
        "finalDateFrom": filters.get("finalDateFrom", ""),
        "finalDateTo": filters.get("finalDateTo", ""),
        "isModified": False
    }
    
    # Remove empty values
    payload = {k: v for k, v in payload.items() if v not in ["", [], None]}
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers={"Accept": "application/json"},
            params={"page": 0},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"❌ Σφάλμα API: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"❌ Σφάλμα σύνδεσης: {str(e)}")
        return None

def get_khmdhs_pdf_link(adam):
    """Generate PDF download link for ΚΗΜΔΗΣ tender"""
    return f"{KHMDHS_BASE_URL}/khmdhs-opendata/notice/attachment/{adam}"

# ============================================================================
# ΔΙΑΥΓΕΙΑ MOCK DATA GENERATOR
# ============================================================================

@st.cache_data(ttl=3600)
def generate_mock_diavgeia_data(days=30, count=50):
    """Generate realistic mock data για προκηρύξεις θέσεων"""
    
    # Τύποι προκηρύξεων
    announcement_types = [
        "Πλήρωση θέσεων μόνιμου προσωπικού",
        "Πλήρωση θέσεων ΙΔΑΧ",
        "Πλήρωση θέσεων με σύμβαση ορισμένου χρόνου",
        "Μετάταξη/Απόσπαση",
        "Πλήρωση διοικητικών θέσεων",
        "Προκήρυξη θέσεων ειδικών επιστημόνων"
    ]
    
    # Realistic φορείς
    organizations = [
        "Υπουργείο Υγείας",
        "Δήμος Αθηναίων",
        "Περιφέρεια Αττικής",
        "ΕΛΣΤΑΤ",
        "ΕΦΚΑ",
        "Γενικό Νοσοκομείο Αθηνών",
        "ΔΕΗ Α.Ε.",
        "ΕΥΔΑΠ",
        "Πανεπιστήμιο Αθηνών",
        "Δήμος Θεσσαλονίκης",
        "Υπουργείο Παιδείας",
        "ΟΑΕΔ"
    ]
    
    # Ειδικότητες
    specialties = [
        "Διοικητικών",
        "Τεχνικών",
        "Νοσηλευτικού Προσωπικού",
        "Ιατρών",
        "IT/Πληροφορικής",
        "Οικονομολόγων",
        "Νομικών",
        "Μηχανικών",
        "Διδακτικού Προσωπικού",
        "Βοηθητικού Προσωπικού"
    ]
    
    data = []
    for i in range(count):
        ann_type = random.choice(announcement_types)
        org = random.choice(organizations)
        specialty = random.choice(specialties)
        
        # Random dates
        days_ago = random.randint(0, days)
        pub_date = datetime.now() - timedelta(days=days_ago)
        deadline_days = random.randint(20, 60)
        deadline = pub_date + timedelta(days=deadline_days)
        
        # Number of positions
        positions = random.randint(1, 25)
        
        # ADA
        ada = f"{''.join([random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0-9Ω') for _ in range(6)])}"
        
        data.append({
            'ada': ada,
            'title': f"{ann_type} - {specialty} ({positions} θέσεις) - {org}",
            'type': ann_type,
            'organization': org,
            'specialty': specialty,
            'positions': positions,
            'published_date': pub_date,
            'deadline': deadline,
            'days_remaining': (deadline - datetime.now()).days,
            'status': 'Ενεργή' if deadline > datetime.now() else 'Έληξε',
            'link': f"https://diavgeia.gov.gr/doc/{ada}"
        })
    
    return pd.DataFrame(data)

# ============================================================================
# MAIN APP
# ============================================================================

# Header
st.title("🏛️ Ενοποιημένο Dashboard - ΚΗΜΔΗΣ & Διαύγεια")
st.markdown("Παρακολούθηση Διαγωνισμών & Προκηρύξεων Θέσεων")
st.markdown("---")

# Main Navigation
main_tab = st.radio(
    "Επιλέξτε Ενότητα:",
    ["🏛️ ΚΗΜΔΗΣ - Διαγωνισμοί", "👥 Διαύγεια - Προκηρύξεις Θέσεων"],
    horizontal=True
)

st.markdown("---")

# ============================================================================
# TAB 1: ΚΗΜΔΗΣ - ΔΙΑΓΩΝΙΣΜΟΙ
# ============================================================================

if main_tab == "🏛️ ΚΗΜΔΗΣ - Διαγωνισμοί":
    st.header("🔴 Ενεργοί Διαγωνισμοί από ΚΗΜΔΗΣ")
    
    # Sidebar Filters for ΚΗΜΔΗΣ
    with st.sidebar:
        st.subheader("🔍 Φίλτρα ΚΗΜΔΗΣ")
        
        title_filter = st.text_input("Τίτλος", placeholder="π.χ. Προμήθεια")
        
        contract_type_options = {
            "Όλα": "",
            "Υπηρεσίες": "9",
            "Έργα": "10",
            "Μελέτες": "12",
            "Προμήθειες": "13",
            "Τεχνικές Υπηρεσίες": "14"
        }
        contract_type = st.selectbox("Τύπος Σύμβασης", list(contract_type_options.keys()))
        
        col1, col2 = st.columns(2)
        with col1:
            date_from = st.date_input(
                "Καταχώρηση Από",
                value=datetime.now() - timedelta(days=30)
            )
        with col2:
            date_to = st.date_input("Καταχώρηση Έως", value=datetime.now())
        
        budget_from = st.number_input("Budget Από (€)", min_value=0, value=0, step=1000)
        budget_to = st.number_input("Budget Έως (€)", min_value=0, value=1000000, step=1000)
        
        search_btn = st.button("🔎 Αναζήτηση", type="primary", use_container_width=True)
        reset_btn = st.button("🔄 Καθαρισμός", use_container_width=True)
    
    # ΚΗΜΔΗΣ Tabs
    khmdhs_tab1, khmdhs_tab2, khmdhs_tab3, khmdhs_tab4 = st.tabs([
        "📋 Αποτελέσματα",
        "📊 Analytics",
        "🔔 Alerts",
        "📁 Data Explorer"
    ])
    
    # Handle search
    if search_btn:
        with st.spinner("⏳ Ανάκτηση δεδομένων από ΚΗΜΔΗΣ..."):
            filters = {
                "title": title_filter,
                "contractType": contract_type_options[contract_type],
                "dateFrom": date_from.strftime("%Y-%m-%d"),
                "dateTo": date_to.strftime("%Y-%m-%d"),
                "totalCostFrom": budget_from,
                "totalCostTo": budget_to
            }
            
            results = fetch_khmdhs_notices(filters)
            
            if results and results.get("content"):
                st.session_state['khmdhs_results'] = results
            else:
                st.warning("⚠️ Δεν βρέθηκαν αποτελέσματα")
    
    # Display results
    with khmdhs_tab1:
        if 'khmdhs_results' in st.session_state:
            results = st.session_state['khmdhs_results']
            content = results.get("content", [])
            
            st.success(f"✅ Βρέθηκαν {results.get('totalElements', 0)} διαγωνισμοί")
            
            if content:
                display_data = []
                for item in content:
                    display_data.append({
                        "ΑΔΑΜ": item.get("referenceNumber", "N/A"),
                        "Τίτλος": item.get("title", "N/A")[:60] + "...",
                        "Φορέας": item.get("organization", {}).get("value", "N/A")[:40],
                        "Τύπος": item.get("contractType", {}).get("value", "N/A"),
                        "Budget (€)": f"{item.get('totalCostWithoutVAT', 0):,.0f}",
                        "Καταληκτική": item.get("finalSubmissionDate", "N/A")[:10] if item.get("finalSubmissionDate") else "N/A",
                    })
                
                df = pd.DataFrame(display_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Export
                csv = df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    "📥 Εξαγωγή CSV",
                    csv,
                    f"khmdhs_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv"
                )
        else:
            st.info("ℹ️ Κάντε αναζήτηση για να δείτε αποτελέσματα")
    
    with khmdhs_tab2:
        if 'khmdhs_results' in st.session_state:
            results = st.session_state['khmdhs_results']
            content = results.get("content", [])
            
            if content:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Σύνολο", results.get('totalElements', 0))
                with col2:
                    total_budget = sum([item.get('totalCostWithoutVAT', 0) for item in content])
                    st.metric("Συνολικός Budget", f"€{total_budget:,.0f}")
                with col3:
                    avg = total_budget / len(content) if content else 0
                    st.metric("Μέσος Budget", f"€{avg:,.0f}")
                with col4:
                    types = [item.get("contractType", {}).get("value", "Άγνωστο") for item in content]
                    st.metric("Τύποι", len(set(types)))
                
                st.markdown("---")
                
                # Charts
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    st.markdown("#### Κατανομή ανά Τύπο")
                    type_counts = pd.Series(types).value_counts()
                    st.bar_chart(type_counts)
                
                with col_c2:
                    st.markdown("#### Budget ανά Τύπο")
                    budget_df = pd.DataFrame([
                        {"Τύπος": item.get("contractType", {}).get("value", "Άγνωστο"),
                         "Budget": item.get('totalCostWithoutVAT', 0)}
                        for item in content
                    ])
                    st.bar_chart(budget_df.set_index("Τύπος"))
        else:
            st.info("ℹ️ Κάντε αναζήτηση για analytics")
    
    with khmdhs_tab3:
        if 'khmdhs_results' in st.session_state:
            results = st.session_state['khmdhs_results']
            content = results.get("content", [])
            
            urgent = []
            for item in content:
                deadline_str = item.get("finalSubmissionDate", "")
                if deadline_str:
                    try:
                        deadline = datetime.fromisoformat(deadline_str.replace("Z", "+00:00"))
                        days_left = (deadline - datetime.now()).days
                        if 0 <= days_left <= 7:
                            urgent.append({
                                "ΑΔΑΜ": item.get("referenceNumber"),
                                "Τίτλος": item.get("title")[:50],
                                "Καταληκτική": deadline_str[:10],
                                "Μέρες": days_left
                            })
                    except:
                        pass
            
            if urgent:
                st.warning(f"⚠️ {len(urgent)} επείγοντες διαγωνισμοί")
                st.dataframe(pd.DataFrame(urgent), use_container_width=True, hide_index=True)
            else:
                st.success("✅ Δεν υπάρχουν επείγοντες")
        else:
            st.info("ℹ️ Κάντε αναζήτηση")
    
    with khmdhs_tab4:
        if 'khmdhs_results' in st.session_state:
            results = st.session_state['khmdhs_results']
            with st.expander("🔍 Raw JSON"):
                st.json(results)
            
            content = results.get("content", [])
            if content:
                df_full = pd.json_normalize(content)
                st.dataframe(df_full, use_container_width=True)
        else:
            st.info("ℹ️ Κάντε αναζήτηση")

# ============================================================================
# TAB 2: ΔΙΑΥΓΕΙΑ - ΠΡΟΚΗΡΥΞΕΙΣ ΘΕΣΕΩΝ
# ============================================================================

elif main_tab == "👥 Διαύγεια - Προκηρύξεις Θέσεων":
    st.header("📋 Προκηρύξεις Πλήρωσης Θέσεων")
    
    # Load data
    df = generate_mock_diavgeia_data(days=30, count=100)
    
    # Sidebar Filters for Διαύγεια
    with st.sidebar:
        st.subheader("🔍 Φίλτρα Διαύγεια")
        
        # Type filter
        types = ["Όλες"] + sorted(df['type'].unique().tolist())
        selected_type = st.selectbox("Τύπος Προκήρυξης", types)
        
        # Specialty filter
        specialties = ["Όλες"] + sorted(df['specialty'].unique().tolist())
        selected_specialty = st.selectbox("Ειδικότητα", specialties)
        
        # Organization filter
        orgs = ["Όλοι"] + sorted(df['organization'].unique().tolist())
        selected_org = st.selectbox("Φορέας", orgs)
        
        # Status filter
        status_filter = st.radio("Κατάσταση", ["Όλες", "Ενεργές", "Έληξαν"])
        
        # Date range
        date_range = st.slider(
            "Ημερομηνίες Δημοσίευσης",
            min_value=-30,
            max_value=0,
            value=(-30, 0),
            format="%d ημέρες"
        )
        
        # Positions slider
        pos_range = st.slider(
            "Αριθμός Θέσεων",
            min_value=int(df['positions'].min()),
            max_value=int(df['positions'].max()),
            value=(int(df['positions'].min()), int(df['positions'].max()))
        )
    
    # Apply filters
    filtered_df = df.copy()
    
    if selected_type != "Όλες":
        filtered_df = filtered_df[filtered_df['type'] == selected_type]
    
    if selected_specialty != "Όλες":
        filtered_df = filtered_df[filtered_df['specialty'] == selected_specialty]
    
    if selected_org != "Όλοι":
        filtered_df = filtered_df[filtered_df['organization'] == selected_org]
    
    if status_filter == "Ενεργές":
        filtered_df = filtered_df[filtered_df['status'] == 'Ενεργή']
    elif status_filter == "Έληξαν":
        filtered_df = filtered_df[filtered_df['status'] == 'Έληξε']
    
    filtered_df = filtered_df[
        (filtered_df['positions'] >= pos_range[0]) &
        (filtered_df['positions'] <= pos_range[1])
    ]
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📋 Σύνολο", len(filtered_df))
    
    with col2:
        active = len(filtered_df[filtered_df['status'] == 'Ενεργή'])
        st.metric("✅ Ενεργές", active)
    
    with col3:
        urgent = len(filtered_df[
            (filtered_df['status'] == 'Ενεργή') & 
            (filtered_df['days_remaining'] <= 7)
        ])
        st.metric("🔥 Επείγουσες", urgent, delta="≤7 ημέρες")
    
    with col4:
        total_positions = filtered_df['positions'].sum()
        st.metric("👥 Σύνολο Θέσεων", total_positions)
    
    st.markdown("---")
    
    # Διαύγεια Tabs
    diav_tab1, diav_tab2, diav_tab3, diav_tab4 = st.tabs([
        "📋 Προκηρύξεις",
        "📊 Analytics",
        "🔔 Alerts",
        "ℹ️ Info"
    ])
    
    with diav_tab1:
        st.markdown(f"### Βρέθηκαν {len(filtered_df)} προκηρύξεις")
        
        # Sort options
        sort_col, sort_order = st.columns([3, 1])
        with sort_col:
            sort_by = st.selectbox("Ταξινόμηση", ["Καταληκτική", "Θέσεις", "Ημ/νία Δημοσίευσης"])
        with sort_order:
            ascending = st.checkbox("Αύξουσα", value=False)
        
        # Sort
        sort_map = {
            "Καταληκτική": "deadline",
            "Θέσεις": "positions",
            "Ημ/νία Δημοσίευσης": "published_date"
        }
        filtered_df = filtered_df.sort_values(sort_map[sort_by], ascending=ascending)
        
        # Display cards
        for _, row in filtered_df.iterrows():
            # Color coding
            if row['status'] == 'Έληξε':
                border_color = "#ff4444"
                emoji = "❌"
            elif row['days_remaining'] <= 7:
                border_color = "#ff6600"
                emoji = "🔥"
            elif row['days_remaining'] <= 14:
                border_color = "#ffaa00"
                emoji = "⚠️"
            else:
                border_color = "#00aa00"
                emoji = "✅"
            
            with st.container():
                st.markdown(
                    f"""
                    <div style="border-left: 5px solid {border_color}; padding: 15px; 
                                margin: 10px 0; background: #f8f9fa; border-radius: 5px;">
                        <h4>{emoji} {row['title']}</h4>
                        <p><strong>📅 Δημοσίευση:</strong> {row['published_date'].strftime('%d/%m/%Y')} | 
                           <strong>⏰ Καταληκτική:</strong> {row['deadline'].strftime('%d/%m/%Y')} | 
                           <strong>⏳ Υπόλοιπες:</strong> {row['days_remaining']} ημέρες</p>
                        <p><strong>🏛️ Φορέας:</strong> {row['organization']} | 
                           <strong>👥 Θέσεις:</strong> {row['positions']} | 
                           <strong>📌 Κατάσταση:</strong> {row['status']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                col_btn1, col_btn2, col_btn3 = st.columns([2, 2, 6])
                with col_btn1:
                    st.link_button("🔗 Διαύγεια", row['link'])
                with col_btn2:
                    st.button(f"📋 ADA: {row['ada']}", key=f"ada_{row['ada']}")
    
    with diav_tab2:
        st.markdown("### 📊 Analytics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Προκηρύξεις ανά Τύπο")
            type_counts = filtered_df['type'].value_counts()
            fig1 = px.bar(
                x=type_counts.values,
                y=type_counts.index,
                orientation='h',
                labels={'x': 'Αριθμός', 'y': 'Τύπος'}
            )
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            st.markdown("#### Θέσεις ανά Ειδικότητα")
            spec_positions = filtered_df.groupby('specialty')['positions'].sum().sort_values(ascending=False)
            fig2 = px.bar(
                x=spec_positions.values,
                y=spec_positions.index,
                orientation='h',
                labels={'x': 'Θέσεις', 'y': 'Ειδικότητα'}
            )
            st.plotly_chart(fig2, use_container_width=True)
        
        col3, col4 = st.columns(2)
        
        with col3:
            st.markdown("#### Timeline Καταληκτικών (Ενεργές)")
            active_df = filtered_df[filtered_df['status'] == 'Ενεργή']
            if not active_df.empty:
                fig3 = px.scatter(
                    active_df,
                    x='deadline',
                    y='positions',
                    color='specialty',
                    size='positions',
                    hover_data=['organization', 'type'],
                    labels={'deadline': 'Καταληκτική', 'positions': 'Θέσεις'}
                )
                st.plotly_chart(fig3, use_container_width=True)
        
        with col4:
            st.markdown("#### Top 10 Φορείς")
            org_counts = filtered_df['organization'].value_counts().head(10)
            fig4 = px.pie(
                values=org_counts.values,
                names=org_counts.index,
                hole=0.4
            )
            st.plotly_chart(fig4, use_container_width=True)
    
    with diav_tab3:
        st.markdown("### 🔔 Επείγουσες Προκηρύξεις")
        
        urgent_df = filtered_df[
            (filtered_df['status'] == 'Ενεργή') & 
            (filtered_df['days_remaining'] <= 7)
        ].sort_values('days_remaining')
        
        if not urgent_df.empty:
            st.warning(f"⚠️ {len(urgent_df)} επείγουσες προκηρύξεις (λήγουν σε ≤7 ημέρες)")
            
            for _, row in urgent_df.iterrows():
                st.error(
                    f"🔥 **{row['title']}**\n\n"
                    f"⏰ Λήγει σε **{row['days_remaining']} ημέρες** ({row['deadline'].strftime('%d/%m/%Y')})"
                )
        else:
            st.success("✅ Δεν υπάρχουν επείγουσες προκηρύξεις")
    
    with diav_tab4:
        st.markdown("### ℹ️ Πληροφορίες")
        
        st.info("""
        **Σχετικά με το Dashboard:**
        
        - 📊 Παρακολούθηση προκηρύξεων πλήρωσης θέσεων από Διαύγεια
        - 🔍 Smart filters για γρήγορη αναζήτηση
        - 🔔 Alerts για επείγουσες προκηρύξεις
        - 📈 Analytics & visualizations
        
        **Επαναλαμβανόμενες Υπηρεσίες (18 κατηγορίες):**
        - Καθαρισμός, Φύλαξη, Τεχνική Συντήρηση
        - IT/Software, Logistics, Τηλεπικοινωνίες
        - Λογιστικές, Νομικές, Εκπαίδευση
        - Πυρασφάλεια, Εσωτερικός Έλεγχος, DPO
        - Ιατρός Εργασίας, και άλλα
        
        **Νομοθεσία:**
        - Ν. 4412/2016 (Δημόσιες Συμβάσεις)
        - Ν. 2518/1997 (Ιδιωτική Ασφάλεια)
        - Ν. 3850/2010 (ΥΑΕ)
        - Ν. 4795/2021 (Εσωτερικός Έλεγχος)
        - GDPR (EU 2016/679)
        """)
        
        # AAHT Info
        aaht_df = load_aaht_list()
        if not aaht_df.empty:
            st.success(f"✅ Φορτώθηκαν {len(aaht_df):,} φορείς από AAHT")

# Footer
st.markdown("---")
st.caption(f"📊 Ενοποιημένο Dashboard v1.0 | Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
st.caption("🔗 ΚΗΜΔΗΣ: https://cerpp.eprocurement.gov.gr | Διαύγεια: https://diavgeia.gov.gr")
