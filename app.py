import streamlit as st

# Configuration de la page Streamlit
st.set_page_config(page_title="F1 Analytics Dashboard", page_icon="🏎️")

st.title("🏎️ F1 Telemetry & Analytics Dashboard")
st.markdown("""
### Bienvenue sur l'application de monitoring F1

Cette application vous permet d'analyser les données de course de Formule 1 en utilisant l'API **FastF1**.

👈 **Utilisez le menu latéral** pour naviguer vers les différentes pages d'analyse :
""")

page_1 = st.Page("pages/1_Grand_Prix_Analysis.py", title="Grand Prix Analysis", icon="🏁")

pg = st.navigation([page_1])
pg.run()