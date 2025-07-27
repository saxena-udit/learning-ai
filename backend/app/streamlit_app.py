import streamlit as st
import pandas as pd
from app.chatbot.financial_chatbot import financial_chatbot
from app.loader.financial_data_loader import financial_data_loader
from app.utils.utils import utils
from app.utils.logger import get_logger
from app.nse.nse_indexes import NSEIndexes
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
        """Displays the sidebar with context-aware checkbox and file uploader."""
        logger.debug("Setting up sidebar components")
        with st.sidebar:  
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
        """Displays the main content area with question input and results."""
        logger.debug(f"Setting up main content with context_aware: {st.session_state[self.context_aware_key]}")
        
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
        """Display NSE indexes in the right column with categorization."""
        st.subheader("📈 NSE Indexes")

        # Get categorized data
        categorized_data = self.nse_indexes.get_categorized_data()
        index_types = self.nse_indexes.get_index_types()

        if categorized_data:
            # Create tabs for different views
            tab1, tab2, tab3 = st.tabs(["📊 All Indexes", "🏷️ By Category", "📈 Summary"])
            
            with tab1:
                # Display all indexes in a single table
                df_formatted, last_update = self.nse_indexes.get_data_for_display()
                if df_formatted is not None:
                    st.dataframe(
                        df_formatted,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Value": st.column_config.NumberColumn(
                                "Value",
                                help="Current index value",
                                format="₹%.2f"
                            ),
                            "Change %": st.column_config.NumberColumn(
                                "Change %",
                                help="Percentage change from previous close",
                                format="%.2f%%"
                            ),
                            "52W High": st.column_config.NumberColumn(
                                "52W High",
                                help="52-week high",
                                format="₹%.2f"
                            ),
                            "52W Low": st.column_config.NumberColumn(
                                "52W Low",
                                help="52-week low",
                                format="₹%.2f"
                            ),
                            "Down from High %": st.column_config.NumberColumn(
                                "Down from High %", 
                                help="Percentage down from 52-week high",
                                format="%.2f%%"
                            ),
                            "Up from Low %": st.column_config.NumberColumn(
                                "Up from Low %", 
                                help="Percentage up from 52-week low",
                                format="%.2f%%"
                            )
                        }
                    )
            
            with tab2:
                # Display categorized tables
                if index_types:
                    # Create a mapping of display names to actual values for the selectbox
                    type_labels = self.nse_indexes.get_index_type_labels()
                    type_display_names = [type_labels.get(t, t) for t in index_types]
                    type_mapping = dict(zip(type_display_names, index_types))
                    
                    selected_type_display = st.selectbox(
                        "Select Index Type:",
                        type_display_names,
                        key="index_type_selector"
                    )
                    
                    if selected_type_display:
                        selected_type = type_mapping[selected_type_display]
                        
                        if selected_type and selected_type in categorized_data:
                            sub_types = list(categorized_data[selected_type].keys())
                            
                            if sub_types:
                                # Create a mapping of display names to actual values for sub-types
                                sub_type_labels = self.nse_indexes.get_index_sub_type_labels()
                                sub_type_display_names = [sub_type_labels.get(st, st) for st in sub_types]
                                sub_type_mapping = dict(zip(sub_type_display_names, sub_types))
                                
                                selected_sub_type_display = st.selectbox(
                                    "Select Index Sub Type:",
                                    sub_type_display_names,
                                    key="index_sub_type_selector"
                                )
                                
                                if selected_sub_type_display:
                                    selected_sub_type = sub_type_mapping[selected_sub_type_display]
                                    
                                    if selected_sub_type and selected_sub_type in categorized_data[selected_type]:
                                        df_subset = categorized_data[selected_type][selected_sub_type]
                                        
                                        # Get display name for the category
                                        category_name = self.nse_indexes.get_display_name(selected_type, selected_sub_type)
                                        st.write(f"**{category_name}** ({len(df_subset)} indices)")
                                        
                                        st.dataframe(
                                            df_subset,
                                            use_container_width=True,
                                            hide_index=True,
                                            column_config={
                                                "Value": st.column_config.NumberColumn(
                                                    "Value",
                                                    help="Current index value",
                                                    format="₹%.2f"
                                                ),
                                                "Change %": st.column_config.NumberColumn(
                                                    "Change %",
                                                    help="Percentage change from previous close",
                                                    format="%.2f%%"
                                                ),
                                                "52W High": st.column_config.NumberColumn(
                                                    "52W High",
                                                    help="52-week high",
                                                    format="₹%.2f"
                                                ),
                                                "52W Low": st.column_config.NumberColumn(
                                                    "52W Low",
                                                    help="52-week low",
                                                    format="₹%.2f"
                                                ),
                                                "Down from High %": st.column_config.NumberColumn(
                                                    "Down from High %", 
                                                    help="Percentage down from 52-week high",
                                                    format="%.2f%%"
                                                ),
                                                "Up from Low %": st.column_config.NumberColumn(
                                                    "Up from Low %", 
                                                    help="Percentage up from 52-week low",
                                                    format="%.2f%%"
                                                )
                                            }
                                        )
                            else:
                                st.info(f"No sub-types found for {selected_type_display}")
                        else:
                            st.info("No data available for selected type")
                else:
                    st.info("No index types available")
            
            with tab3:
                # Display summary statistics
                st.write("**Index Categories Summary:**")
                
                summary_data = []
                type_labels = self.nse_indexes.get_index_type_labels()
                
                for index_type in categorized_data:
                    total_indices = 0
                    sub_types_count = len(categorized_data[index_type])
                    
                    for sub_type in categorized_data[index_type]:
                        total_indices += len(categorized_data[index_type][sub_type])
                    
                    # Use descriptive label for index type
                    display_type = type_labels.get(index_type, index_type)
                    
                    summary_data.append({
                        "Index Type": display_type,
                        "Sub Types": sub_types_count,
                        "Total Indices": total_indices
                    })
                
                if summary_data:
                    summary_df = pd.DataFrame(summary_data)
                    st.dataframe(
                        summary_df,
                        use_container_width=True,
                        hide_index=True
                    )
                
                
            # Refresh button and last update time
            if st.button("🔄 Refresh Indexes", key="refresh_indexes"):
                self.nse_indexes.force_refresh()
                st.rerun()

            # Get last update time
            _, last_update = self.nse_indexes.get_data_for_display()
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
        self.display_sidebar()
        # Create two columns: main (3/4) and right (1/4)
        main_col, right_col = st.columns([3, 1])
        with main_col:
            self.display_nse_indexes()
        with right_col:
            self.display_main_content()

if __name__ == "__main__":
    logger.info("Starting StreamlitApp")
    app = StreamlitApp()
    app.run() 