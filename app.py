__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import os, json, hashlib, time, glob
import logging
import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
try:
    from langchain_chroma import Chroma
    logger.info("Using Chroma from langchain_chroma.")
except ImportError:
    from langchain_community.vectorstores import Chroma
    logger.info("Using Chroma fallback from langchain_community.vectorstores.")
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
import chromadb

st.set_page_config(page_title="Policy Compliance Checker", layout="wide")
st.title("Policy Compliance Checker RAG System")

with st.sidebar:
    st.header("Configuration")
    google_api_key = st.text_input("Google API Key", type="password")
    chroma_api_key = st.text_input("ChromaDB API Key", type="password")
    chroma_tenant = st.text_input("ChromaDB Tenant")
    data_path = st.text_input("Dataset Path", value="./CUAD_v1")
    target_contract = st.text_input("Target Contract", value="DISTRIBUTOR AGREEMENT")
    
    if google_api_key:
        os.environ["GOOGLE_API_KEY"] = google_api_key

@st.cache_data
def generate_rules(data_path):
    df = pd.read_csv(f"{data_path}/master_clauses.csv", nrows=0)
    all_categories = [c for c in df.columns if "-Answer" not in c and c != "Filename"]
    critical_keywords = ["Governing Law", "Non-Compete", "Exclusivity", "Indemnification", 
                        "Liability", "Insurance", "Termination", "Assignment", 
                        "Audit", "IP Ownership", "Warranty", "Solicit", "Most Favored"]
    selected_categories = [cat for cat in all_categories if any(k in cat for k in critical_keywords)]
    
    return [{
        "id": f"R{i+1:02d}",
        "topic": cat,
        "requirement": f"Verify strict compliance regarding '{cat}'. Identify obligations, restrictions, or rights.",
        "keywords": cat.replace("-", " ").replace("_", " ").lower()
    } for i, cat in enumerate(selected_categories)]

@st.cache_resource
def setup_vectorstore(_chroma_api_key, _chroma_tenant, target_file, _embedding_function):
    client = chromadb.CloudClient(api_key=_chroma_api_key, tenant=_chroma_tenant, database='PolicyCheckerRAG')
    collection = client.get_or_create_collection("compliance_store")
    existing = collection.get(where={"source": target_file})
    
    vectorstore = Chroma(client=client, collection_name="compliance_store", embedding_function=_embedding_function)
    
    if len(existing['ids']) == 0:
        raw_docs = PyPDFLoader(target_file).load_and_split(
            RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=300))
        
        unique_docs = []
        seen_hashes = set()
        for doc in raw_docs:
            doc.metadata["source"] = target_file
            content_hash = hashlib.md5(doc.page_content.encode('utf-8')).hexdigest()
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_docs.append(doc)
        
        progress_bar = st.progress(0)
        for i in range(0, len(unique_docs), 10):
            vectorstore.add_documents(unique_docs[i:i+10])
            progress_bar.progress(min((i+10)/len(unique_docs), 1.0))
            time.sleep(5)
    
    return vectorstore

class ComplianceAnalysis(BaseModel):
    status: str = Field(description="Result: 'Compliant', 'Non-Compliant', or 'Missing Info'")
    evidence: str = Field(description="Verbatim quote from the text supporting the finding.")
    remediation: str = Field(description="Actionable suggestion if non-compliant; otherwise 'None'.")

def run_compliance_check(rules, retriever, llm):
    parser = JsonOutputParser(pydantic_object=ComplianceAnalysis)
    prompt = PromptTemplate(
        template="""You are a strict Legal Compliance Auditor.
Rule to Check: {rule_requirement}
Contract Sections (Context):
{context}
Analyze the context against the rule.
{format_instructions}""",
        input_variables=["rule_requirement", "context"],
        partial_variables={"format_instructions": parser.get_format_instructions()})
    
    chain = prompt | llm | parser
    results = []
    progress = st.progress(0)
    status_text = st.empty()
    
    for i, rule in enumerate(rules):
        status_text.text(f"Checking rule {i+1}/{len(rules)}: {rule['topic']}")
        docs = retriever.invoke(f"{rule['topic']} {rule['keywords']}")
        context = "\n---\n".join([d.page_content for d in docs])
        
        try:
            response = chain.invoke({"rule_requirement": rule['requirement'], "context": context})
            results.append({"Rule ID": rule['id'], "Topic": rule['topic'], 
                          "Requirement": rule['requirement'], **response})
        except Exception as e:
            results.append({"Rule ID": rule['id'], "Topic": rule['topic'], 
                          "status": "Error", "evidence": str(e), "remediation": "N/A"})
        
        progress.progress((i+1)/len(rules))
    
    status_text.empty()
    progress.empty()
    return results

if all([google_api_key, chroma_api_key, chroma_tenant]) and os.path.exists(data_path):

    if st.button("Generate Rules"):
        with st.spinner("Generating compliance rules..."):
            st.session_state.rules = generate_rules(data_path)
    
    if 'rules' in st.session_state:
        st.success(f"{len(st.session_state.rules)} compliance rules loaded")
        with st.expander("View Rules"):
            st.json(st.session_state.rules)

        pdf_files = glob.glob(f"{data_path}/**/*.pdf", recursive=True)
        target_file = next((f for f in pdf_files if target_contract in f), None)
        
        if target_file:
            st.info(f"Target: {os.path.basename(target_file)}")
            
            if st.button("Run Compliance Audit"):
                with st.spinner("Setting up vector store..."):
                    embedding_fn = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
                    vectorstore = setup_vectorstore(chroma_api_key, chroma_tenant, target_file, embedding_fn)
                    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
                    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0)
                
                st.write("### Running Compliance Checks...")
                results = run_compliance_check(st.session_state.rules, retriever, llm)
                st.session_state.results = results
        else:
            st.error(f"Contract '{target_contract}' not found")

    if 'results' in st.session_state:
        st.write("## Compliance Audit Results")
        df = pd.DataFrame(st.session_state.results)

        col1, col2, col3 = st.columns(3)
        col1.metric("Compliant", len(df[df['status']=='Compliant']))
        col2.metric("Non-Compliant", len(df[df['status']=='Non-Compliant']))
        col3.metric("Missing Info", len(df[df['status']=='Missing Info']))

        comparison = df[['Topic', 'status', 'evidence']].copy()
        comparison['__sort'] = comparison.status.map({"Non-Compliant":0, "Missing Info":1, "Compliant":2})
        comparison = comparison.sort_values(['__sort', 'Topic']).drop(columns='__sort')
        
        def color_status(val):
            colors = {"Non-Compliant": "background-color: #FF0000", 
                     "Missing Info": "background-color: #808080",
                     "Compliant": "background-color: #00ff00"}
            return colors.get(val, "")
        
        st.dataframe(comparison.style.applymap(color_status, subset=['status']), 
                    use_container_width=True, height=600)

        csv = df.to_csv(index=False)
        st.download_button("Download Report", csv, "compliance_report.csv", "text/csv")
        
else:
    st.warning("Please configure all settings in the sidebar and ensure dataset path exists.")
