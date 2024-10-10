import streamlit as st
import requests
import pandas as pd

st.set_page_config(layout="wide")

# Streamlit UI setup
st.title("Type your query Below")

# Dropdown for selecting collections
collections = {
    "Leads": "el_leads",
    "Orders": "el_orders",
    "Travel Management": "travel_plan"
}

selected_collection = st.selectbox("Select Collection", options=list(collections.keys()))

# Input from the user
user_input = st.text_input("Enter your query in natural language:")

# Submit button
if st.button("Submit"):
    # Display the query input
    st.write(f"Query: {user_input}")
    st.write(f"Selected Collection: {selected_collection}")

    # Send the query to the backend API along with the selected collection
    try:
        response = requests.post(
            "http://127.0.0.1:5000/query", 
            json={"query": user_input, "collection": collections[selected_collection]}
        )
        response_json = response.json()

        # Check for error in the response
        if 'error' in response_json:
            st.error(f"Error: {response_json['error']} - Please try again.")
        else:
            # Convert the JSON response into a DataFrame for table display
            if isinstance(response_json, list):
                df = pd.DataFrame(response_json)
                st.dataframe(df)
            else:
                st.json(response_json)
    except Exception as e:
        st.error("Please try again.")
