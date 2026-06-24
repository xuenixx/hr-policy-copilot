import streamlit as st
import anthropic
import chromadb
import fitz  # pymupdf
import PyPDF2
import io

st.set_page_config(page_title="HR Policy Co-Pilot", page_icon="⚖️", layout="wide")

st.title("⚖️ HR Policy Co-Pilot")
st.caption("Ask questions about Singapore employment law — powered by your uploaded policy documents")

# ── API Key ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Settings")
    try:
        api_key = st.secrets["ANTHROPIC_API_KEY"]
        st.success("API key loaded from secrets ✓")
    except Exception:
        api_key = st.text_input("Anthropic API Key", type="password",
                                help="Get yours at console.anthropic.com")

    st.markdown("---")

    # ── PDF upload ───────────────────────────────────────────────────────────
    st.subheader("📂 Upload HR Policy PDFs")
    st.caption(
        "Upload any combination of:\n"
        "- Singapore Employment Act\n"
        "- Tripartite Guidelines\n"
        "- MOM Advisories\n"
        "- Your own company HR policies"
    )
    uploaded_pdfs = st.file_uploader(
        "Select PDF files", type=["pdf"], accept_multiple_files=True
    )

    if uploaded_pdfs and st.button("🔄 Build Knowledge Base", type="primary"):
        with st.spinner("Processing documents …"):

            def extract_text(file_bytes: bytes) -> str:
                # Try PyPDF2 first
                try:
                    reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
                    text = "".join(page.extract_text() or "" for page in reader.pages)
                    if text.strip():
                        return text
                except Exception:
                    pass
                # Fallback to PyMuPDF (handles more PDF types)
                try:
                    doc = fitz.open(stream=file_bytes, filetype="pdf")
                    return "".join(page.get_text() for page in doc)
                except Exception:
                    return ""

            all_chunks, all_metadata = [], []

            for pdf_file in uploaded_pdfs:
                text = extract_text(pdf_file.read())
                if not text.strip():
                    st.warning(f"No text extracted from {pdf_file.name} — skipping.")
                    continue
                words = text.split()
                for i in range(0, len(words), 200):
                    chunk = " ".join(words[i : i + 300])
                    if chunk:
                        all_chunks.append(chunk)
                        all_metadata.append({"source": pdf_file.name})

            if all_chunks:
                client = chromadb.Client()
                # Reset collection if it already exists
                try:
                    client.delete_collection("hr_policies")
                except Exception:
                    pass
                collection = client.create_collection("hr_policies")

                for i in range(0, len(all_chunks), 50):
                    batch = all_chunks[i : i + 50]
                    meta = all_metadata[i : i + 50]
                    ids = [str(j) for j in range(i, i + len(batch))]
                    collection.add(documents=batch, metadatas=meta, ids=ids)

                st.session_state["collection"] = collection
                st.session_state["messages"] = []
                st.success(
                    f"✓ {collection.count()} chunks loaded from "
                    f"{len(uploaded_pdfs)} PDF(s)"
                )
                st.rerun()
            else:
                st.error("No text could be extracted from any of the uploaded PDFs.")

    if st.session_state.get("collection"):
        if st.button("🗑️ Clear Chat History"):
            st.session_state["messages"] = []
            st.rerun()

# ── Initialise session state ─────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# ── Main area ────────────────────────────────────────────────────────────────
if not api_key:
    st.warning("👈 Enter your Anthropic API key in the sidebar to get started.")
    st.stop()

if "collection" not in st.session_state:
    st.info(
        "👈 Upload your HR policy PDFs in the sidebar and click **Build Knowledge Base** "
        "to get started.\n\n"
        "The original app was built with Singapore MOM and Tripartite Alliance documents "
        "(Employment Act, wrongful dismissal guidelines, FWA guidelines, retrenchment "
        "advisories, and more)."
    )
    st.stop()

# Display chat history
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if question := st.chat_input("Ask a question about HR policy …"):
    st.session_state["messages"].append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Searching policy documents …"):
            collection = st.session_state["collection"]
            results = collection.query(query_texts=[question], n_results=6)

            context = ""
            sources = []
            for doc_chunk, metadata in zip(
                results["documents"][0], results["metadatas"][0]
            ):
                context += f"\n---\n{doc_chunk}"
                sources.append(metadata["source"])

            claude = anthropic.Anthropic(api_key=api_key)
            response = claude.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1000,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "You are an HR policy assistant for Singapore employers. "
                            "Answer based ONLY on the context below. "
                            "Always cite which document your answer comes from. "
                            "If the answer is not in the context, say so clearly.\n\n"
                            f"Context:\n{context}\n\n"
                            f"Question: {question}"
                        ),
                    }
                ],
            )

            answer = response.content[0].text
            st.markdown(answer)

            unique_sources = sorted(set(sources))
            st.caption(f"📄 Sources: {' · '.join(unique_sources)}")

            st.session_state["messages"].append(
                {"role": "assistant", "content": answer}
            )
