import streamlit as st
from pydantic import BaseModel
from langgraph.graph import StateGraph, START, END
from typing import Optional, List, Dict
from IPython.display import Image, display
from langchain_core.runnables.graph import MermaidDrawMethod
import requests

def fetch_interest_rate():
    try:
        response = requests.get("https://www.bankbazaar.com/personal-loan-interest-rate.html")
        if response.status_code == 200:
            return "Personal loan interest rates vary by bank. Please check official bank websites for the latest rates."
    except Exception as e:
        return "Could not fetch the interest rate. Please check with your bank."


def displayGraph(graph):
    image = graph.get_graph().draw_mermaid_png(
        draw_method=MermaidDrawMethod.API,
    )
    st.image(image, caption='Loan Application Process')

class LoanApplicationState(BaseModel):
    name: Optional[str] = None
    salary: Optional[float] = None
    pan: Optional[str] = None
    loan_amount: Optional[float] = None
    tenure: Optional[int] = None
    status: str = "pending"
    messages: List[Dict[str, str]] = [{"role": "system", "content": "Loan Application Process Started"}]

def handle_user_state(state: LoanApplicationState) -> LoanApplicationState:
    missing_details = [field for field in state.model_fields if getattr(state, field) is None and field != "status"]
    if missing_details:
        state.messages.append({"role": "assistant", "content": f"Please provide: {', '.join(missing_details)}."})
        state.status = "pending"
    else:
        state.messages.append({"role": "assistant", "content": "All details collected. Validating..."})
        state.status = "validating"
    return state

def validate_application(state: LoanApplicationState) -> LoanApplicationState:
    if state.pan and (not state.pan.isalnum() or len(state.pan) != 10):
        state.messages.append({"role": "assistant", "content": "PAN number is invalid."})
        state.status = "invalid_pan"
    elif state.salary and state.salary > 50000:
        state.status = "approved"
        state.messages.append({"role": "assistant", "content": "Your loan is approved!"})
    elif state.salary and (state.salary > 30000 and state.salary <= 50000):
        state.status = "escalated"
        state.messages.append({"role": "assistant", "content": "Your application has been escalated for review."})
    else:
        state.status = "rejected"
        state.messages.append({"role": "assistant", "content": "Your loan is rejected."})
    return state

def check_next_step(state: LoanApplicationState):
    if state.status == "validating":
        return "validate_application"
    elif state.status == "invalid_pan":
        return "handle_user_input"
    elif state.status == "pending":
        return "handle_user_input"
    elif state.status in ["approved", "rejected", "escalated"]:
        return END

def create_graph():
    graph_builder = StateGraph(LoanApplicationState)
    graph_builder.add_node("handle_user_input", handle_user_state)
    graph_builder.add_node("validate_application", validate_application)
    graph_builder.add_edge(START, "handle_user_input")
    graph_builder.add_conditional_edges("handle_user_input", check_next_step)
    graph_builder.add_conditional_edges("validate_application", check_next_step)
    return graph_builder.compile()

# Streamlit UI
st.set_page_config(page_title = "Loan Eligibility Checker", page_icon="Streamlit/ey-logo-black.png")
with st.container(border=True, height=380, key="con1"):
    col1, col2, col3 = st.columns([3,5,3])
    with col1 : st.image("Streamlit/ey-logo-black.png", width=100)

    with col2: st.write("")
    with col3: st.write("")

    st.title("Loan Eligibility Checker")
    user_query = st.text_input("Ask a question or enter loan details")

if user_query:
    if user_query.lower() in ["hi", "hello", "hey"]:
        st.write("Hello! How can I assist you today?")
    elif any(keyword in user_query.lower() for keyword in ["interest rate", "rate of interest"]):

        st.write(fetch_interest_rate())
        st.write("Please enter your details to check your eligibility for loan:")
        name = st.text_input("Enter your name")
        salary = st.number_input("Enter your salary", min_value=0)
        pan = st.text_input("Enter your PAN number")
        loan_amount = st.number_input("Enter loan amount", min_value=0)
        tenure = st.number_input("Enter loan tenure (months)", min_value=1, step=1)

        if st.button("Check Eligibility"):
            user_inputs = LoanApplicationState(name=name, salary=salary, pan=pan, loan_amount=loan_amount, tenure=tenure)
            graph = create_graph()
            state = user_inputs
    
        for output in graph.stream(state):
            state = LoanApplicationState(**output[list(output.keys())[0]])
    
            st.subheader("Loan Status: " + state.status.upper())
        for msg in state.messages:
            st.write(f"{msg['role'].capitalize()}: {msg['content']}")

    else:
        st.write("Please rephrase your query.")


# Custom CSS for background color
st.markdown("""
    <style>
    .stApp {
        background-color: darkgrey;
    }
</style>
""", unsafe_allow_html=True)

    
    #displayGraph(graph)