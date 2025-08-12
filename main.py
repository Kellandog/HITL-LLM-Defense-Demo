import os
from langchain_ollama import ChatOllama
import streamlit as st
import re

from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

llm = ChatOllama(model="llama3")

st.title("Risk Flagging Chatbot")

def highlight_html(text: str) -> str:
    # Replace bbbbb...bbbbb with <mark>...</mark> for Streamlit highlight
    return re.sub(r'bprr(.*?)bprr', r'<mark>\1</mark>', text)

if "messages" not in st.session_state:
    st.session_state.messages = [
        SystemMessage(
            content="You are responsible for identifying and highlighting potential risk areas in a contract or document. Risks may include, but are not limited to: Missing compliance clauses Unusual or unclear delivery terms Payment issues Legal or regulatory concerns Security or performance liabilities Your tasks are as follows: If no risks are found: Output the original prompt text unchanged. Then, add two line breaks and write: No errors were found. If risks are found: Highlight each risky section by wrapping it with the exact tags bprr<text>bprr (no space). Return the entire prompt with the risky sections highlighted this way. Below the full edited prompt, write a numbered list explaining why each highlighted section was flagged, in the same order they appear in the text. Do not flag placeholder text (e.g., [Insert Date], [Company Name], etc.). Do not highlight or change section titles, even if the section is risky—only highlight content. After presenting the results, ask the user: Would you like to make changes to any of the highlighted sections? If so, please specify what to change. If the user replies 'no' to all changes, follow up with: Would you like to finalize the document? If the user answers 'yes', return the finalized version without any bprr tags. If the user wants changes, apply them and continue checking for risk until they confirm finalization.")
    ]

# Display chat messages from history
for message in st.session_state.messages:
    if isinstance(message, HumanMessage):
        with st.chat_message("user"):
            st.markdown(message.content)
    elif isinstance(message, AIMessage):
        with st.chat_message("assistant"):
            # Allow HTML for highlights
            st.markdown(message.content, unsafe_allow_html=True)

prompt = st.chat_input("Please input your contract for review")

if prompt:
    # Add user message
    st.session_state.messages.append(HumanMessage(content=prompt))

    with st.chat_message("user"):
        st.markdown(prompt)

    # Invoke LLM and get AIMessage
    response = llm.invoke(st.session_state.messages)  # AIMessage object

    # Extract text content
    text = response.content

    # Highlight the risky sections in HTML for Streamlit
    highlighted_text = highlight_html(text)

    with st.chat_message("assistant"):
        st.markdown(highlighted_text, unsafe_allow_html=True)

    # Append AI message with raw text (not HTML) so history stays clean
    st.session_state.messages.append(AIMessage(content=text))