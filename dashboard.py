import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime
import glob

st.set_page_config(page_title="Agent Business Dashboard", layout="wide")

st.title("🤖 Agent Business - Dashboard Analize")
st.markdown("---")

MEMORY_FILE = "/data/memory_index.json"

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return {"analyses": {}}

memory = load_memory()
analyses = memory.get("analyses", {})

# Sidebar
st.sidebar.header("📊 Statistici")
st.sidebar.metric("Total analize", len(analyses))

if analyses:
    last_domain = list(analyses.keys())[-1]
    last_date = analyses[last_domain]["date"][:10]
    st.sidebar.metric("Ultima analiza", last_domain, last_date)

st.sidebar.markdown("---")
st.sidebar.info("Dashboard creat cu Streamlit | Datele sunt salvate local")

# Tab-uri
tab1, tab2, tab3 = st.tabs(["📈 Lista Analize", "🔍 Cauta Analiza", "📄 PDF-uri Generate"])

with tab1:
    st.header("Toate analizele disponibile")
    
    if analyses:
        data = []
        for domain, info in analyses.items():
            data.append({
                "Domeniu": domain.upper(),
                "Data": info["date"][:10],
                "Ora": info["date"][11:16]
            })
        
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
        
        st.subheader("Detalii analiza")
        selected_domain = st.selectbox("Alege un domeniu:", list(analyses.keys()))
        
        if selected_domain:
            info = analyses[selected_domain]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Cercetare piata**")
                st.info(info.get("market", "N/A")[:500])
                
                st.markdown("**Oportunitate**")
                st.success(info.get("competition", "N/A")[:400])
            
            with col2:
                st.markdown("**Nume propuse**")
                st.write(info.get("business_names", "N/A"))
                
                st.markdown("**Potentiali clienti**")
                st.write(info.get("leads", "N/A")[:300])
    else:
        st.warning("Nu exista analize. Ruleaza agentul.")

with tab2:
    st.header("Cauta in analize")
    
    search_term = st.text_input("Cauta dupa domeniu:")
    
    if search_term and analyses:
        results = []
        for domain, info in analyses.items():
            if search_term.lower() in domain.lower():
                results.append(domain)
        
        if results:
            st.success(f"Gasite {len(results)} rezultate:")
            for r in results:
                st.markdown(f"- **{r.upper()}**")
        else:
            st.warning("Nu s-au gasit rezultate.")

with tab3:
    st.header("PDF-uri generate")
    
    pdf_files = glob.glob("/data/*.pdf")
    
    if pdf_files:
        for pdf in pdf_files:
            filename = os.path.basename(pdf)
            file_size = os.path.getsize(pdf) / 1024
            st.markdown(f"- **{filename}** ({file_size:.1f} KB)")
            
            with open(pdf, "rb") as f:
                st.download_button(
                    label=f"Descarca {filename}",
                    data=f,
                    file_name=filename,
                    mime="application/pdf",
                    key=filename
                )
    else:
        st.info("Nu exista PDF-uri. Ruleaza agentul.")

st.markdown("---")
st.caption(f"Dashboard actualizat: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")