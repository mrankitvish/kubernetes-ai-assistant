import streamlit as st
import requests
import json

# --- Configuration ---
# Replace with the actual URL of your FastAPI backend
FASTAPI_BACKEND_URL = "http://localhost:8000"
CHAT_ENDPOINT = f"{FASTAPI_BACKEND_URL}/chat/stream"

# --- Streamlit UI Setup ---
st.set_page_config(page_title="Kubernetes Agent Chat", page_icon="🤖")
st.title("🤖 Kubernetes Agent Chat")

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize session_id in session state
if "session_id" not in st.session_state:
    st.session_state.session_id = None

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("What can I help you with in Kubernetes?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Prepare payload for FastAPI backend
    payload = {"message": prompt}
    if st.session_state.session_id:
        payload["session_id"] = st.session_state.session_id

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(CHAT_ENDPOINT, json=payload, stream=True, headers={"x-api-key": "kjsfjds"})
                response.raise_for_status()  # Raise an exception for HTTP errors

                # Use st.empty() to create a container for the streamed response
                message_placeholder = st.empty()
                full_response = ""

                # Stream the response content (SSE format)
                # Use a simple line-by-line approach for SSE
                lines = response.iter_lines(decode_unicode=True)
                
                # Read the first line to get the session ID
                try:
                    first_line = next(lines)
                    if first_line.startswith("data: "):
                        try:
                            session_data = json.loads(first_line[len("data: "):])
                            if "session_id" in session_data:
                                st.session_state.session_id = session_data["session_id"]
                        except json.JSONDecodeError:
                            # Handle case where first line is not valid JSON
                            pass # Or log an error
                except StopIteration:
                    # Handle empty response
                    st.error("Empty response from the backend.")
                    pass # Exit the try block if StopIteration occurs
                
                # Process the rest of the streamed chunks
                for line in lines:
                    if line.startswith("data: "):
                        content = line[len("data: "):]
                        full_response += content
                        # Update the message in the UI in real-time
                        message_placeholder.markdown(full_response + "▌")

                # Final update to remove the cursor
                message_placeholder.markdown(full_response)

                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": full_response})

            except requests.exceptions.ConnectionError:
                st.error("Could not connect to the FastAPI backend. Please ensure it's running.")
            except requests.exceptions.RequestException as e:
                st.error(f"Error communicating with the backend: {e}")