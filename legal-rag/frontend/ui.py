import os, requests, pandas as pd, streamlit as st

API_URL = os.getenv("API_URL", "http://backend:8000/query")

st.set_page_config(
    page_title="Legal RAG - Buscador de Fallos",
    page_icon="⚖️",
    layout="wide"
)

st.title("⚖️ Buscador de Fallos Jurisprudenciales")
st.markdown("Sistema RAG para consultas legales en expedientes judiciales")

# Sidebar con controles
with st.sidebar:
    st.header("📊 Configuración")
    top_n = st.slider("Número de resultados", 5, 12, 8)
    
    # Información del sistema
    try:
        health_response = requests.get(f"{API_URL.replace('/query', '/health')}", timeout=5)
        if health_response.status_code == 200:
            health_data = health_response.json()
            status = health_data.get("status", "unknown")
            if status == "healthy":
                st.success("✅ Sistema operativo")
            else:
                st.warning("⚠️ Sistema con problemas")
        else:
            st.error("❌ Sistema no disponible")
    except:
        st.error("❌ No se puede conectar al backend")

# Input principal
query = st.text_input(
    "💬 Pregunta al asistente legal",
    placeholder="Ej: ¿Qué dice sobre contratos de alquiler?",
    help="Ingresa tu consulta legal y el sistema buscará en la base de fallos"
)

if st.button("🔍 Buscar", type="primary") and query:
    with st.spinner("🔎 Consultando base de datos jurisprudencial..."):
        try:
            response = requests.post(
                API_URL, 
                json={"question": query, "top_n": top_n},
                timeout=60
            )
            
            if response.status_code != 200:
                st.error(f"❌ Error de API {response.status_code}: {response.text}")
            else:
                data = response.json()
                
                # Verificar si hay resultados
                if not data.get("results"):
                    st.warning("⚠️ No se encontraron resultados para tu consulta")
                else:
                    # Mostrar métricas
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("📄 Resultados", len(data["results"]))
                    with col2:
                        st.metric("⏱️ Tiempo total", f"{data.get('total_time', 0):.2f}s")
                    with col3:
                        st.metric("🔍 Búsqueda", f"{data.get('search_time', 0):.3f}s")
                    with col4:
                        st.metric("🤖 LLM", f"{data.get('llm_time', 0):.2f}s")
                    
                    st.divider()
                    
                    # Respuesta del asistente
                    st.markdown("### 🤖 Respuesta del Asistente")
                    st.markdown(data["markdown"])
                    
                    st.divider()
                    #mostrar data["results"]
                    # st.markdown("### 📋 Resultados de la Búsqueda")
                    # st.write(data["results"])
                    # Resultados detallados
                    st.markdown("### 📋 Documentos Consultados")
                    
                    # Crear DataFrame con manejo de errores
                    results_data = []
                    for i, result in enumerate(data["results"], 1):
                        results_data.append({
                            "#": i,
                            "Expediente": result.get("expte", "N/A"),
                            "Sección": result.get("section", "N/A")[:50] + "..." if len(result.get("section", "")) > 50 else result.get("section", "N/A"),
                            "Extracto": result.get("paragraph", "N/A")[:100] + "..." if len(result.get("paragraph", "")) > 100 else result.get("paragraph", "N/A"),
                            "Score": f"{result.get('score', 0):.2f}",
                            "Tipo": result.get("search_type", "hybrid")
                        })
                    
                    df = pd.DataFrame(results_data)
                    
                    # Mostrar tabla con estilo
                    st.dataframe(
                        df,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "#": st.column_config.NumberColumn("#", width="small"),
                            "Expediente": st.column_config.TextColumn("Expediente", width="small"),
                            "Sección": st.column_config.TextColumn("Sección", width="medium"),
                            "Extracto": st.column_config.TextColumn("Extracto", width="large"),
                            "Score": st.column_config.NumberColumn("Score", width="small"),
                            "Tipo": st.column_config.TextColumn("Tipo", width="small")
                        }
                    )
                    
                    # Expandir resultados individuales
                    with st.expander("📄 Ver detalles completos"):
                        for i, result in enumerate(data["results"], 1):
                            st.markdown(f"**{i}. Expediente {result.get('expte', 'N/A')} - {result.get('section', 'N/A')}**")
                            st.markdown(f"*Score: {result.get('score', 0):.3f} | Tipo: {result.get('search_type', 'hybrid')}*")
                            st.markdown(result.get("paragraph", "Sin contenido"))
                            st.markdown(f"📁 *Archivo: {result.get('path', 'N/A')}*")
                            if i < len(data["results"]):
                                st.divider()
                    
                    # Agrupar resultados por expediente
                    grouped = {}
                    for result in data["results"]:
                        expte = result.get("expte", "N/A")
                        if expte not in grouped:
                            grouped[expte] = {
                                "idea_central": result.get("idea_central", "Sin idea central"),
                                "idea_central_original": result.get("idea_central_original", result.get("idea_central", "Sin idea central")),
                                "articulos_citados": result.get("articulos_citados", []),
                                "materia_preliminar": result.get("materia_preliminar", ""),
                                "metadatos": result.get("metadatos", {}),
                                "extractos": [],
                                "paths": set(),
                                "sections": set(),
                                "scores": [],
                                "search_types": set(),
                            }
                        grouped[expte]["extractos"].append(result.get("paragraph", "Sin contenido"))
                        grouped[expte]["paths"].add(result.get("path", "N/A"))
                        grouped[expte]["sections"].add(result.get("section", "N/A"))
                        grouped[expte]["scores"].append(result.get("score", 0))
                        grouped[expte]["search_types"].add(result.get("search_type", "hybrid"))

                    st.markdown("### 📋 Fallos relevantes agrupados por expediente")
                    for expte, info in grouped.items():
                        with st.container():
                            st.markdown(f"#### Expediente: `{expte}`")
                            st.markdown(f"**Materia:** {info['materia_preliminar']}")
                            st.markdown(f"**Archivos:** {'; '.join(info['paths'])}")
                            st.markdown(f"**Secciones:** {'; '.join(info['sections'])}")
                            st.markdown(f"**Score promedio:** {sum(info['scores'])/len(info['scores']):.2f}")
                            st.markdown(f"**Tipo de búsqueda:** {', '.join(info['search_types'])}")
                            st.markdown(":blue[Idea central resumida por LLM]:")
                            st.info(info["idea_central"])
                            with st.expander("Ver idea central original guardada en base de datos"):
                                st.write(info["idea_central_original"])
                            st.markdown(":orange[Artículos citados]:")
                            if info["articulos_citados"]:
                                for art in info["articulos_citados"]:
                                    st.markdown(f"- {art}")
                            else:
                                st.write("No hay artículos citados.")
                            st.markdown(":green[Extractos relevantes]:")
                            for i, ext in enumerate(info["extractos"], 1):
                                st.markdown(f"{i}. {ext}")
                            st.divider()
                    
                    # Mostrar tabla tipo jurisprudencial agrupada por expediente y extracto (nuevo formato)
                    if data.get("results"):
                        results_data = []
                        for i, fallo in enumerate(data["results"], 1):
                            expte = fallo.get("expte", "N/A")
                            materia = fallo.get("materia_preliminar", "N/A")
                            idea_central = fallo.get("idea_central", "-")
                            articulos = fallo.get("articulos_citados", [])
                            # Formatear artículos citados: main_source + números
                            articulos_str = "; ".join(
                                f"{a.get('main_source', '')} {', '.join(map(str, a.get('cited_articles', [])))}".strip()
                                for a in articulos if a
                            ) if articulos else "-"
                            for sec, ext in zip(fallo.get("sections", []), fallo.get("extractos", [])):
                                results_data.append({
                                    "Expte.": expte,
                                    "Sección": sec,
                                    "Extracto": ext,
                                    "Materia": materia,
                                    "Artículos citados": articulos_str,
                                    "Idea central": idea_central
                                })
                        df = pd.DataFrame(results_data)
                        st.markdown("### 📋 Resultados jurisprudenciales relevantes")
                        st.dataframe(
                            df,
                            use_container_width=True,
                            hide_index=True
                        )
                        # Expander para idea central original
                        with st.expander("Ver ideas centrales originales de los fallos"):
                            for i, fallo in enumerate(data["results"], 1):
                                st.markdown(f"**{i}. Expediente {fallo.get('expte', 'N/A')}**")
                                st.write(fallo.get("idea_central", "-"))
                                st.divider()
        
        except requests.RequestException as e:
            st.error(f"❌ Error de conexión: {str(e)}")
        except Exception as e:
            st.error(f"❌ Error inesperado: {str(e)}")

# Footer con información
st.divider()
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.8em;'>
⚖️ Sistema RAG Legal | Sala Civil y Comercial<br>
Búsqueda híbrida con IA generativa
</div>
""", unsafe_allow_html=True)
