import pandas as pd
import streamlit as st
from typing import Dict, Optional, Tuple, List
try:
    from utils.logger import get_logger
except ImportError:
    try:
        from app.utils.logger import get_logger
    except ImportError:
        import logging
        def get_logger(name):
            return logging.getLogger(name)

logger = get_logger("nse_formatter")

class NSEFormatter:
    """Class to handle formatting of NSE indexes data for display"""
    
    def __init__(self):
        self.column_mapping = {
            'index': 'Index',
            'last': 'Value',
            'variation': 'Variation',
            'percentChange': 'Change %',
            'high': 'High',
            'low': 'Low',
            'open': 'Open',
            'previousClose': 'Prev Close',
            'yearHigh': '52W High',
            'yearLow': '52W Low',
            'downFromHighPct': 'Down from High %',
            'upFromLowPct': 'Up from Low %',
            'timeVal': 'Time',
            'indexType': 'Index Type',
            'indexSubType': 'Index Sub Type'
        }
        
        self.numeric_columns = [
            'Value', 'Variation', 'Change %', 'High', 'Low', 'Open', 
            'Prev Close', '52W High', '52W Low', 'Down from High %', 'Up from Low %'
        ]

    def format_data_for_display(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        """Format raw NSE data for display."""
        if raw_data is None or raw_data.empty:
            return pd.DataFrame()
        
        try:
            # Select and rename columns
            available_columns = [col for col in self.column_mapping.keys() if col in raw_data.columns]
            df_formatted = raw_data[available_columns].copy()
            df_formatted = df_formatted.rename(columns=self.column_mapping)
            
            # Convert numeric columns
            for col in self.numeric_columns:
                if col in df_formatted.columns:
                    df_formatted[col] = df_formatted[col].astype(str).str.replace(',', '').apply(
                        lambda x: pd.to_numeric(x, errors='coerce')
                    )
            
            return df_formatted
            
        except Exception as e:
            logger.error(f"Error formatting data for display: {str(e)}", exc_info=True)
            return pd.DataFrame()

    def get_column_definitions(self) -> Dict[str, Dict[str, any]]:
        """Get column definitions for Streamlit column configuration."""
        return {
            'Index': {'type': 'text', 'help': 'Index name'},
            'Value': {'type': 'number', 'format': '₹%.2f', 'help': 'Current index value'},
            'Variation': {'type': 'number', 'format': '₹%.2f', 'help': 'Absolute change from previous close', 'hidden': True},
            'Change %': {'type': 'number', 'format': '%.2f%%', 'help': 'Percentage change from previous close'},
            'High': {'type': 'number', 'format': '₹%.2f', 'help': 'Day high', 'hidden': True},
            'Low': {'type': 'number', 'format': '₹%.2f', 'help': 'Day low', 'hidden': True},
            'Open': {'type': 'number', 'format': '₹%.2f', 'help': 'Opening price', 'hidden': True},
            'Prev Close': {'type': 'number', 'format': '₹%.2f', 'help': 'Previous closing price', 'hidden': True},
            '52W High': {'type': 'number', 'format': '₹%.2f', 'help': '52-week high'},
            '52W Low': {'type': 'number', 'format': '₹%.2f', 'help': '52-week low'},
            'Down from High %': {'type': 'number', 'format': '%.2f%%', 'help': 'Percentage down from 52-week high'},
            'Up from Low %': {'type': 'number', 'format': '%.2f%%', 'help': 'Percentage up from 52-week low'},
            'Time': {'type': 'text', 'help': 'Last update time', 'hidden': True},
            'Index Type': {'type': 'text', 'help': 'Type of index', 'hidden': True},
            'Index Sub Type': {'type': 'text', 'help': 'Sub-type of index', 'hidden': True}
        }

    def create_column_config(self) -> Dict:
        """Create Streamlit column configuration for visible columns."""
        column_definitions = self.get_column_definitions()
        column_config = {}
        
        for col in column_definitions:
            col_def = column_definitions[col]
            if col_def['type'] == 'number':
                config = st.column_config.NumberColumn(
                    col,
                    help=col_def['help'],
                    format=col_def['format']
                )
            else:
                config = st.column_config.TextColumn(
                    col,
                    help=col_def['help']
                )
            config['hidden'] = col_def.get('hidden', False)
            column_config[col] = config
        
        return column_config

    def get_categorized_data(self, raw_data: pd.DataFrame) -> Dict[str, Dict[str, pd.DataFrame]]:
        """Get NSE indexes data categorized by indexType and indexSubType."""
        if raw_data is None or raw_data.empty:
            return {}
        
        try:
            # Format the data first
            df_formatted = self.format_data_for_display(raw_data)
            
            # Categorize by indexType and indexSubType
            categorized_data = {}
            
            for index_type in raw_data['indexType'].unique():
                if pd.isna(index_type):
                    continue
                    
                type_data = raw_data[raw_data['indexType'] == index_type]
                categorized_data[index_type] = {}
                
                for sub_type in type_data['indexSubType'].unique():
                    if pd.isna(sub_type):
                        continue
                        
                    # Get the corresponding display data for this sub-type
                    sub_type_indices = type_data[type_data['indexSubType'] == sub_type]['index'].tolist()
                    sub_type_display_data = df_formatted[df_formatted['Index'].isin(sub_type_indices)]
                    categorized_data[index_type][sub_type] = sub_type_display_data
            
            return categorized_data
            
        except Exception as e:
            logger.error(f"Error categorizing data: {str(e)}", exc_info=True)
            return {}

    def get_summary_statistics(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate summary statistics for the formatted data."""
        if df is None or df.empty:
            return {}
        
        try:
            stats = {}
            
            if 'Change %' in df.columns:
                stats['average_change'] = df['Change %'].mean()
                stats['positive_count'] = len(df[df['Change %'] > 0])
                stats['negative_count'] = len(df[df['Change %'] < 0])
            
            if 'Value' in df.columns:
                stats['total_indices'] = len(df)
                stats['avg_value'] = df['Value'].mean()
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating summary statistics: {str(e)}", exc_info=True)
            return {} 