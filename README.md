# Policy Compliance RAG System

A Streamlit web application that performs automated compliance auditing of legal contracts using Retrieval-Augmented Generation (RAG). The system checks commercial contracts against a set of compliance rules derived from the [CUAD v1](https://www.atticusprojectai.org/cuad) dataset and produces a detailed, color-coded compliance report.

## Features

- **Automated Rule Generation** – Derives compliance rules from 41 legal clause categories in the CUAD dataset, focusing on critical topics such as Governing Law, Non-Compete, Exclusivity, Indemnification, Liability, Insurance, Termination, Assignment, Audit Rights, IP Ownership, and more.
- **Vector-Store-Backed Retrieval** – Indexes contract PDFs into a ChromaDB cloud collection using Google Generative AI embeddings, enabling semantic search over contract text.
- **LLM-Powered Compliance Checking** – Uses the Gemini 2.0 Flash model to analyze each retrieved contract section against the corresponding compliance rule and return a structured verdict.
- **Structured Results** – Each rule is evaluated as **Compliant**, **Non-Compliant**, or **Missing Info**, with verbatim evidence and an actionable remediation suggestion.
- **Interactive Dashboard** – Displays summary metrics, a color-coded results table (sortable by compliance status), and a one-click CSV download of the full audit report.

## Tech Stack

| Component | Library / Service |
|---|---|
| UI Framework | [Streamlit](https://streamlit.io/) |
| LLM & Embeddings | [Google Generative AI (Gemini)](https://ai.google.dev/) via `langchain-google-genai` |
| Vector Store | [ChromaDB Cloud](https://www.trychroma.com/) |
| RAG Orchestration | [LangChain](https://python.langchain.com/) |
| Data Handling | [Pandas](https://pandas.pydata.org/) |
| PDF Parsing | PyPDF via `langchain-community` |
| Data Validation | [Pydantic](https://docs.pydantic.dev/) |

## Dataset

This application uses the **Contract Understanding Atticus Dataset (CUAD) v1**, a corpus of more than 13,000 labels across 510 commercial legal contracts covering 41 categories of legally significant clauses. CUAD is published by [The Atticus Project](https://www.atticusprojectai.org/cuad) and is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

Download CUAD v1 at [www.atticusprojectai.org/cuad](https://www.atticusprojectai.org/cuad) and place the extracted folder at `./CUAD_v1` (the default dataset path).

## Prerequisites

- Python 3.9 or higher
- A [Google AI Studio](https://aistudio.google.com/) API key (for Gemini and Generative AI Embeddings)
- A [ChromaDB Cloud](https://www.trychroma.com/) account with an API key and tenant name

## Installation

```bash
git clone https://github.com/Waleed-Ahmad20/PolicyComplianceRAG-Streamlit.git
cd PolicyComplianceRAG-Streamlit
pip install -r requirements.txt
```

## Running the App

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

## Configuration

Fill in the sidebar fields before running an audit:

| Field | Description |
|---|---|
| **Google API Key** | Your Google Generative AI API key |
| **ChromaDB API Key** | Your ChromaDB Cloud API key |
| **ChromaDB Tenant** | Your ChromaDB Cloud tenant name |
| **Dataset Path** | Path to the CUAD v1 folder (default: `./CUAD_v1`) |
| **Target Contract** | Substring of the contract filename to audit (default: `DISTRIBUTOR AGREEMENT`) |

## Usage

1. Enter all configuration values in the sidebar.
2. Click **Generate Rules** to load compliance rules from the CUAD dataset.
3. Expand **View Rules** to inspect the generated rule set.
4. Click **Run Compliance Audit** to index the target contract and run all compliance checks.
5. Review the compliance results table – rows are color-coded:
   - 🟢 **Green** – Compliant
   - 🔴 **Red** – Non-Compliant
   - ⚫ **Gray** – Missing Info
6. Click **Download Report** to export the full results as a CSV file.

## Project Structure

```
PolicyComplianceRAG-Streamlit/
├── app.py               # Main Streamlit application
├── requirements.txt     # Python dependencies
└── CUAD_v1/             # CUAD dataset (download separately)
    ├── master_clauses.csv
    ├── CUAD_v1.json
    ├── CUAD_v1_README.txt
    └── full_contract_pdf/
```

## License

The application code in this repository is provided as-is. The CUAD v1 dataset is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) by The Atticus Project.
