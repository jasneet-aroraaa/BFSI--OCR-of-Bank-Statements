import streamlit as st
import os
import io
import tempfile
import fitz  # PyMuPDF
from PIL import Image
import pandas as pd
import base64

from document_processor import DocumentProcessor
from visualizations import visualize_comparative_data, process_comparative_data, create_interactive_pie_chart

def main():
    st.set_page_config(page_title="Financial Document Analyzer", layout="wide")

    # Sidebar for navigation and configuration
    with st.sidebar:
        st.title("Financial Document Analyzer")

        # Document Type Selection
        document_types = [
            "Bank Statement",
            "Cheques",
            "Profit and Loss Statement",
            "Salary Slip",
            "Transaction History",
        ]
        selected_doc_type = st.selectbox("Select Document Type", document_types)

        # Graph Type Selection
        graph_types = [
            "Bar Chart",
            "Pie Chart",
        ]
        selected_graph_type = st.selectbox("Select Graph Type", graph_types)

        # Multiple File Upload Option
        upload_multiple = st.checkbox("Upload Multiple Files", value=False)

    # Main content area
    st.header(f"{selected_doc_type} Analysis")

    # File Upload in main content area
    uploaded_files = st.file_uploader(
        f"Upload {selected_doc_type} {'(Multiple Files)' if upload_multiple else ''}",
        type=["png", "jpg", "jpeg", "pdf"],
        accept_multiple_files=upload_multiple,
    )

    # Ensure uploaded_files is a list even for single file
    if not upload_multiple and uploaded_files:
        uploaded_files = [uploaded_files]

    processed_dfs = []
    processing_errors = []
    temp_image_paths = []

    if uploaded_files:
        processor = DocumentProcessor()

        for uploaded_file in uploaded_files:
            try:
                # Create a temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as temp_file:
                    temp_file.write(uploaded_file.getvalue())
                    temp_path = temp_file.name

                # Convert PDF to image if needed
                if os.path.splitext(uploaded_file.name)[1].lower() == ".pdf":
                    with fitz.open(stream=uploaded_file.getvalue(), filetype="pdf") as doc:
                        page = doc[0]
                        pix = page.get_pixmap()
                        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        temp_image_path = f"{temp_path}_page_0.png"
                        img.save(temp_image_path)
                        temp_image_paths.append(temp_image_path)
                else:
                    temp_image_path = temp_path
                    temp_image_paths.append(temp_image_path)

                # Extract parameters
                df, raw_text = processor.extract_parameters(temp_image_path, selected_doc_type)

                if df is not None:
                    # Ensure the DataFrame has the required columns
                    required_columns = ["Parameter", "Value"]
                    if all(col in df.columns for col in required_columns):
                        # Add Document column
                        df["Document"] = uploaded_file.name if len(uploaded_files) > 1 else "Default Document"
                        processed_dfs.append(df)
                    else:
                        st.warning(f"Extracted DataFrame for {uploaded_file.name} is missing required columns")

            except Exception as e:
                processing_errors.append(f"Error processing {uploaded_file.name}: {str(e)}")

        # Display errors if any
        if processing_errors:
            for error in processing_errors:
                st.error(error)

        # Process and visualize data
        if processed_dfs:
            # Combine dataframes
            combined_df = pd.concat(processed_dfs, ignore_index=True)

            # Display extracted parameters
            st.subheader("Extracted Parameters")
            st.dataframe(combined_df)

            # Visualization based on selected graph type
            if selected_graph_type == "Bar Chart":
                # Visualize comparative or single document bar chart
                figs = visualize_comparative_data(combined_df)

                if figs:
                    for fig in figs:
                        st.plotly_chart(fig, use_container_width=True)

            elif selected_graph_type == "Pie Chart":
                # Multi-document scenario
                if len(processed_dfs) > 1:
                    # Process to get common parameters
                    _, common_params = process_comparative_data(combined_df)

                    # Interactive Pie Chart Selection
                    st.subheader("Select Parameter for Pie Chart")
                    selected_param = st.selectbox(
                        "Choose a parameter to visualize",
                        common_params,
                    )

                    # Create and display interactive pie chart
                    pie_fig = create_interactive_pie_chart(combined_df, selected_param)
                    if pie_fig:
                        st.plotly_chart(pie_fig, use_container_width=True)

                else:
                    # Single document scenario
                    pie_fig = create_interactive_pie_chart(combined_df)
                    if pie_fig:
                        st.plotly_chart(pie_fig, use_container_width=True)

            # Download CSV option
            csv_buffer = io.StringIO()
            combined_df.to_csv(csv_buffer, index=False)
            st.download_button(
                label="Download Parameters CSV",
                data=csv_buffer.getvalue(),
                file_name=f"{selected_doc_type.lower().replace(' ', '_')}_parameters.csv",
                mime="text/csv",
            )

        # Image Query Section
        st.divider()
        st.subheader("Ask a Question About the Document")
        
        # Check if images were processed
        if temp_image_paths:
            # If multiple files, allow selection
            if len(temp_image_paths) > 1:
                selected_image = st.selectbox(
                    "Select Image to Query",
                    [f"Document {i+1}" for i in range(len(temp_image_paths))]
                )
                image_index = [f"Document {i+1}" for i in range(len(temp_image_paths))].index(selected_image)
                current_image_path = temp_image_paths[image_index]
            else:
                # If only one image, use it directly
                current_image_path = temp_image_paths[0]
                
            # Query input
            user_query = st.text_input("Enter your question about the document:")
            
            if user_query:
                try:
                    # Encode the image in Base64
                    with open(current_image_path, "rb") as img_file:
                        encoded_image = base64.b64encode(img_file.read()).decode("utf-8")
                        
                    # Use the processor or client to send the query
                    response = processor.client.chat.completions.create(
                        model=processor.model,
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": user_query},
                                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}}
                                ]
                            }
                        ],
                        max_tokens=500,
                        temperature=0.3
                    )
                    
                    # Display the AI's response
                    st.subheader("AI Response")
                    st.write(response.choices[0].message.content)
                
                except Exception as e:
                    st.error(f"Error processing query: {e}")
                    
        else:
            st.warning("Please upload a document to ask questions.")
            
        # Clean up temporary files
        for temp_path in temp_image_paths:
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except Exception as e:
                st.warning(f"Could not remove temporary file {temp_path}: {e}")

if __name__ == "__main__":
    main()