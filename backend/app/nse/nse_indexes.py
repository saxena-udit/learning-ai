import pandas as pd
from nsepython import nse_index
from typing import List, Dict, Optional, Tuple
import time
try:
    from utils.logger import get_logger
except ImportError:
    try:
        from app.utils.logger import get_logger
    except ImportError:
        import logging
        def get_logger(name):
            return logging.getLogger(name)

logger = get_logger("nse_indexes")

class NSEIndexes:
    """Class to handle NSE indexes data"""

    def __init__(self):
        self.indexes_data: Optional[pd.DataFrame] = None
        self.last_update: Optional[float] = None
        self.update_interval: int = 300  # 5 minutes
        # Get all available indices dynamically
        self.available_indices: List[str] = []
        self._load_available_indices()

    def _load_available_indices(self):
        """Load all available indices from NSE using nse_index"""
        try:
            # Use nse_index to get all indices data and extract index names
            all_indices_df = nse_index()
            self.available_indices = all_indices_df['indexName'].tolist()
            # Store the data for reuse in get_nse_indexes
            self._cached_indices_data = all_indices_df
            logger.info(f"Loaded {len(self.available_indices)} available indices from NSE")
        except Exception as e:
            logger.error(f"Error loading available indices: {str(e)}", exc_info=True)
            # Fallback to major indices if loading fails
            self.available_indices = [
                'NIFTY 50', 'NIFTY BANK', 'NIFTY IT', 'NIFTY PHARMA', 
                'NIFTY AUTO', 'NIFTY FMCG', 'NIFTY METAL', 'NIFTY REALTY',
                'NIFTY INFRA', 'NIFTY ENERGY', 'NIFTY CONSUMPTION', 'NIFTY MEDIA'
            ]
            self._cached_indices_data = None
            logger.warning("Using fallback major indices")

    def get_nse_indexes(self) -> pd.DataFrame:
        """
        Fetch NSE indexes data using nse_index (optimized)
        Returns a pandas DataFrame containing index information
        """
        try:
            # Use cached data if available, otherwise fetch fresh data
            if hasattr(self, '_cached_indices_data') and self._cached_indices_data is not None:
                all_indices_df = self._cached_indices_data
                # Clear cache after use to ensure fresh data on next call
                self._cached_indices_data = None
                logger.debug("Using cached indices data")
            else:
                # Fetch fresh data if cache is not available
                all_indices_df = nse_index()
                logger.debug("Fetched fresh indices data")
            
            if all_indices_df.empty:
                logger.warning("No index data could be fetched.")
                return pd.DataFrame()

            # Process the data to match our expected format
            indexes_list = []
            
            for _, row in all_indices_df.iterrows():
                try:
                    # Extract and clean numeric values
                    last_price = self._clean_numeric_value(row.get('last', '0'))
                    prev_close = self._clean_numeric_value(row.get('previousClose', '0'))
                    variation = last_price - prev_close
                    
                    # Calculate percentage down from year high
                    year_high = self._clean_numeric_value(row.get('yearHigh', '0'))
                    down_from_high_pct = ((year_high - last_price) / year_high * 100) if year_high > 0 else 0
                    
                    # Calculate percentage up from year low
                    year_low = self._clean_numeric_value(row.get('yearLow', '0'))
                    up_from_low_pct = ((last_price - year_low) / year_low * 100) if year_low > 0 else 0
                    
                    # Format the data for our DataFrame
                    formatted_data = {
                        'index': row.get('indexName', ''),
                        'last': row.get('last', '0'),
                        'variation': variation,
                        'percentChange': row.get('percChange', '0'),
                        'high': row.get('high', '0'),
                        'low': row.get('low', '0'),
                        'open': row.get('open', '0'),
                        'previousClose': row.get('previousClose', '0'),
                        'yearHigh': row.get('yearHigh', '0'),
                        'yearLow': row.get('yearLow', '0'),
                        'downFromHighPct': down_from_high_pct,
                        'upFromLowPct': up_from_low_pct,
                        'timeVal': row.get('timeVal', ''),
                        'indexType': row.get('indexType', ''),
                        'indexSubType': row.get('indexSubType', ''),
                        'indexOrder': row.get('indexOrder', 0)
                    }
                    indexes_list.append(formatted_data)
                    
                except Exception as e:
                    logger.warning(f"Failed to process index {row.get('indexName', 'Unknown')}: {str(e)}")
                    continue

            if not indexes_list:
                logger.warning("No index data could be processed.")
                return pd.DataFrame()

            indexes_df = pd.DataFrame(indexes_list)
            logger.info(f"Successfully processed data for {len(indexes_list)} out of {len(all_indices_df)} available indices")
            
            # Ensure we have the expected columns
            expected_columns = ['index', 'last', 'variation', 'percentChange', 'high', 'low', 'open', 'previousClose', 'yearHigh', 'yearLow', 'downFromHighPct', 'upFromLowPct', 'timeVal']
            for col in expected_columns:
                if col not in indexes_df.columns:
                    indexes_df[col] = None

            return indexes_df

        except Exception as e:
            logger.error(f"Error fetching NSE indexes: {str(e)}", exc_info=True)
            # Return empty DataFrame if fetching fails
            return pd.DataFrame()

    def _clean_numeric_value(self, value) -> float:
        """Clean and convert numeric values from string format"""
        if pd.isna(value) or value is None:
            return 0.0
        
        if isinstance(value, (int, float)):
            return float(value)
        
        # Convert string to float, handling commas and other formatting
        try:
            cleaned_value = str(value).replace(',', '').replace('₹', '').strip()
            return float(cleaned_value) if cleaned_value else 0.0
        except (ValueError, TypeError):
            return 0.0

    def should_update_data(self) -> bool:
        """Check if data should be updated based on time interval"""
        if self.last_update is None:
            return True

        current_time = time.time()
        return (current_time - self.last_update) > self.update_interval

    def update_data(self):
        """Update the indexes data if it's stale."""
        if self.should_update_data():
            self.indexes_data = self.get_nse_indexes()
            if not self.indexes_data.empty:
                self.last_update = time.time()
                logger.info(f"Updated NSE indexes data with {len(self.indexes_data)} indices")

    def force_refresh(self):
        """Forces a data refresh on the next data request."""
        self.last_update = None
        # Clear cached data to ensure fresh fetch
        if hasattr(self, '_cached_indices_data'):
            self._cached_indices_data = None
        # Also reload available indices
        self._load_available_indices()
        logger.info("NSE index refresh forced.")

    def refresh_available_indices(self):
        """Refresh the list of available indices from NSE."""
        # Clear cached data to ensure fresh fetch
        if hasattr(self, '_cached_indices_data'):
            self._cached_indices_data = None
        self._load_available_indices()
        logger.info("Available indices refreshed.")

    def get_available_indices_count(self) -> int:
        """Get the count of available indices."""
        return len(self.available_indices)

    def get_available_indices(self) -> List[str]:
        """Get the list of available indices."""
        return self.available_indices.copy()

    def get_data_for_display(self) -> Tuple[Optional[pd.DataFrame], Optional[float]]:
        """
        Update data if needed and return formatted DataFrame and last update time.
        """
        self.update_data()

        if self.indexes_data is None or self.indexes_data.empty:
            return None, self.last_update

        df = self.indexes_data
        display_cols = {
            'index': 'Index',
            'last': 'Value',
            'percentChange': 'Change %',
            'yearHigh': '52W High',
            'yearLow': '52W Low',
            'downFromHighPct': 'Down from High %',
            'upFromLowPct': 'Up from Low %'
        }
        # Use a copy to avoid SettingWithCopyWarning
        df_display = df[[col for col in display_cols if col in df.columns]].copy()
        df_display = df_display.rename(columns=display_cols)

        # Columns that should be numeric
        numeric_cols = ['Value', 'Change %', '52W High', '52W Low', 'Down from High %', 'Up from Low %']
        for col in numeric_cols:
            if col in df_display.columns:
                # Convert string values to numeric, handling commas
                df_display[col] = df_display[col].astype(str).str.replace(',', '').apply(
                    lambda x: pd.to_numeric(x, errors='coerce')
                )

        # Store numeric values for sorting (before formatting)
        numeric_data = df_display.copy()
        
        # Keep all columns as numeric for proper sorting
        # Formatting will be handled by Streamlit's column configuration

        # Store the numeric data for sorting purposes
        df_display.attrs['numeric_data'] = numeric_data

        return df_display, self.last_update

    def get_data_for_sorting(self) -> Optional[pd.DataFrame]:
        """
        Return numeric data for proper sorting of percentage columns.
        """
        self.update_data()

        if self.indexes_data is None or self.indexes_data.empty:
            return None

        df = self.indexes_data
        display_cols = {
            'index': 'Index',
            'last': 'Value',
            'percentChange': 'Change %',
            'yearHigh': '52W High',
            'yearLow': '52W Low',
            'downFromHighPct': 'Down from High %',
            'upFromLowPct': 'Up from Low %'
        }
        
        df_display = df[[col for col in display_cols if col in df.columns]].copy()
        df_display = df_display.rename(columns=display_cols)

        # Convert to numeric for sorting
        numeric_cols = ['Value', 'Change %', '52W High', '52W Low', 'Down from High %', 'Up from Low %']
        for col in numeric_cols:
            if col in df_display.columns:
                df_display[col] = df_display[col].astype(str).str.replace(',', '').apply(
                    lambda x: pd.to_numeric(x, errors='coerce')
                )

        return df_display

    def get_categorized_data(self) -> Dict[str, Dict[str, pd.DataFrame]]:
        """
        Get NSE indexes data categorized by indexType and indexSubType.
        Returns a nested dictionary: {indexType: {indexSubType: DataFrame}}
        """
        self.update_data()

        if self.indexes_data is None or self.indexes_data.empty:
            return {}

        df = self.indexes_data.copy()
        
        # Add display columns (excluding indexType and indexSubType from display)
        display_cols = {
            'index': 'Index',
            'last': 'Value',
            'percentChange': 'Change %',
            'yearHigh': '52W High',
            'yearLow': '52W Low',
            'downFromHighPct': 'Down from High %',
            'upFromLowPct': 'Up from Low %'
        }
        
        # Select and rename columns
        df_display = df[[col for col in display_cols if col in df.columns]].copy()
        df_display = df_display.rename(columns=display_cols)

        # Convert numeric columns
        numeric_cols = ['Value', 'Change %', '52W High', '52W Low', 'Down from High %', 'Up from Low %']
        for col in numeric_cols:
            if col in df_display.columns:
                df_display[col] = df_display[col].astype(str).str.replace(',', '').apply(
                    lambda x: pd.to_numeric(x, errors='coerce')
                )

        # Categorize by indexType and indexSubType (using original df for categorization)
        categorized_data = {}
        
        for index_type in df['indexType'].unique():
            if pd.isna(index_type):
                continue
                
            type_data = df[df['indexType'] == index_type]
            categorized_data[index_type] = {}
            
            for sub_type in type_data['indexSubType'].unique():
                if pd.isna(sub_type):
                    continue
                    
                # Get the corresponding display data for this sub-type
                sub_type_indices = type_data[type_data['indexSubType'] == sub_type]['index'].tolist()
                sub_type_display_data = df_display[df_display['Index'].isin(sub_type_indices)]
                categorized_data[index_type][sub_type] = sub_type_display_data

        return categorized_data

    def get_index_types(self) -> List[str]:
        """Get list of available index types."""
        self.update_data()
        
        if self.indexes_data is None or self.indexes_data.empty:
            return []
            
        return self.indexes_data['indexType'].dropna().unique().tolist()

    def get_index_sub_types(self, index_type: str = None) -> List[str]:
        """Get list of available index sub types, optionally filtered by index type."""
        self.update_data()
        
        if self.indexes_data is None or self.indexes_data.empty:
            return []
            
        if index_type:
            filtered_data = self.indexes_data[self.indexes_data['indexType'] == index_type]
            return filtered_data['indexSubType'].dropna().unique().tolist()
        else:
            return self.indexes_data['indexSubType'].dropna().unique().tolist()

    def get_index_type_labels(self) -> Dict[str, str]:
        """Get descriptive labels for index types."""
        return {
            'eq': 'Equity Indices',
            'fi': 'Fixed Income Indices',
            '-': 'Other Indices'
        }

    def get_index_sub_type_labels(self) -> Dict[str, str]:
        """Get descriptive labels for index sub types."""
        return {
            'bm': 'Broad Market',
            'sc': 'Sector/Theme',
            'th': 'Thematic',
            'st': 'Strategy',
            'Target Maturity': 'Target Maturity',
            'GSec': 'Government Securities',
            'Money Market': 'Money Market',
            '-': 'Other'
        }

    def get_display_name(self, index_type: str, sub_type: str = None) -> str:
        """Get a user-friendly display name for index type and sub-type combination."""
        type_labels = self.get_index_type_labels()
        sub_type_labels = self.get_index_sub_type_labels()
        
        type_label = type_labels.get(index_type, index_type)
        
        if sub_type:
            sub_type_label = sub_type_labels.get(sub_type, sub_type)
            return f"{type_label} - {sub_type_label}"
        else:
            return type_label
