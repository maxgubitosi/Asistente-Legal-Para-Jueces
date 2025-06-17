import os, requests, pandas as pd, streamlit as st

API_URL = os.getenv("API_URL", "http://backend:8000/query")

st.title("Buscador de Fallos")

top_n = st.sidebar.slider("Resultados", 5, 20, 8)
query  = st.text_input("Pregunta al asistente")

if st.button("Buscar") and query:
    with st.spinner("Consultando…"):
        r = requests.post(API_URL, json={"question": query, "top_n": top_n})
    if r.status_code != 200:
        st.error(f"API error {r.status_code}: {r.text}")
    else:
        data = r.json()
        df   = pd.DataFrame(data["results"])
        # Usar 'paragraph' en lugar de 'extracto' para coincidir con los datos del backend
        st.dataframe(df[["expte", "section", "paragraph"]], use_container_width=True)
        st.markdown("### Resumen")
        st.markdown(data["markdown"])
