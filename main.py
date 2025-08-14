import streamlit as st
import re
import google.generativeai as genai
import streamlit.components.v1 as components
import json
import base64

def rerun():
    from streamlit.runtime.scriptrunner import RerunException
    from streamlit.runtime.scriptrunner import RerunData
    raise RerunException(RerunData())

# Configure Gemini API
genai.configure(api_key="AIzaSyDHKNVVFmw8qIaZiBFEz5xwV8ZxXQ0VecA")
model = genai.GenerativeModel("gemini-2.5-pro")

st.title("AI Proposal Generator Interactive Prototype")

def highlight_html(text: str) -> str:
    """Wraps bprr...bprr sections in <mark> tags for highlighting."""
    return re.sub(r'bprr(.*?)bprr', r'<mark>\1</mark>', text, flags=re.DOTALL)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": (
                "You are responsible for selecting an RFQ which aligns with a users stated machines, creating a proposal based on the chosen RFQ, and then finding risks present in a user edited version of the prompt."
                "These different responsibilities will be designated based on the number which comes at the start of the prompt."
                "A 1 will mean you are supposed to choose one of the RFQs based on input machines. Provide a short reasoning for why it was selected, and then put the actual proposal under that. Alternatively, the user may input a RFQ, in which case you should just generate a proposal based on the input RFQ and not any of the other options."
                "A 2 will mean you are supposed to create a proposal based on the input RFQ."
                "A 3 will mean you are supposed to find risks present in the document, and presenting them in the following format:"
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
                "Always seperate the original RFQ and Explanation of Risks with three ***."
                "The number of explanations should be equal to the number of highlights. Only one explanation per highlight."
                "Additionally, a user may request a summary or explanation of any section of the proposal."
                "Do not use elements such as tables, graphs, or dotted lists."
                "Always end with a sign off type of thing with name and company name and similar things, not filled in. Always give a response, never give nothing"
                "These are the ten RFQs which will be used: 1. RFQ for 200 ruggedized field laptops (MIL-STD-810H, 72-hour battery life, integrated GPS, 45-day delivery); 2. RFQ for 400 tactical UAV reconnaissance drones (thermal imaging, encrypted comms, 120-minute flight time, 90-day delivery); 3. RFQ for 1,500 flame-resistant combat uniforms (NFPA 2112 compliant, moisture-wicking, 60-day delivery); 4. RFQ for 250 portable satellite communication terminals (global coverage, MIL-STD-188-164A, 75-day delivery); 5. RFQ for 600 armored tactical transport cases (NIJ Level III ballistic protection, waterproof to IP68, 50-day delivery); 6. RFQ for 350 high-output portable water purification units (capable of 1,000 liters/hour, NSF/ANSI Standard 53, 40-day delivery); 7. RFQ for 800 advanced combat helmets (NIJ Level IIIA, integrated comms mount, 90-day delivery); 8. RFQ for 500 tactical field medical kits (NSN compliant, waterproof case, 30-day delivery); 9. RFQ for 1,200 long-range encrypted handheld radios (AES-256 encryption, 40-mile range, MIL-STD-810G, 60-day delivery); 10. RFQ for 100 portable solar-powered field generators (5 kW output, foldable panels, MIL-STD-810G, 70-day delivery)"
            )
        }
    ]

if "step" not in st.session_state:
    st.session_state.step = 1

# Step 1
if st.session_state.step == 1:
    st.header("Step 1: Enter your machines or RFQ")
    user_input = st.text_area("Enter your machines or RFQ for proposal:", height=150)

    if st.button("Submit and Continue"):
        if user_input.strip():
            st.session_state.messages.append({"role": "user", "content": user_input})
            gemini_prompt = "\n".join([f"{msg['role']}: 1{msg['content']}" for msg in st.session_state.messages])
            response = model.generate_content(gemini_prompt)
            assistant_text = response.candidates[0].content.parts[0].text
            st.session_state.messages.append({"role": "assistant", "content": assistant_text})
            st.session_state.step = 2
            rerun()
        else:
            st.warning("Please enter some text before continuing.")

# Step 2
elif st.session_state.step == 2:
    st.header("Step 2: Review and edit the proposal")

    last_assistant_message = ""
    for msg in reversed(st.session_state.messages):
        if msg["role"] == "assistant":
            last_assistant_message = msg["content"]
            break

    highlighted_text = highlight_html(last_assistant_message)
    proposal_text = last_assistant_message

    col1, col2 = st.columns(2)

    with col1:
        edited_text = st.text_area("Edit Proposal Here", value=proposal_text, height=3000)

    with col2:
        st.markdown(highlighted_text, unsafe_allow_html=True)

    col3, col4 = st.columns(2)
    with col4:
        if st.button("Finalize Document"):
            final_text = re.sub(r'bprr(.*?)bprr', r'\1', edited_text.replace("*", ""), flags=re.DOTALL)
            final_text = final_text.replace("***", "\n\n")
            st.session_state.messages.append({"role": "assistant", "content": "Finalized Document:\n\n" + final_text})
            st.session_state.step = 3
            rerun()
        if st.button("🚩"):
            st.warning("This response has been flagged for review")

# Step 3
elif st.session_state.step == 3:
    st.header("Step 3: Finalized Document")

    last_assistant_message = ""
    for msg in reversed(st.session_state.messages):
        if msg["role"] == "assistant":
            last_assistant_message = msg["content"]
            break

    st.text_area("Final Document", value=last_assistant_message, height=600)

    # Ensure we copy exactly the finalized text
    final_text = last_assistant_message
    encoded_text = base64.b64encode(final_text.encode()).decode()

    copy_button_html = f"""
    <button style="padding:8px 16px; background:#4CAF50; color:white; border:none;
    border-radius:6px; cursor:pointer;"
    onclick="
        (async () => {{
            const text = atob('{encoded_text}');
            await navigator.clipboard.writeText(text);
            alert('Copied to clipboard!');
        }})()
    ">
    Copy Final Text
    </button>
    """

    components.html(copy_button_html, height=50)