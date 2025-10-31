import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random

# Page config
st.set_page_config(
    page_title="Διαύγεια Monitor - Επαναλαμβανόμενες Συμβάσεις",
    page_icon="📊",
    layout="wide"
)

# Load AAHT List
@st.cache_data
def load_aaht_list():
    try:
        df = pd.read_excel('/mnt/project/AAHTList.xlsx')
        return df
    except:
        return pd.DataFrame()

# Mock Diavgeia Data Generator
@st.cache_data(ttl=3600)  # Cache for 1 hour
def generate_mock_diavgeia_data(days=30, count=50):
    """
    Generate realistic mock data για επαναλαμβανόμενες συμβάσεις
    """
    
    # Υπηρεσίες από το PDF
    services = [
        "Καθαρισμός χώρων",
        "Φύλαξη (Security)",
        "Τεχνική Συντήρηση",
        "Συντήρηση Υποδομών (Η/Μ)",
        "Προμήθεια Αναλωσίμων",
        "Υπηρεσίες Logistics",
        "Συντήρηση Η/Υ & Λογισμικού",
        "Απολύμανση/Μυοκτονία",
        "Τηλεπικοινωνίες/Internet",
        "Μεταφορά Προσωπικού",
        "Λογιστικές Υπηρεσίες",
        "Ασφάλιση",
        "Εκπαίδευση Προσωπικού",
        "Νομικές Υπηρεσίες",
        "Πυρασφάλεια",
        "Εσωτερικός Έλεγχος",
        "Υπεύθυνος Προστασίας Δεδομένων (DPO)",
        "Ιατρός Εργασίας/Τεχνικός Ασφαλείας"
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
    
    # Generate data
    data = []
    for i in range(count):
        service = random.choice(services)
        org = random.choice(organizations)
        
        # Random date in last X days
        days_ago = random.randint(0, days)
        pub_date = datetime.now() - timedelta(days=days_ago)
        
        # Deadline (random 20-60 days from publication)
        deadline_days = random.randint(20, 60)
        deadline = pub_date + timedelta(days=deadline_days)
        
        # Budget (realistic ranges per service type)
        if "Καθαρισμός" in service or "Φύλαξη" in service:
            budget = random.randint(50000, 500000)
        elif "Συντήρηση" in service:
            budget = random.randint(30000, 300000)
        elif "Λογιστικές" in service or "Νομικές" in service:
            budget = random.randint(10000, 100000)
        else:
            budget = random.randint(15000, 200000)
        
        # ADA (realistic format)
        ada = f"{''.join([random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0-9Ω') for _ in range(6)])}"
        
        data.append({
            'ada': ada,
            'title': f"Ανοικτός Διαγωνισμός για {service} - {org}",
            'service': service,
            'organization': org,
            'publish_date': pub_date.strftime('%Y-%m-%d'),
            'deadline': deadline.strftime('%Y-%m-%d'),
            'budget': budget,
            'status': 'Ενεργή' if deadline > datetime.now() else 'Έληξε',
            'link': f"https://diavgeia.gov.gr/decision/view/{ada}"
        })
    
    df = pd.DataFrame(data)
    df['days_remaining'] = (pd.to_datetime(df['deadline']) - datetime.now()).dt.days
    return df

# Sidebar
st.sidebar.title("🔍 Φίλτρα Αναζήτησης")

# Load data
aaht_df = load_aaht_list()
diavgeia_df = generate_mock_diavgeia_data(days=30, count=100)

# Filters
st.sidebar.subheader("Υπηρεσία")
all_services = ["Όλες"] + sorted(diavgeia_df['service'].unique().tolist())
selected_service = st.sidebar.selectbox("Επιλέξτε υπηρεσία:", all_services)

st.sidebar.subheader("Κατάσταση")
status_filter = st.sidebar.radio("Εμφάνιση:", ["Όλες", "Μόνο Ενεργές", "Μόνο Ληγμένες"])

st.sidebar.subheader("Ημερομηνίες")
date_range = st.sidebar.slider(
    "Ημέρες καταληκτικής:",
    min_value=-30,
    max_value=60,
    value=(-30, 60),
    help="Αρνητικές τιμές = ληγμένες, θετικές = μελλοντικές"
)

st.sidebar.subheader("Προϋπολογισμός")
min_budget, max_budget = st.sidebar.slider(
    "Εύρος προϋπολογισμού (€):",
    min_value=0,
    max_value=int(diavgeia_df['budget'].max()),
    value=(0, int(diavgeia_df['budget'].max())),
    step=10000
)

# Apply filters
filtered_df = diavgeia_df.copy()

if selected_service != "Όλες":
    filtered_df = filtered_df[filtered_df['service'] == selected_service]

if status_filter == "Μόνο Ενεργές":
    filtered_df = filtered_df[filtered_df['status'] == 'Ενεργή']
elif status_filter == "Μόνο Ληγμένες":
    filtered_df = filtered_df[filtered_df['status'] == 'Έληξε']

filtered_df = filtered_df[
    (filtered_df['days_remaining'] >= date_range[0]) & 
    (filtered_df['days_remaining'] <= date_range[1])
]

filtered_df = filtered_df[
    (filtered_df['budget'] >= min_budget) & 
    (filtered_df['budget'] <= max_budget)
]

# Main content
st.title("📊 Διαύγεια Monitor - Επαναλαμβανόμενες Συμβάσεις")
st.markdown("### Παρακολούθηση Διαγωνισμών για Υπηρεσίες Υποστήριξης")

# Warning banner
st.info("⚠️ **DEMO MODE**: Αυτά είναι mock data. Σε production θα συνδεθούμε live με το Διαύγεια API.")

# Metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "📋 Σύνολο Διαγωνισμών",
        len(filtered_df),
        delta=f"{len(filtered_df) - len(diavgeia_df)} από φίλτρα"
    )

with col2:
    active_count = len(filtered_df[filtered_df['status'] == 'Ενεργή'])
    st.metric(
        "✅ Ενεργοί",
        active_count,
        delta=f"{active_count}/{len(filtered_df)}"
    )

with col3:
    urgent = len(filtered_df[filtered_df['days_remaining'].between(0, 7)])
    st.metric(
        "🔥 Επείγοντα (7 ημέρες)",
        urgent,
        delta="Προσοχή!" if urgent > 0 else None
    )

with col4:
    total_budget = filtered_df['budget'].sum()
    st.metric(
        "💰 Συνολικός Προϋπ/σμός",
        f"€{total_budget:,.0f}"
    )

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📋 Διαγωνισμοί", "📊 Analytics", "🔔 Alerts", "ℹ️ Info"])

with tab1:
    st.subheader(f"Βρέθηκαν {len(filtered_df)} διαγωνισμοί")
    
    # Sort options
    sort_col1, sort_col2 = st.columns([3, 1])
    with sort_col1:
        sort_by = st.selectbox(
            "Ταξινόμηση κατά:",
            ["Καταληκτική (Επείγοντα πρώτα)", "Προϋπολογισμός (Μεγαλύτερα πρώτα)", "Ημ/νία Δημοσίευσης"]
        )
    
    # Sort dataframe
    if sort_by == "Καταληκτική (Επείγοντα πρώτα)":
        display_df = filtered_df.sort_values('days_remaining', ascending=True)
    elif sort_by == "Προϋπολογισμός (Μεγαλύτερα πρώτα)":
        display_df = filtered_df.sort_values('budget', ascending=False)
    else:
        display_df = filtered_df.sort_values('publish_date', ascending=False)
    
    # Display as cards
    for idx, row in display_df.iterrows():
        with st.container():
            # Color coding based on urgency
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
            
            st.markdown(f"""
            <div style="border-left: 5px solid {border_color}; padding: 15px; margin: 10px 0; background-color: #f8f9fa; border-radius: 5px;">
                <h4>{emoji} {row['title']}</h4>
                <p><strong>ADA:</strong> {row['ada']} | <strong>Φορέας:</strong> {row['organization']}</p>
                <p><strong>Υπηρεσία:</strong> {row['service']}</p>
                <p><strong>Προϋπολογισμός:</strong> €{row['budget']:,} | <strong>Δημοσίευση:</strong> {row['publish_date']} | <strong>Καταληκτική:</strong> {row['deadline']}</p>
                <p><strong>Υπόλοιπες ημέρες:</strong> {row['days_remaining']} | <strong>Κατάσταση:</strong> {row['status']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            col_a, col_b = st.columns([4, 1])
            with col_b:
                st.link_button("🔗 Άνοιγμα στο Διαύγεια", row['link'])
            
            st.divider()

with tab2:
    st.subheader("📊 Στατιστικά & Visualizations")
    
    # Chart 1: Διαγωνισμοί ανά υπηρεσία
    st.markdown("#### Κατανομή Διαγωνισμών ανά Υπηρεσία")
    service_counts = filtered_df['service'].value_counts().reset_index()
    service_counts.columns = ['Υπηρεσία', 'Αριθμός']
    
    fig1 = px.bar(
        service_counts,
        x='Αριθμός',
        y='Υπηρεσία',
        orientation='h',
        title='Διαγωνισμοί ανά Τύπο Υπηρεσίας'
    )
    st.plotly_chart(fig1, use_container_width=True)
    
    # Chart 2: Budget distribution
    st.markdown("#### Κατανομή Προϋπολογισμού")
    fig2 = px.histogram(
        filtered_df,
        x='budget',
        nbins=20,
        title='Κατανομή Προϋπολογισμών',
        labels={'budget': 'Προϋπολογισμός (€)'}
    )
    st.plotly_chart(fig2, use_container_width=True)
    
    # Chart 3: Timeline
    st.markdown("#### Timeline Καταληκτικών")
    timeline_df = filtered_df[filtered_df['status'] == 'Ενεργή'].sort_values('deadline')
    
    fig3 = px.scatter(
        timeline_df,
        x='deadline',
        y='service',
        size='budget',
        color='days_remaining',
        hover_data=['title', 'organization', 'budget'],
        title='Timeline Ενεργών Διαγωνισμών',
        labels={'deadline': 'Καταληκτική', 'service': 'Υπηρεσία'}
    )
    st.plotly_chart(fig3, use_container_width=True)
    
    # Chart 4: Φορείς
    st.markdown("#### Top 10 Φορείς με Περισσότερους Διαγωνισμούς")
    org_counts = filtered_df['organization'].value_counts().head(10).reset_index()
    org_counts.columns = ['Φορέας', 'Διαγωνισμοί']
    
    fig4 = px.pie(
        org_counts,
        values='Διαγωνισμοί',
        names='Φορέας',
        title='Κατανομή ανά Φορέα'
    )
    st.plotly_chart(fig4, use_container_width=True)

with tab3:
    st.subheader("🔔 Ειδοποιήσεις & Alerts")
    
    # Urgent tenders
    urgent_df = filtered_df[
        (filtered_df['status'] == 'Ενεργή') & 
        (filtered_df['days_remaining'] <= 7)
    ].sort_values('days_remaining')
    
    if len(urgent_df) > 0:
        st.error(f"🚨 **{len(urgent_df)} Επείγοντες Διαγωνισμοί** (λήγουν σε ≤7 ημέρες)")
        
        for idx, row in urgent_df.iterrows():
            st.warning(f"""
            **{row['title']}**  
            📅 Λήγει σε: **{row['days_remaining']} ημέρες** ({row['deadline']})  
            💰 Προϋπολογισμός: €{row['budget']:,}  
            🏛️ Φορέας: {row['organization']}  
            [🔗 Δες στο Διαύγεια]({row['link']})
            """)
    else:
        st.success("✅ Δεν υπάρχουν επείγοντες διαγωνισμοί αυτή τη στιγμή!")
    
    st.divider()
    
    # Coming soon
    st.markdown("#### 📧 Email Alerts (Coming Soon)")
    st.info("""
    Σύντομα θα μπορείτε να:
    - Ορίσετε email notifications για νέους διαγωνισμούς
    - Λαμβάνετε alerts για επικείμενες καταληκτικές
    - Custom filters για τις υπηρεσίες που σας ενδιαφέρουν
    """)

with tab4:
    st.subheader("ℹ️ Πληροφορίες & Οδηγίες")
    
    st.markdown("""
    ### 🎯 Τι κάνει αυτό το site;
    
    Το **Διαύγεια Monitor** παρακολουθεί αυτόματα το πρόγραμμα Διαύγεια για **επαναλαμβανόμενες συμβάσεις** 
    που αφορούν υπηρεσίες υποστήριξης (καθαριότητα, φύλαξη, συντήρηση, κτλ.).
    
    ### 📋 Τι μπορείτε να κάνετε:
    
    1. **Αναζήτηση** διαγωνισμών με φίλτρα (υπηρεσία, προϋπολογισμός, ημερομηνίες)
    2. **Παρακολούθηση** καταληκτικών και alerts για επείγοντα
    3. **Ανάλυση** στατιστικών και τάσεων
    4. **Export** δεδομένων για περαιτέρω επεξεργασία
    
    ### 🔧 Τεχνολογία:
    
    - **Data Source**: Διαύγεια API (gov.gr)
    - **Frontend**: Streamlit
    - **Updates**: Αυτόματα κάθε 6 ώρες
    
    ### 📚 Υπηρεσίες που παρακολουθούνται:
    
    Βασισμένο στο PDF "Επαναλαμβανόμενες Συμβάσεις", παρακολουθούμε:
    
    - Καθαρισμός χώρων (Ν. 4412/2016)
    - Φύλαξη/Security (Ν. 2518/1997, Ν. 4412/2016)
    - Τεχνική Συντήρηση (εξοπλισμού, εγκαταστάσεων)
    - Συντήρηση Υποδομών (Η/Μ έργα, κτίρια)
    - Προμήθεια Αναλωσίμων
    - Υπηρεσίες Logistics
    - Συντήρηση Η/Υ & Λογισμικού
    - Απολύμανση/Μυοκτονία
    - Τηλεπικοινωνίες/Internet
    - Μεταφορές (προσωπικού, αγαθών)
    - Λογιστικές/Φοροτεχνικές
    - Ασφαλίσεις
    - Εκπαίδευση Προσωπικού
    - Νομικές Υπηρεσίες
    - Πυρασφάλεια
    - Εσωτερικός Έλεγχος
    - DPO (GDPR Compliance)
    - Ιατρός Εργασίας/Τεχνικός Ασφαλείας
    
    ### 📊 ΑΑΗΤ Database:
    
    Έχουμε φορτώσει **{:,} φορείς** από το ΑΑΗΤ για cross-reference.
    
    ---
    
    **Version**: 0.1 (Prototype)  
    **Status**: 🟡 Demo Mode (Mock Data)  
    **Next**: Production deployment με live API
    """.format(len(aaht_df) if not aaht_df.empty else 0))

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; padding: 20px;">
    <p>💡 <strong>Tip:</strong> Χρησιμοποιήστε τα φίλτρα στην αριστερή πλευρά για να βρείτε τους διαγωνισμούς που σας ενδιαφέρουν</p>
    <p>📧 Για ερωτήσεις ή προτάσεις, επικοινωνήστε μαζί μας</p>
</div>
""", unsafe_allow_html=True)
