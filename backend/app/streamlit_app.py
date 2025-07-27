import streamlit as st
import pandas as pd
from app.chatbot.financial_chatbot import financial_chatbot
from app.loader.financial_data_loader import financial_data_loader
from app.utils.utils import utils
from app.utils.logger import get_logger
from app.nse.nse_indexes import NSEIndexes
from app.nse.nse_formatter import NSEFormatter
import time

# Get logger for this module
logger = get_logger("streamlit_app")

class StreamlitApp:
    def __init__(self):
        # Initialize Streamlit settings
        logger.info("Initializing StreamlitApp")
        st.set_page_config(page_title=f'Langchain Demo [model:{utils.model_name}]', layout="wide")
        self.context_aware_key = "context_aware"
        self.question_key = "question_input"
        self.input_text = ""
        self.ticker_key = "ticker_input"
        # Initialize session state
        if self.context_aware_key not in st.session_state:
            st.session_state[self.context_aware_key] = True
            logger.debug("Initialized context_aware session state to True")
            
        if self.question_key not in st.session_state:
            st.session_state[self.question_key] = ""
            logger.debug("Initialized question_input session state to empty string")

        if self.input_text not in st.session_state:
            st.session_state[self.input_text] = ""
            logger.debug("Initialized input_text session state to empty string")
            
        if self.ticker_key not in st.session_state:
            st.session_state[self.ticker_key] = ""
            logger.debug("Initialized ticker_input session state to empty string")
            
        # File uploader state
        if "file_uploader_key" not in st.session_state:
            st.session_state.file_uploader_key = 0
        try:
            self.chatbot = financial_chatbot
            self.financial_data_loader = financial_data_loader
            self.nse_indexes = NSEIndexes()
            self.nse_formatter = NSEFormatter()
            logger.info("Components initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing StreamlitApp components: {str(e)}", exc_info=True)
            st.error(f"Error initializing application: {str(e)}")

    def flip_context_aware(self):
        logger.info(f"Toggling context_aware from {st.session_state[self.context_aware_key]} to {not st.session_state[self.context_aware_key]}")
        st.session_state[self.context_aware_key] = not st.session_state[self.context_aware_key]
    
    def process_question(self):
        """Process the question from session state and clear input after processing"""
        input_text = st.session_state[self.question_key]
        st.session_state.input_text = input_text
        if input_text:
            logger.info(f"Processing question: '{input_text[:50]}...'")
            retrieval_chain_ = self.chatbot.retrieval_chain(st.session_state[self.context_aware_key])
            
            try:
                result = retrieval_chain_.invoke({"question": input_text})
                logger.info("Successfully processed question")
                
                if isinstance(result, dict):
                    logger.debug("Result is a dictionary, displaying as table")
                    st.session_state.last_result = pd.DataFrame(result)
                    st.session_state.result_type = "table"
                else:
                    logger.debug("Result is not a dictionary, displaying as text")
                    st.session_state.last_result = result
                    st.session_state.result_type = "text"
            except Exception as e:
                logger.error(f"Error processing question: {str(e)}", exc_info=True)
                st.session_state.last_result = f"Error processing question: {str(e)}"
                st.session_state.result_type = "error"
        
        # Clear the input field after processing
        st.session_state[self.question_key] = ""
        
    def process_ticker(self):
        """Process the ticker and clear input after processing"""
        ticker = st.session_state[self.ticker_key]
        if ticker:
            logger.info(f"Loading context for ticker: {ticker}")
            try:
                urls = self.financial_data_loader.load_vector_db(tickers=[ticker])
                logger.info(f"Loaded {len(urls)} PDFs for ticker: {ticker}")
                st.success(f"Loaded {len(urls)} PDFs for {ticker}")
                # Display loaded URLs as bullet points
                if urls and len(urls) > 0:
                    for url in urls:
                        st.markdown(f"• {url}")
            except Exception as e:
                logger.error(f"Error loading ticker context: {str(e)}", exc_info=True)
                st.error(f"Error loading ticker context: {str(e)}")
            
            # Clear ticker input after processing
            st.session_state[self.ticker_key] = ""

    def reset_file_uploader(self):
        """Reset the file uploader by incrementing its key"""
        st.session_state.file_uploader_key += 1

    def display_sidebar(self):
        """Displays the sidebar controls with context-aware checkbox and file uploader."""
        logger.debug("Setting up sidebar components")
        
        st.checkbox(
            "Context Aware",
            value=st.session_state[self.context_aware_key],
            key="check",
            on_change=self.flip_context_aware
        )
        uploaded_file = st.file_uploader("Add more context", type="pdf", key=f"uploader_{st.session_state.file_uploader_key}")
        if uploaded_file:
            logger.info(f"Processing uploaded PDF: {uploaded_file.name}")
            try:
                splits = self.financial_data_loader.load_and_split_pdf(uploaded_file)
                logger.info(f"Successfully processed PDF with {len(splits)} chunks")
                st.success(f"Processed PDF with {len(splits)} chunks")
                # Reset file uploader after successful processing
                self.reset_file_uploader()
            except Exception as e:
                logger.error(f"Error processing PDF: {str(e)}", exc_info=True)
                st.error(f"Error processing PDF: {str(e)}")
        
        st.text_input("Add ticker context", key=self.ticker_key, on_change=self.process_ticker)
    
    def display_main_content(self):
        """Displays the main content area with question input and results, including sidebar functionality."""
        logger.debug(f"Setting up main content with context_aware: {st.session_state[self.context_aware_key]}")
        
        # Create two columns: sidebar (1/4) and main content (3/4)
        sidebar_col, main_col = st.columns([1, 3])
        
        with sidebar_col:
            self.display_sidebar()
            
        with main_col:
            # Use the callback to process and clear input
            st.text_input("Question:", key=self.question_key, on_change=self.process_question)
            
            # Display the last result if it exists
            if hasattr(st.session_state, 'last_result'):
                st.write(f"Question: {st.session_state.input_text}")
                if st.session_state.result_type == "table":
                    st.table(st.session_state.last_result)
                elif st.session_state.result_type == "error":
                    st.error(st.session_state.last_result)
                else:
                    st.write(st.session_state.last_result)

    def display_nse_indexes(self):
        """Display NSE indexes in the first tab with categorization."""
        st.subheader("📈 NSE Indexes")

        # Get raw data
        raw_data, last_update = self.nse_indexes.get_raw_data()
        
        if raw_data is not None and not raw_data.empty:
            # Get categorized data using formatter
            index_types = self.nse_indexes.get_index_types()
            
            # Display all indexes in a single table with filtering options
            st.write("**All NSE Indexes**")
            
            # Add filtering options
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # Filter by index type
                type_labels = self.nse_indexes.get_index_type_labels()
                type_display_names = [type_labels.get(t, t) for t in index_types]
                type_mapping = dict(zip(type_display_names, index_types))
                
                selected_type_display = st.selectbox(
                    "Filter by Index Type:",
                    ["All Types"] + type_display_names,
                    key="index_type_filter"
                )
            
            with col2:
                # Filter by sub type (if a type is selected)
                sub_type_filter = None
                if selected_type_display and selected_type_display != "All Types":
                    selected_type = type_mapping[selected_type_display]
                    sub_types = self.nse_indexes.get_index_sub_types(selected_type)
                    
                    if sub_types:
                        sub_type_labels = self.nse_indexes.get_index_sub_type_labels()
                        sub_type_display_names = [sub_type_labels.get(st, st) for st in sub_types]
                        sub_type_mapping = dict(zip(sub_type_display_names, sub_types))
                        
                        selected_sub_type_display = st.selectbox(
                            "Filter by Sub Type:",
                            ["All Sub Types"] + sub_type_display_names,
                            key="index_sub_type_filter"
                        )
                        
                        if selected_sub_type_display and selected_sub_type_display != "All Sub Types":
                            sub_type_filter = sub_type_mapping[selected_sub_type_display]
            
            # Format the data using formatter
            df_formatted = self.nse_formatter.format_data_for_display(raw_data)
            
            if not df_formatted.empty:
                # Apply filters if selected
                if selected_type_display and selected_type_display != "All Types":
                    selected_type = type_mapping[selected_type_display]
                    # Filter by index type
                    filtered_indices = raw_data[raw_data['indexType'] == selected_type]['index'].tolist()
                    df_formatted = df_formatted[df_formatted['Index'].isin(filtered_indices)]
                    
                    # Apply sub-type filter if selected
                    if sub_type_filter:
                        sub_type_indices = raw_data[
                            (raw_data['indexType'] == selected_type) & 
                            (raw_data['indexSubType'] == sub_type_filter)
                        ]['index'].tolist()
                        df_formatted = df_formatted[df_formatted['Index'].isin(sub_type_indices)]
                
                # Create column configuration for all columns
                column_config = self.nse_formatter.create_column_config()
                
                # Display the data with all columns visible
                st.dataframe(
                    df_formatted,
                    use_container_width=True,
                    hide_index=True,
                    column_config=column_config
                )
                
                # Display summary information
                st.write(f"**Showing {len(df_formatted)} indices**")
                st.info("💡 Use the view icon (👁️) in the dataframe to show/hide columns as needed")
                
                # Get and display summary statistics
                stats = self.nse_formatter.get_summary_statistics(df_formatted)
                if stats:
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if 'average_change' in stats:
                            st.metric("Average Change %", f"{stats['average_change']:.2f}%")
                    
                    with col2:
                        if 'positive_count' in stats:
                            st.metric("Positive Changes", stats['positive_count'])
                    
                    with col3:
                        if 'negative_count' in stats:
                            st.metric("Negative Changes", stats['negative_count'])
            
            # Refresh button and last update time
            if st.button("🔄 Refresh Indexes", key="refresh_indexes"):
                self.nse_indexes.force_refresh()
                st.rerun()

            # Get last update time
            if last_update:
                last_update_time = time.strftime('%H:%M:%S', time.localtime(last_update))
                st.caption(f"Last updated: {last_update_time}")
        else:
            st.warning("Unable to fetch NSE indexes data. Please try again later.")
            if st.button("🔄 Refresh Indexes", key="refresh_indexes"):
                self.nse_indexes.force_refresh()
                st.rerun()


    def run(self):
        """Runs the Streamlit application."""
        logger.info("Running StreamlitApp")
        
        # Create two tabs: NSE Indexes and Chatbot
        tab1, tab2 = st.tabs(["📈 NSE Indexes", "🤖 Financial Chatbot"])
        
        with tab1:
            self.display_nse_indexes()
            
        with tab2:
            self.display_main_content()

if __name__ == "__main__":
    logger.info("Starting StreamlitApp")
    app = StreamlitApp()
    app.run() 