import streamlit as st
import os
from dotenv import load_dotenv
from rag_engine import RAGEngine

# Load environment variables for the OpenAI API Key
load_dotenv()

# Setup Streamlit page configuration for a polished UI
st.set_page_config(
    page_title="GigaCorp Support Agent",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Apply some custom CSS for better styling
st.markdown("""
<style>
    .stChatFloatingInputContainer {
        padding-bottom: 20px;
    }
    /* Removed the forced .main background-color to fix dark mode text visibility */
</style>
""", unsafe_allow_html=True)

# Initialize session state for RAG Engine and Chat History
if "rag_engine" not in st.session_state:
    with st.spinner("Initializing GigaCorp Support Agent..."):
        # Ensure API key is present before initializing the engine
        if not os.getenv("GROQ_API_KEY") or os.getenv("GROQ_API_KEY") == "your_groq_api_key_here":
            st.error("⚠️ GROQ_API_KEY is missing or invalid in the .env file. Please add your key and refresh the page.")
            st.stop()
        
        # The RAGEngine handles data loading, vector DB creation, and chain construction
        st.session_state.rag_engine = RAGEngine()

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am the GigaCorp Support Agent. How can I assist you today?"}
    ]

def render_ui():
    """Renders the Streamlit chat interface with polished formatting."""
    st.title("🤖 GigaCorp Customer Support")
    st.markdown(
        "Welcome to the GigaCorp support portal. Ask me anything about our shipping, "
        "returns, operating hours, or service tiers!"
    )
    st.divider()

    # Display chat history iteratively
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Handle incoming user input
    user_query = st.chat_input("Type your question here...")
    
    if user_query:
        # 1. Display user message in the chat container
        with st.chat_message("user"):
            st.markdown(user_query)
        
        # Add user message to session state memory
        st.session_state.messages.append({"role": "user", "content": user_query})

        # 2. Fetch and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                engine = st.session_state.rag_engine
                
                # Pass the history (excluding the current user query) to the chain
                response_data = engine.get_response(
                    user_query=user_query, 
                    chat_history=st.session_state.messages[:-1]
                )
                
                answer = response_data["answer"]
                sources = response_data["sources"]
                
                # Display the primary textual answer
                st.markdown(answer)
                
                # If there are sources retrieved, render them cleanly in an expander
                if sources:
                    with st.expander("📚 View Sources & Citations"):
                        for i, doc in enumerate(sources):
                            st.markdown(f"**Source {i+1}:**")
                            # We use st.info or st.code to visually differentiate the citation
                            st.info(doc.page_content.strip())
                            
        # 3. Add assistant message to session state memory
        st.session_state.messages.append({"role": "assistant", "content": answer})

if __name__ == "__main__":
    render_ui()
