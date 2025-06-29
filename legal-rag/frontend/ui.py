import os, requests, pandas as pd, streamlit as st
import re

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
                
                # --------------------------------------------
                # Extraer resúmenes LLM por expediente del markdown
                # Formato esperado: [1234] «Texto…»
                summary_by_expte = {}
                markdown_text = data.get("markdown", "") or ""
                for expte, paragraph in re.findall(r"\[(\d+)\]\s+«([^»]+)»", markdown_text):
                    summary_by_expte[expte] = paragraph.strip()
                # --------------------------------------------
                
                # Mostrar JSON completo para depuración
                with st.expander("🗄️ Ver JSON completo de la respuesta"):
                    st.json(data)
                
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
                    
                    # Preparar datos para documentos consultados (DataFrame) sin mostrar todavía
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
                    
                    # Agrupar resultados por expediente
                    grouped = {}
                    for result in data["results"]:
                        expte = result.get("expte", "N/A")
                        if expte not in grouped:
                            grouped[expte] = {
                                "idea_central": result.get("idea_central", "Sin idea central"),
                                "articulos_citados": result.get("articulos_citados", []),
                                "materia_preliminar": result.get("materia_preliminar", ""),
                                "metadatos": result.get("metadatos", {}),
                                "extractos": [],
                                "paths": set(),
                                "sections": set(),
                                "scores": [],
                                "search_types": set(),
                                "llm_summary": summary_by_expte.get(expte, ""),
                            }
                        grouped[expte]["extractos"].append(result.get("paragraph", "Sin contenido"))
                        grouped[expte]["paths"].add(result.get("path", "N/A"))
                        grouped[expte]["sections"].add(result.get("section", "N/A"))
                        grouped[expte]["scores"].append(result.get("score", 0))
                        grouped[expte]["search_types"].add(result.get("search_type", "hybrid"))

                    # Ordenar por score promedio descendente
                    sorted_grouped = sorted(
                        grouped.items(),
                        key=lambda kv: (sum(kv[1]['scores'])/len(kv[1]['scores']) if kv[1]['scores'] else 0),
                        reverse=True
                    )

                    st.markdown("### 📋 Fallos relevantes")
                    for expte, info in sorted_grouped:
                        with st.container():
                            st.markdown(f"#### Expediente: `{expte}`")
                            # ---- Diseño estético de la información general ----
                            st.markdown(
                                f"##### ⚖️ <span style='font-weight:600;'>{info['materia_preliminar']}</span>",
                                unsafe_allow_html=True
                            )

                            row1_left, row1_right = st.columns(2, gap="large")
                            with row1_left:
                                st.markdown(
                                    f"<span style='font-size:15px'>📁 <b>Archivo:</b><br>{'; '.join(info['paths'])}</span>",
                                    unsafe_allow_html=True
                                )
                            with row1_right:
                                st.markdown(
                                    f"<span style='font-size:15px'>📑 <b>Sección:</b><br>{'; '.join(info['sections'])}</span>",
                                    unsafe_allow_html=True
                                )

                            row2_left, row2_right = st.columns(2, gap="large")
                            with row2_left:
                                st.markdown(
                                    f"<span style='font-size:15px'>🏷️ <b>Tipo de búsqueda:</b> {', '.join(info['search_types'])}</span>",
                                    unsafe_allow_html=True
                                )
                            with row2_right:
                                avg_score = sum(info['scores'])/len(info['scores']) if info['scores'] else 0
                                st.markdown(
                                    f"<span style='font-size:15px'>⭐ <b>Score promedio:</b> {avg_score:.2f}</span>",
                                    unsafe_allow_html=True
                                )

                            st.divider()

                            # Justificación LLM primero
                            if info.get("llm_summary"):
                                st.markdown(":violet[¿Por qué este fallo puede ayudarte?]:")
                                st.write(info["llm_summary"])

                            # Extractos relevantes después
                            st.markdown(":green[Párrafos del fallo que pueden contestar tu pregunta]:")
                            for i, ext in enumerate(info["extractos"], 1):
                                st.markdown(f"{i}. {ext}")

                            # Idea central resumida luego
                            st.markdown(":blue[Idea central del fallo resumida]:")
                            st.info(info["idea_central"])

                            # Artículos citados en todo el fallo
                            st.markdown(":orange[Artículos citados en todo el fallo]:")
                            if info["articulos_citados"]:
                                formatted_arts = []
                                for art in info["articulos_citados"]:
                                    if not art:
                                        continue
                                    main_src = art.get("main_source", "").strip()
                                    nums = art.get("cited_articles", [])
                                    nums_str = ", ".join(map(str, nums)) if nums else ""
                                    if main_src and nums:
                                        label = "artículo" if len(nums) == 1 else "artículos"
                                        formatted_arts.append(f"**\"{main_src}\"** {label} {nums_str}.")
                                    elif main_src:
                                        formatted_arts.append(f"**\"{main_src}\"**.")
                                if formatted_arts:
                                    for line in formatted_arts:
                                        st.markdown(f"- {line}")
                                else:
                                    st.write("No hay artículos citados.")
                            else:
                                st.write("No hay artículos citados.")
                            st.divider()
                    
                    # ------------------------------------------------
                    #   Expanders al final
                    # ------------------------------------------------

                    st.markdown("### ➖ Información adicional (desplegable)")

                    with st.expander("🤖 Respuesta del Asistente"):
                        st.markdown(data["markdown"])

                    with st.expander("📋 Documentos Consultados"):
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
                        # Detalles individuales dentro del mismo expander
                        st.markdown("---")
                        st.markdown("#### Detalles individuales")
                        for i, result in enumerate(data["results"], 1):
                            st.markdown(f"**{i}. Expediente {result.get('expte', 'N/A')} - {result.get('section', 'N/A')}**")
                            st.markdown(f"*Score: {result.get('score', 0):.3f} | Tipo: {result.get('search_type', 'hybrid')}*")
                            st.markdown(result.get("paragraph", "Sin contenido"))
                            st.markdown(f"📁 *Archivo: {result.get('path', 'N/A')}*")
                            if i < len(data["results"]):
                                st.divider()

                            # (Informacion general ya mostrada arriba; bloque duplicado eliminado)
        
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
