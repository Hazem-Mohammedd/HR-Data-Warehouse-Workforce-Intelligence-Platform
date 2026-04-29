import streamlit as st
import pandas as pd
# Import the database engine and the main ETL function from the pipeline file
from etl_pipeline import engine, main_etl_process
import PyPDF2
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_community.vectorstores import FAISS
import os
from google import genai
from langchain_community.utilities import SQLDatabase
from langchain_ollama import ChatOllama
from sqlalchemy import create_engine

# ==========================================
# 1. Page Configuration
# ==========================================
st.set_page_config(page_title="HR ETL Pipeline", page_icon="🏢", layout="wide")

# ==========================================
# 1.5 Custom CSS Injection (Advanced Dark UI)
# ==========================================
def inject_custom_css():
    st.markdown("""
    <style>
    /* 1. Advanced Animated Gradient Background */
    .stApp {
        background: linear-gradient(-45deg, #020617, #0f172a, #1d4ed8, #0f172a);
        background-size: 400% 400%;
        animation: gradientBG 15s ease infinite;
    }
    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* 2. Global Text Color Enforcement for Readability */
    .stApp, h1, h2, h3, h4, h5, h6, p, span, div, label, li {
        color: #f8fafc !important;
    }

    /* 3. Premium Glassmorphism (Metrics, Expanders, DataFrames) */
    div[data-testid="metric-container"], 
    div[data-testid="stExpander"], 
    .stDataFrame {
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(16px) saturate(120%) !important;
        -webkit-backdrop-filter: blur(16px) saturate(120%) !important;
        border-radius: 16px !important;
        padding: 15px !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2) !important;
        transition: transform 0.3s ease, border 0.3s ease !important;
    }
    
    /* Interactive hover effect for glass cards */
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }

    /* 4. Ultra-Smooth Glowing Button */
    button[kind="primary"] {
        background: linear-gradient(90deg, #2563eb, #3b82f6) !important;
        border: none !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px !important;
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.4) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    button[kind="primary"]:hover {
        box-shadow: 0 0 25px rgba(59, 130, 246, 0.8), 0 0 40px rgba(59, 130, 246, 0.4) !important;
        transform: translateY(-3px) !important;
        filter: brightness(1.1) !important;
    }
    button[kind="primary"]:active {
        transform: translateY(0px) !important;
    }

    /* 5. Gradient Text for Main Title */
    h1:first-of-type {
        background: linear-gradient(90deg, #93c5fd, #3b82f6) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        font-weight: 800 !important;
    }
    </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# ==========================================
# 2. UI Tabs Setup & Custom Title
# ==========================================
st.markdown("""
    <div style="display: flex; align-items: center; margin-bottom: 1.5rem;">
        <svg width="42" height="42" viewBox="0 0 24 24" fill="#93c5fd" style="margin-right: 15px; filter: drop-shadow(0px 4px 6px rgba(0,0,0,0.3));">
            <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 14H7v-2h5v2zm0-4H7v-2h5v2zm0-4H7V7h5v2zm5 8h-3v-2h3v2zm0-4h-3v-2h3v2zm0-4h-3V7h3v2z"/>
        </svg>
        <h1 style="margin: 0; padding: 0;">HR Analytics: Data Ingestion Pipeline</h1>
    </div>
""", unsafe_allow_html=True)

tabs = st.tabs(["Ingestion & Quality", "Predictive Engine", "HR Policy Copilot", "Executive Copilot"])

# --- Tab 1: Data Ingestion & Quality 📊 ---
with tabs[0]:
    st.markdown("""
    Welcome to the HR Data Ingestion Portal. This tab is used to upload and process your employee data.
    The system will automatically:
    1. **Extraction & Cleaning:** Remove duplicates, fix dates, and clean formatting.
    2. **Staging:** Truncate the staging area.
    3. **Data Warehouse Load:** Intelligently Upsert data into the Star Schema.
    """)

    st.divider()

    uploaded_file = st.file_uploader("📥 Upload CSV file here", type=['csv'], key="tab1_uploader")

    if uploaded_file is not None:
        raw_df = pd.read_csv(uploaded_file)
        
        st.info(f"📄 File uploaded successfully! Contains {len(raw_df)} rows and {len(raw_df.columns)} columns.")
        
        with st.expander("🔍 Raw Data Preview"):
            st.dataframe(raw_df.head(10))

        if st.button("🚀 Run ETL Pipeline & Update Data Warehouse", use_container_width=True, type="primary", key="tab1_btn"):
            
            with st.spinner("⏳ Cleaning and processing data in SQL Server... Please wait."):
                uploaded_file.seek(0)
                success, message = main_etl_process(uploaded_file, engine)
                
                if success:
                    st.balloons()
                    st.success(f"✅ {message}")
                    
                    st.markdown("### 📊 Process Summary")
                    col1, col2, col3 = st.columns(3)
                    active = len(raw_df[raw_df['ExitDate'].isna()])
                    terminated = len(raw_df[raw_df['ExitDate'].notna()])
                    
                    col1.metric("Total Records Processed", len(raw_df))
                    col2.metric("🟢 Active Employees", active)
                    col3.metric("🔴 Terminated Employees", terminated)
                    st.info("💡 Tab 1 is complete! Phase 2: Python ETL is finished.")
                else:
                    st.error(f"❌ Pipeline execution failed: {message}")

# --- Tab 2: Predictive Engine 🧠 ---
with tabs[1]:
    st.markdown("""
        <h2 style='color: #60a5fa;'>🧠 AI Predictive Engine</h2>
        <p style='color: #cbd5e1;'>Run the XGBoost Machine Learning model to analyze active employees and identify top flight risks.</p>
    """, unsafe_allow_html=True)
    
    # Create a nice layout
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.info("💡 **How it works:**\nThe model analyzes Tenure, Pay Zone, Satisfaction, and Training patterns of past resignations to score current employees.")
        
        if st.button("🚀 Run AI Engine & Send Alert", use_container_width=True):
            st.session_state['run_ml'] = True

    with col2:
        if st.session_state.get('run_ml', False):
            with st.spinner("Training XGBoost Beast & Scoring Employees..."):
                # Import the functions from your ML script
                from predictive_engine import run_ml_pipeline, send_hr_alert_email
                
                # Run the model
                top_risk_df = run_ml_pipeline()
                
            if top_risk_df is not None:
                st.success("✅ Analysis Complete! Top At-Risk Employees identified.")
                st.dataframe(top_risk_df, use_container_width=True)
                
                with st.spinner("Preparing and sending automated email to HR..."):
                    email_status = send_hr_alert_email(top_risk_df)
                    
                if email_status:
                    st.toast('Email Alert Sent Successfully!', icon='📧')
                    st.success("📧 Automated Alert successfully delivered to the HR Inbox!")
                else:
                    st.error("❌ Failed to send email. Please check your SMTP credentials.")
            
            # Reset state so it doesn't run endlessly
            st.session_state['run_ml'] = False

# --- Tab 3: HR Policy Copilot 🤖 ---
with tabs[2]:
    st.markdown("""
        <h2 style='color: #60a5fa;'>🦙 HR Policy Copilot (Powered by Ollama)</h2>
        <p style='color: #cbd5e1;'>Upload a company policy document (PDF) and ask questions. The AI will answer strictly based on the document.</p>
    """, unsafe_allow_html=True)
    
    # 1. File Uploader for the PDF
    pdf_file = st.file_uploader("📄 Upload Company Policy (PDF)", type="pdf")
    
    if pdf_file is not None:
        # 2. Process the PDF only once
        if "vector_store" not in st.session_state or st.session_state.get('current_file') != pdf_file.name:
            with st.spinner("🧠 Gemini is reading and memorizing the document..."):
                # Extract text from PDF
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                raw_text = ""
                for page in pdf_reader.pages:
                    if page.extract_text():
                        raw_text += page.extract_text()
                
                # Split text into chunks
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=200,
                    length_function=len
                )
                chunks = text_splitter.split_text(raw_text)
                
                # Use Local Ollama Embeddings (No Internet Needed!)
                embeddings = OllamaEmbeddings(model="nomic-embed-text")
                vector_store = FAISS.from_texts(chunks, embeddings)
                
                # Save to session state
                st.session_state.vector_store = vector_store
                st.session_state.current_file = pdf_file.name
                
                # Initialize chat history
                st.session_state.chat_history = []
            
            st.success("✅ Document memorized! You can now ask questions.")

        # 3. Chat Interface
        st.markdown("---")
        
        # Display previous chat history
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # 4. User Input
        user_question = st.chat_input("Ask a question about the policy (e.g., 'What is the maternity leave policy?')")
        
        if user_question:
            # Show user question
            with st.chat_message("user"):
                st.markdown(user_question)
            
            # Add user question to history
            st.session_state.chat_history.append({"role": "user", "content": user_question})
            
            # 5. RAG Process: Local Mistral via Ollama
            with st.chat_message("assistant"):
                with st.spinner("Mistral is thinking locally..."):
                    # Searching for relevant paragraphs
                    docs = st.session_state.vector_store.similarity_search(user_question, k=3)
                    context = "\n\n".join([doc.page_content for doc in docs])
                    
                    # Writing the prompt
                    prompt_text = f"Answer based ONLY on context: {context}\n\nQuestion: {user_question}"
                    
                    # Talk to Local Mistral
                    # Talk to Local Phi-3 (Lightweight & Fast!)
                    llm = ChatOllama(model="phi3", temperature=0)
                    response = llm.invoke(prompt_text)
                    
                    ai_answer = response.content
                    
                    st.markdown(ai_answer)
            
            # Add AI answer to history
            st.session_state.chat_history.append({"role": "assistant", "content": ai_answer})


with tabs[3]: # Tab 4: Executive Copilot
    st.markdown("""
        <h2 style='color: #fbbf24;'>📊 Executive Data Copilot (Text-to-SQL)</h2>
        <p style='color: #cbd5e1;'>Ask business questions in plain English/Arabic, and the local AI will query your SQL Server Data Warehouse to get answers.</p>
    """, unsafe_allow_html=True)
    
    # --- FIX 1: Cache the Model in Session State ---
    if "sql_llm" not in st.session_state:
        from langchain_ollama import ChatOllama
        # You can use phi3 or phi3:mini depending on what you pulled
        st.session_state.sql_llm = ChatOllama(model="phi3", temperature=0)
    
    # 1. Database Connection 
    db_server = os.getenv("DB_SERVER")
    db_name = os.getenv("DB_NAME")
    db_uri = f"mssql+pyodbc://@{db_server}/{db_name}?driver=ODBC+Driver+17+for+SQL+Server&Trusted_Connection=yes"
    
    try:
        # Optimized Database Connection 
        db = SQLDatabase.from_uri(
            db_uri,
            include_tables=["Fact_HR", "Dim_Employee", "Dim_Job", "Dim_Location", "Dim_Training"],
            sample_rows_in_table_info=0
        )
        st.success(f"✅ Successfully connected to Data Warehouse: **{db_name}** on **{db_server}**!")
    except Exception as e:
        st.error(f"⚠️ Database connection failed. Error: {e}")
        db = None

    if db:
        st.markdown("---")
        manager_query = st.chat_input("Ask a data question (e.g., 'What is the total salary by department?')")
        
        if manager_query:
            with st.chat_message("user"):
                st.markdown(manager_query)
                
            with st.chat_message("assistant"):
                with st.spinner("Generating ultra-fast T-SQL..."):
                    try:
                        # Fetch the cached model
                        llm = st.session_state.sql_llm
                        
                        # --- FIX 2: Reduce Schema Size (Manual Definition) ---
                        db_schema = """
                        Fact_HR(EmployeeID, EmployeeKey, JobKey, LocationKey, TrainingKey, StartDate, ExitDate, SurveyDate, TrainingDate, EmployeeStatus, EmployeeType, EmployeeClassificationType, PayZone, AttritionFlag, TerminationType, TerminationDescription, TenureDays, PerformanceScore, CurrentRating, EngagementScore, SatisfactionScore, WorkLifeBalanceScore, TrainingOutcome, TrainingDurationDays, TrainingCost)
                        Dim_Employee(EmployeeKey, EmployeeID, FullName, Age, Gender, Race, MaritalStatus, Supervisor, Email)
                        Dim_Job(JobKey, Title, Department, BusinessUnit, Division, JobFunctionDescription)
                        Dim_Location(LocationKey, LocationCode, State, City)
                        Dim_Training(TrainingKey, ProgramName, TrainingType, TrainerName)
                        """
                        
                        # 3. Prompt for T-SQL Generation
                        sql_prompt = f"""
                        You are an expert MS SQL Server Data Analyst.
                        Given the following database schema summary:
                        {db_schema}
                        
                        Write a valid T-SQL query to answer the following question:
                        {manager_query}
                        
                        CRITICAL RULES:
                        1. ONLY use table and column names explicitly listed above.
                        2. DO NOT invent columns.
                        3. Return ONLY the SQL code. No explanations, no markdown formatting.
                        """
                        
                        # 4. Generate SQL
                        generated_sql = llm.invoke(sql_prompt).content.strip()
                        cleaned_sql = generated_sql.replace("```sql", "").replace("```", "").strip()
                        
                        with st.expander("🔍 View Generated T-SQL Query"):
                            st.code(cleaned_sql, language="sql")
                            
                        # 5. Execute SQL
                        raw_result = db.run(cleaned_sql)
                        
                        # --- FIX 4: Remove Second LLM Call (Display Table directly) ---
                        if raw_result and raw_result.strip() != "":
                            st.success("⚡ Data Retrieved:")
                            st.write(raw_result) # Just display the raw data/table
                        else:
                            st.warning("Query executed successfully, but returned no data.")
                            
                    except Exception as e:
                        st.error(f"❌ An error occurred: {e}")