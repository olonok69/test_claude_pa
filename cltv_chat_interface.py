import streamlit as st
from langchain_core.messages import HumanMessage
from cltv_ai_agent import create_cltv_agent

def main():
    st.set_page_config(
        page_title="CLTV AI Chat Assistant",
        page_icon="🏠",
        layout="wide"
    )
    
    st.title("💬 CLTV AI Chat Assistant")
    st.markdown("Chat with an AI expert in mortgage lending and CLTV analysis")
    
    # Initialize session state for chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.graph = create_cltv_agent()
        st.session_state.config = {"configurable": {"thread_id": "cltv_chat"}}
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me about CLTV, DTI, loan qualification, or mortgage analysis..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate AI response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                try:
                    result = st.session_state.graph.invoke(
                        {"messages": [HumanMessage(content=prompt)]},
                        st.session_state.config
                    )
                    response = result["messages"][-1].content
                    st.markdown(response)
                    
                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                except Exception as e:
                    error_msg = f"I apologize, but I encountered an error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    # Sidebar with example prompts
    st.sidebar.header("💡 Example Questions")
    
    example_prompts = [
        "Analyze a borrower with $500K property, $400K loan, $8K income, 740 credit score",
        "What CLTV ratio is considered good for conventional loans?", 
        "Compare loan scenarios for different down payment amounts",
        "Calculate DTI for $6K income, $1K debts, $2.5K housing payment",
        "What are the PMI requirements for conventional loans?",
        "Analyze a cash-out refinance scenario",
        "What compensating factors help with high DTI ratios?"
    ]
    
    for prompt in example_prompts:
        if st.sidebar.button(prompt, key=prompt):
            # Add the prompt to chat
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.rerun()

if __name__ == "__main__":
    main()