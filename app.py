import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Dragon Ball API", page_icon="🐉", layout="wide")

BASE_URL = "https://dragonball-api.com/api"

@st.cache_data
def get_json(endpoint, params=None):
    url = f"{BASE_URL}/{endpoint}"
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()

def normalize_response(data):
    if isinstance(data, dict) and "items" in data:
        return pd.json_normalize(data["items"]), data.get("meta", {}), data.get("links", {})
    if isinstance(data, list):
        return pd.json_normalize(data), {}, {}
    if isinstance(data, dict):
        return pd.json_normalize([data]), {}, {}
    return pd.DataFrame(), {}, {}

def show_stats(df):
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total registros", len(df))
    c2.metric("Con imagen", int(df["image"].notna().sum()) if "image" in df.columns else 0)
    c3.metric("Razas distintas", int(df["race"].nunique()) if "race" in df.columns else 0)
    c4.metric("Géneros distintos", int(df["gender"].nunique()) if "gender" in df.columns else 0)

def show_charts(df):
    st.subheader("Estadísticas")
    col1, col2 = st.columns(2)

    with col1:
        if "race" in df.columns:
            raza_counts = df["race"].fillna("Desconocida").astype(str).value_counts().reset_index()
            raza_counts.columns = ["Raza", "Cantidad"]
            st.bar_chart(raza_counts.set_index("Raza"))

    with col2:
        if "gender" in df.columns:
            gender_counts = df["gender"].fillna("Desconocido").astype(str).value_counts().reset_index()
            gender_counts.columns = ["Género", "Cantidad"]
            st.bar_chart(gender_counts.set_index("Género"))

def show_character_detail(df):
    st.subheader("Detalle del personaje")
    if df.empty or "name" not in df.columns:
        st.info("No hay personajes para mostrar.")
        return

    elegido = st.selectbox("Selecciona un personaje", df["name"].astype(str).tolist())
    fila = df[df["name"].astype(str) == elegido].iloc[0]

    c1, c2 = st.columns([1, 2])

    with c1:
        if "image" in fila and pd.notna(fila["image"]):
            st.image(fila["image"], use_container_width=True)

    with c2:
        st.markdown(f"**Nombre:** {fila.get('name', 'N/A')}")
        st.markdown(f"**Ki:** {fila.get('ki', 'N/A')}")
        st.markdown(f"**Max Ki:** {fila.get('maxKi', 'N/A')}")
        st.markdown(f"**Raza:** {fila.get('race', 'N/A')}")
        st.markdown(f"**Género:** {fila.get('gender', 'N/A')}")
        st.markdown(f"**Afiliación:** {fila.get('affiliation', 'N/A')}")
        st.markdown(f"**Descripción:** {fila.get('description', 'N/A')}")

st.title("🐉 Dragon Ball API con Streamlit")
st.write("Aplicación web que consume una API online, permite filtrar datos y muestra estadísticas.")

menu = st.sidebar.radio("Sección", ["Personajes", "Planetas"])

try:
    if menu == "Personajes":
        st.sidebar.header("Filtros")

        activar_filtros = st.sidebar.checkbox("Usar filtros")
        nombre = st.sidebar.text_input("Buscar por nombre").strip()
        genero = st.sidebar.selectbox("Género", ["Todos", "Male", "Female", "Unknown"])
        raza = st.sidebar.selectbox("Raza", ["Todas", "Human", "Saiyan", "Namekian", "Majin", "Frieza Race", "Android", "Jiren Race", "God", "Angel", "Evil", "Nucleico", "Nucleico benigno", "Unknown"])
        afiliacion = st.sidebar.text_input("Afiliación").strip()

        if activar_filtros and any([nombre, genero != "Todos", raza != "Todas", afiliacion]):
            params = {}
            if nombre:
                params["name"] = nombre
            if genero != "Todos":
                params["gender"] = genero
            if raza != "Todas":
                params["race"] = raza
            if afiliacion:
                params["affiliation"] = afiliacion

            data = get_json("characters", params=params)
            df, meta, links = normalize_response(data)
            st.subheader("Resultados filtrados")
            st.caption("Los filtros no tienen paginación según la API.")
        else:
            pagina = st.sidebar.number_input("Página", min_value=1, value=1, step=1)
            limite = st.sidebar.selectbox("Elementos por página", [5, 10, 20, 50], index=1)

            data = get_json("characters", params={"page": pagina, "limit": limite})
            df, meta, links = normalize_response(data)
            st.subheader("Personajes paginados")

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total personajes", meta.get("totalItems", 0))
            c2.metric("En página", meta.get("itemCount", 0))
            c3.metric("Por página", meta.get("itemsPerPage", 0))
            c4.metric("Total páginas", meta.get("totalPages", 0))

            b1, b2, b3, b4 = st.columns(4)
            if links.get("first"):
                b1.link_button("Primera", links["first"])
            if links.get("previous"):
                b2.link_button("Anterior", links["previous"])
            if links.get("next"):
                b3.link_button("Siguiente", links["next"])
            if links.get("last"):
                b4.link_button("Última", links["last"])

        if df.empty:
            st.warning("No se encontraron resultados.")
            st.stop()

        columnas = [c for c in ["id", "name", "race", "gender", "affiliation", "ki", "maxKi", "image"] if c in df.columns]
        st.dataframe(df[columnas] if columnas else df, use_container_width=True, hide_index=True)

        show_stats(df)
        show_charts(df)
        show_character_detail(df)

    else:
        st.sidebar.header("Filtros de planetas")

        nombre_planeta = st.sidebar.text_input("Buscar por nombre").strip()
        destruidos = st.sidebar.selectbox("Destruidos", ["Todos", "true", "false"])

        params = {}
        if nombre_planeta:
            params["name"] = nombre_planeta
        if destruidos != "Todos":
            params["isDestroyed"] = destruidos

        data = get_json("planets", params=params if params else {"page": 1, "limit": 10})
        df, meta, links = normalize_response(data)

        st.subheader("Planetas")

        if isinstance(data, dict) and "items" in data:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total planetas", meta.get("totalItems", 0))
            c2.metric("En página", meta.get("itemCount", 0))
            c3.metric("Por página", meta.get("itemsPerPage", 0))
            c4.metric("Total páginas", meta.get("totalPages", 0))

        if df.empty:
            st.warning("No se encontraron planetas.")
            st.stop()

        columnas = [c for c in ["id", "name", "isDestroyed", "image", "description"] if c in df.columns]
        st.dataframe(df[columnas] if columnas else df, use_container_width=True, hide_index=True)

        if "isDestroyed" in df.columns:
            destroyed_counts = df["isDestroyed"].astype(str).value_counts().reset_index()
            destroyed_counts.columns = ["Estado", "Cantidad"]
            st.bar_chart(destroyed_counts.set_index("Estado"))

except requests.exceptions.RequestException as e:
    st.error(f"Error de conexión con la API: {e}")
except Exception as e:
    st.error(f"Error inesperado: {e}")