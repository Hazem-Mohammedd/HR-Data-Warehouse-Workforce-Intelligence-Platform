# HR-Data-Warehouse-Workforce-Intelligence-Platform
Built an automated, end-to-end HR intelligence platform designed to maximize workforce retention and optimize strategic planning by integrating Python ETL, SQL Star Schemas, Power BI, and GenAI copilots into a unified interactive view. This solution empowers executives to predict attrition, query live data, and automate policy support.

# Project excerpt
Designed and deployed a comprehensive HR Data & AI ecosystem, transforming legacy CSVs into a centralized SQL Star Schema, interactive Power BI dashboards, ML predictive models, and privacy-first local LLM copilots for automated workforce intelligence.

# Business Case

The company’s HR data was stored in old CSV systems that were not connected together. Because of this, reporting took a long time, there was no real-time view of workforce performance, and the company could not predict future HR trends.

HR teams also spent too much time on repetitive manual tasks, such as answering common employee questions and preparing custom reports for management. This reduced their ability to focus on important strategic work.

Project Goal

The goal was to build and launch a complete HR intelligence platform that uses AI to improve decision-making.

The system was created to:

- automate employee support tasks,
- provide real-time HR data,
- allow managers and executives to access reports easily, and
- help the company move from reactive reporting to proactive planning and forecasting.

# Process & Methodology

1. Data Ingestion & Quality Automation Engineered robust Python-based ETL pipelines to automate the extraction of data from legacy CSV sources. Implemented strict programmatic preprocessing, regex-based data cleansing, and structural validation checks to enforce data quality and integrity before staging and loading into the database.

2. Data Warehousing & Star Schema Architected a highly scalable enterprise Data Warehouse (HR_DW) on MS SQL Server. Designed a dimensional Star Schema topology, centralizing transactional data within a Fact_HR table, surrounded by conformed dimensions (Dim_Employee, Dim_Job, Dim_Location, Dim_Training). This structure was heavily optimized for high-performance analytical querying and reporting.

3. Business Intelligence & Dashboards (Power BI) Integrated Power BI with the SQL Data Warehouse to democratize descriptive analytics. Engineered a dynamic Dim_Date table using M-Language to enable robust, highly flexible time-intelligence analysis across the dataset. Developed complex DAX measures to track critical KPIs (Headcount, Turnover Rate, Average Tenure) and delivered an interactive suite of enterprise dashboards capable of independently addressing ~80% of recurring managerial reporting needs.

4. Predictive Analytics Engine Transitioned the platform from descriptive to predictive by developing machine learning models capable of forecasting employee attrition. By analyzing historical workforce data, the engine identifies underlying risk patterns and flight-risk probabilities, empowering HR leadership with data-driven workforce planning and proactive retention strategies.

5. HR Policy Copilot (RAG System) Engineered a privacy-first, 100% offline Retrieval-Augmented Generation (RAG) system to automate employee support. Embedded complex HR handbooks and policy PDFs using nomic-embed-text and stored the vectors in a FAISS database. Leveraged local Large Language Models (phi3 / mistral) to provide employees with highly accurate, context-aware policy answers without exposing sensitive internal data to external cloud APIs.

6. Executive Data Copilot (Text-to-SQL) Designed a Manager-Facing AI Agent to bridge the gap between executives and raw data. This copilot translates natural language questions into highly optimized T-SQL queries, executes them directly against the HR_DW Star Schema, and returns real-time, tabular insights, allowing senior leaders to answer complex, ad-hoc business questions instantaneously.

# Key Insights

- Attrition Drivers: Uncovered hidden correlations between specific compensation zones, tenure milestones, and elevated flight risks.
- Workforce Optimization: Identified distinct workforce distribution bottlenecks within critical business units, highlighting inefficiencies in the hiring pipeline.
- Program Efficacy: Demonstrated a quantifiable link between specific onboarding/training programs and extended average employee tenure.
Impact

- 90% Reduction in Ad-Hoc Reporting: The Text-to-SQL Executive Copilot eliminated the traditional week-long wait times for custom data pulls, enabling real-time executive decision-making.
- Massive Time Savings for HR: Automated 100% of routine policy inquiries via the RAG Copilot, freeing up dozens of hours monthly for HR business partners.
- Proactive Risk Mitigation: Enabled targeted retention interventions months in advance through the deployment of early-warning predictive attrition scoring.
- Enterprise Scalability: Established a single source of truth via the SQL Star Schema, laying a scalable foundation for all future People Analytics initiatives.

# Tools & Technologies Used

- Data Engineering: Python (Pandas), MS SQL Server, T-SQL, ODBC.
- Business Intelligence: Power BI, DAX, M-Language (Power Query), Data Modeling (Star Schema).
- Artificial Intelligence: Local LLMs (Ollama, Phi-3, Mistral, Nomic-Embed-Text), LangChain, FAISS Vector Database, Streamlit (UI/UX).
- Machine Learning: Scikit-Learn, Predictive Modeling.
