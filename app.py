import streamlit as st
import fastf1
import fastf1.plotting
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os  # <--- NOUVEL IMPORT NÉCESSAIRE

# Configuration de la page Streamlit
st.set_page_config(page_title="F1 Analytics Dashboard", layout="wide")

# Configuration de FastF1 pour les graphiques
fastf1.plotting.setup_mpl(misc_mpl_mods=False)

# --- CORRECTION DU CACHE ---
cache_dir = 'f1_cache'

# On vérifie si le dossier existe, sinon on le crée
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)

fastf1.Cache.enable_cache(cache_dir) 
# ---------------------------

# ... Le reste du code reste identique ...
# --- TITRE ---
st.title("🏎️ F1 Telemetry & Analytics Dashboard")
st.markdown("Analyse des données de course via l'API **FastF1**.")

# --- SIDEBAR: SÉLECTION ---
st.sidebar.header("Paramètres de la Session")

year = st.sidebar.selectbox("Année", [2025, 2024, 2023, 2022, 2021], index=0)

# Récupération dynamique du calendrier
try:
    schedule = fastf1.get_event_schedule(year)
    # On filtre pour ne garder que les courses passées ou officielles
    event_names = schedule['EventName'].unique().tolist()
    grand_prix = st.sidebar.selectbox("Grand Prix", event_names)
    
    session_type = st.sidebar.selectbox("Session", ["R", "Q", "FP1", "FP2", "FP3", "SS"], index=0)
    st.sidebar.info("R=Race, Q=Qualif, FP=Essais, SS=Sprint")

except Exception as e:
    st.error(f"Erreur lors du chargement du calendrier: {e}")
    st.stop()

# --- CHARGEMENT DES DONNÉES ---
@st.cache_data
def load_data(year, gp, session_type):
    try:
        session = fastf1.get_session(year, gp, session_type)
        session.load()
        return session
    except Exception as e:
        return None

if st.sidebar.button("Charger les données"):
    with st.spinner('Téléchargement des données de télémétrie en cours...'):
        session = load_data(year, grand_prix, session_type)
        
    if session is None:
        st.error("Impossible de charger la session. Vérifiez que la course a bien eu lieu.")
    else:
        st.success(f"Données chargées pour {grand_prix} {year} - {session_type}")
        
        # --- TABS (ONGLÉS) ---
        tab1, tab2, tab3 = st.tabs(["🏆 Résultats", "⏱️ Analyse des Tours", "📈 Comparaison Télémétrie"])

        # --- TAB 1: RÉSULTATS ---
        with tab1:
            st.subheader(f"Résultats de la session - {session.event['EventName']}")
            results = session.results[['ClassifiedPosition', 'Abbreviation', 'TeamName', 'GridPosition', 'Time', 'Points']]
            st.dataframe(results, use_container_width=True)

        # --- TAB 2: ANALYSE DES TOURS ---
        with tab2:
            st.subheader("Distribution des temps au tour (Rythme de course)")
            
            # Filtrer les tours rapides (exclure les tours de sortie/entrée et les tours très lents)
            laps = session.laps.pick_quicklaps()

            # Conversion du temps au tour (Timedelta) en secondes (float) pour le graphique
            laps['LapTimeSeconds'] = laps['LapTime'].dt.total_seconds()
            
            # Sélectionner les Top 10 pilotes pour la lisibilité
            top_10_drivers = session.results['Abbreviation'][:10].tolist()
            laps_top_10 = laps[laps['Driver'].isin(top_10_drivers)]
            
            # Création du Boxplot avec Seaborn
            fig_laps, ax_laps = plt.subplots(figsize=(10, 6))
            
            # Utilisation d'une palette de couleurs officielle F1 si possible, sinon standard
            sns.boxplot(data=laps_top_10, x="Driver", y="LapTimeSeconds", ax=ax_laps, palette="turbo")
            sns.swarmplot(data=laps_top_10, x="Driver", y="LapTimeSeconds", color=".25", size=2, ax=ax_laps)
            
            ax_laps.set_title("Régularité des 10 premiers pilotes")
            ax_laps.set_ylabel("Temps au tour (secondes)")
            ax_laps.invert_yaxis() # En F1, plus bas est mieux, mais pour un boxplot on garde l'échelle standard ou inversée selon préférence
            
            st.pyplot(fig_laps)
            st.markdown("*Le graphique ci-dessus montre la dispersion des temps. Une boîte 'courte' indique une grande régularité.*")

else:
    st.info("Veuillez sélectionner une course et cliquer sur 'Charger les données' dans la barre latérale.")