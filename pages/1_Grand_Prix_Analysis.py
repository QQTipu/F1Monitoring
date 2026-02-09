import streamlit as st
import fastf1
import fastf1.plotting
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="F1 Telemetry Hub",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration du cache pour FastF1 (Essentiel pour la performance)
# Crée un dossier 'cache' localement s'il n'existe pas
cache_dir = 'cache'
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)

fastf1.Cache.enable_cache(cache_dir) 

# --- FONCTIONS DE CHARGEMENT DE DONNÉES ---

@st.cache_data
def load_session_data(year, gp, session_type):
    """Charge la session F1 spécifiée."""
    try:
        session = fastf1.get_session(year, gp, session_type)
        session.load()
        return session
    except Exception as e:
        st.error(f"Erreur lors du chargement des données: {e}")
        return None

def get_driver_color(driver_abr, session):
    """Récupère la couleur de l'écurie ou une couleur par défaut."""
    try:
        style = fastf1.plotting.get_driver_style(identifier=driver_abr, style=['color'], session=session)
        return style['color']
    except:
        return "#FFFFFF"

# --- INTERFACE UTILISATEUR ---

# Sidebar
with st.sidebar:
    st.title("🏎️ F1 Telemetry Hub")
    st.markdown("---")
    
    st.subheader("Sélection de l'Épreuve")
    # Par défaut, on met une course récente intéressante
    year = st.selectbox("Saison", [2025, 2024, 2023], index=1)
    
    # Liste simplifiée des GP (FastF1 peut gérer les noms approximatifs)
    gp_list = ["Bahrain", "Saudi Arabia", "Australia", "Japan", "China", "Miami", "Imola", "Monaco", "Canada", "Spain", "Austria", "Great Britain", "Hungary", "Belgium", "Netherlands", "Italy", "Azerbaijan", "Singapore", "USA", "Mexico", "Brazil", "Las Vegas", "Qatar", "Abu Dhabi"]
    gp = st.selectbox("Grand Prix", gp_list, index=15) # Italy par défaut pour l'exemple
    
    session_type = st.selectbox("Session", ["FP1", "FP2", "FP3", "Q", "R"], index=4) # Course par défaut
    
    load_btn = st.button("Charger les Données", type="primary")
    
    st.info("Note : Le premier chargement d'une session peut prendre 30-60 secondes (téléchargement des données).")

# --- LOGIQUE PRINCIPALE ---

if load_btn or 'session_loaded' not in st.session_state:
    if load_btn:
        with st.spinner(f"Chargement des données pour {gp} {year} ({session_type})..."):
            session = load_session_data(year, gp, session_type)
            if session:
                st.session_state['session'] = session
                st.session_state['session_loaded'] = True
    else:
        st.markdown("### 👋 Bienvenue sur le Dashboard F1")
        st.markdown("Veuillez sélectionner une course et cliquer sur **'Charger les Données'** dans la barre latérale.")

if 'session_loaded' in st.session_state and st.session_state['session_loaded']:
    session = st.session_state['session']
    
    # Titre dynamique
    st.header(f"{session.event['EventName']} {year} - {session_type}")
    
    # Onglets
    tab1, tab2, tab3 = st.tabs(["Vue d'ensemble", "Performance & Télémétrie", "Analyse de Course"])
    
    # --- ONGLET 1 : VUE D'ENSEMBLE ---
    with tab1:
        col1, col2, col3, col4 = st.columns(4)
        
        # Récupération du vainqueur (si c'est une course)
        results = session.results
        winner = results.iloc[0]
        fastest_lap_info = session.laps.pick_fastest()
        
        with col1:
            st.metric("Vainqueur / P1", f"{winner['Abbreviation']}", f"{winner['TeamName']}")
        with col2:
            st.metric("Meilleur Tour", f"{fastest_lap_info['Driver']}", f"{str(fastest_lap_info['LapTime']).split('days')[-1][:-3]}")
        with col3:
            st.metric("Temp. Piste", f"{session.weather_data['TrackTemp'].mean():.1f} °C")
        with col4:
            st.metric("Temp. Air", f"{session.weather_data['AirTemp'].mean():.1f} °C")

        st.markdown("### 🏆 Classement de la Session")
        
        # Préparation du tableau propre
        display_results = results[['Position', 'Abbreviation', 'TeamName', 'GridPosition', 'Time', 'Status']].copy()
        display_results['Time'] = display_results['Time'].astype(str).map(lambda x: x.split('days')[-1] if pd.notnull(x) else "N/A")
        st.dataframe(display_results, use_container_width=True, hide_index=True)

        # Carte du circuit (Basique avec positions GPS)
        st.markdown("### 🗺️ Tracé du Circuit")
        try:
            lap = session.laps.pick_fastest()
            pos = lap.get_telemetry().subset(['X', 'Y'])
            fig_map = px.line(pos, x='X', y='Y', title=f"Tracé: {session.event['EventName']}")
            fig_map.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', 
                font=dict(color='white'), showlegend=False,
                xaxis=dict(visible=False), yaxis=dict(visible=False)
            )
            fig_map.update_traces(line=dict(color='#ef4444', width=4))
            st.plotly_chart(fig_map, use_container_width=True)
        except Exception as e:
            st.warning("Données de carte non disponibles.")

    # --- ONGLET 2 : PERFORMANCE (TÉLÉMÉTRIE) ---
    with tab2:
        st.markdown("### ⚡ Comparaison Télémétrie (Vitesse)")
        
        drivers_list = session.results['Abbreviation'].unique().tolist()
        selected_drivers = st.multiselect("Sélectionner des pilotes à comparer (Max 3 conseillé)", drivers_list, default=drivers_list[:2])
        
        if selected_drivers:
            fig_telemetry = go.Figure()
            
            for driver in selected_drivers:
                try:
                    driver_lap = session.laps.pick_driver(driver).pick_fastest()
                    telemetry = driver_lap.get_telemetry()
                    
                    # Couleur F1
                    color = get_driver_color(driver, session)
                    
                    fig_telemetry.add_trace(go.Scatter(
                        x=telemetry['Distance'], 
                        y=telemetry['Speed'], 
                        mode='lines', 
                        name=driver,
                        line=dict(color=color, width=2)
                    ))
                except Exception as e:
                    st.warning(f"Pas de données télémétrie pour {driver}")

            fig_telemetry.update_layout(
                title="Vitesse vs Distance (Tour le plus rapide)",
                xaxis_title="Distance (m)",
                yaxis_title="Vitesse (km/h)",
                template="plotly_dark",
                plot_bgcolor='rgba(30, 41, 59, 0.5)',
                paper_bgcolor='rgba(15, 23, 42, 1)',
                hovermode="x unified"
            )
            st.plotly_chart(fig_telemetry, use_container_width=True)
            
            st.info("Ce graphique remplace le 'Radar Chart' de la maquette par une analyse réelle de la vitesse en tout point du circuit, permettant d'identifier les vitesses de pointe (Speed Trap) et les vitesses en virage.")

    # --- ONGLET 3 : ANALYSE DE COURSE ---
    with tab3:
        st.markdown("### ⏱️ Rythme de Course (Race Pace)")
        
        if session_type == "R":
            # Filtrer les tours lents (In/Out laps, Safety Car excessif)
            race_laps = session.laps.pick_quicklaps()
            
            # Sélectionner top 5 pilotes
            top_drivers = session.results.head(5)['Abbreviation'].tolist()
            
            # Conversion timedelta en secondes pour l'affichage
            race_laps['LapTimeSec'] = race_laps['LapTime'].dt.total_seconds()
            
            # 1. Box Plot (Distribution des temps)
            fig_box = px.box(
                race_laps[race_laps['Driver'].isin(top_drivers)], 
                x="Driver", 
                y="LapTimeSec", 
                color="Driver",
                color_discrete_map={d: get_driver_color(d, session) for d in top_drivers},
                title="Distribution des Temps au Tour (Top 5)"
            )
            fig_box.update_layout(template="plotly_dark", showlegend=False)
            st.plotly_chart(fig_box, use_container_width=True)
            
            # 2. Line Chart (Évolution tour par tour)
            st.markdown("### 📉 Évolution des Temps au Tour")
            fig_pace = go.Figure()
            
            for driver in top_drivers:
                driver_laps = race_laps[race_laps['Driver'] == driver]
                color = get_driver_color(driver, session)
                
                fig_pace.add_trace(go.Scatter(
                    x=driver_laps['LapNumber'],
                    y=driver_laps['LapTimeSec'],
                    mode='lines+markers',
                    name=driver,
                    line=dict(color=color),
                    marker=dict(size=4)
                ))
                
            fig_pace.update_layout(
                title="Rythme Tour par Tour",
                xaxis_title="Tour",
                yaxis_title="Temps (s)",
                template="plotly_dark",
                hovermode="x unified"
            )
            st.plotly_chart(fig_pace, use_container_width=True)
            
        else:
            st.warning("L'analyse du rythme de course n'est disponible que pour les sessions de Course (R).")