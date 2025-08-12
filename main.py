import streamlit as st
import re
import google.generativeai as genai

# Configure Gemini API
genai.configure(api_key="YOUR_API_KEY")
model = genai.GenerativeModel("gemini-2.5-pro")

st.title("Risk Flagging Chatbot (Gemini 2.5)")

def highlight_html(text: str) -> str:
    """Wraps bprr...bprr sections in <mark> tags for highlighting."""
    return re.sub(r'bprr(.*?)bprr', r'<mark>\1</mark>', text)

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": (
                "You are responsible for identifying and highlighting potential risk areas in a contract or document. "
                "Risks may include, but are not limited to:\n"
                "- Missing compliance clauses\n"
                "- Unusual or unclear delivery terms\n"
                "- Payment issues\n"
                "- Legal or regulatory concerns\n"
                "- Security or performance liabilities\n\n"
                "Your tasks are as follows:\n"
                "1. If no risks are found: Output the original prompt text unchanged. Then, add two line breaks and write: No errors were found.\n"
                "2. If risks are found: Highlight each risky section by wrapping it with the exact tags bprr<text>bprr (no space). Return the entire prompt with the risky sections highlighted this way.\n"
                "3. Below the full edited prompt, write a numbered list explaining why each highlighted section was flagged, in the same order they appear in the text.\n"
                "4. Do not flag placeholder text (e.g., [Insert Date], [Company Name], etc.).\n"
                "5. Do not highlight or change section titles, even if the section is risky—only highlight content.\n"
                "6. After presenting the results, ask the user: Would you like to make changes to any of the highlighted sections? "
                "If so, please specify what to change.\n"
                "7. If the user replies 'no' to all changes, follow up with: Would you like to finalize the document? "
                "If the user answers 'yes', return the finalized version without any bprr tags.\n"
                "8. If the user wants changes, apply them and continue checking for risk until they confirm finalization."
            )
        }
    ]

# Display chat history (only user inputs so far)
for message in st.session_state.messages:
    if message["role"] == "user":
        with st.chat_message("user"):
            st.markdown(message["content"])

# Input box remains at top
prompt = st.chat_input("Please input your contract for review")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    gemini_prompt = "\n".join(
        [f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages]
    )

    response = model.generate_content(gemini_prompt)
    text = response.text

    # Separate highlighted text from explanations
    if "\n" in text:
        parts = text.split("\n", 1)
        highlighted_part = parts[0]
        explanation_part = parts[1]
    else:
        highlighted_part = text
        explanation_part = ""

    highlighted_text = highlight_html(highlighted_part)

    # Show results side-by-side
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Edit Proposal Here")
        plain_text = re.sub(r'<.*?>', '', highlighted_text)
        st.text_area(plain_text, height=300)

    with col2:
        st.subheader("Explanations")
        st.markdown(highlighted_text, unsafe_allow_html=True)

    st.session_state.messages.append(
        {"role": "assistant", "content": highlighted_text + "\n\n" + explanation_part}
    )