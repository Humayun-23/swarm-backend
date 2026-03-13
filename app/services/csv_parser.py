"""
CSV Parser Service
"""
from typing import List, Dict, Any, Tuple
import pandas as pd
from io import StringIO
import csv
from app.utils.logger import logger
from app.utils.helpers import validate_email


class CSVParser:
    """CSV parser for participant data"""
    
    REQUIRED_COLUMNS = ["email", "full_name"]
    OPTIONAL_COLUMNS = [
        "organization", "role", "is_speaker", "is_sponsor"
    ]
    
    def __init__(self):
        self.errors: List[str] = []
    
    def parse_csv_file(self, file_content: bytes) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Parse CSV file content
        
        Args:
            file_content: CSV file content as bytes
            
        Returns:
            Tuple of (parsed participants list, errors list)
        """
        self.errors = []
        participants = []
        
        try:
            # Decode content
            content_str = file_content.decode("utf-8")
            
            # Read CSV using pandas
            df = pd.read_csv(StringIO(content_str))
            
            # Validate required columns
            missing_cols = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
            if missing_cols:
                self.errors.append(f"Missing required columns: {', '.join(missing_cols)}")
                return [], self.errors
            
            # Process each row
            for idx, row in df.iterrows():
                try:
                    participant = self._process_row(row, idx)
                    if participant:
                        participants.append(participant)
                except Exception as e:
                    self.errors.append(f"Row {idx + 2}: {str(e)}")
            
            logger.info(f"Parsed {len(participants)} participants from CSV")
            
        except UnicodeDecodeError:
            self.errors.append("Invalid file encoding. Please use UTF-8 encoding.")
        except pd.errors.EmptyDataError:
            self.errors.append("CSV file is empty")
        except Exception as e:
            self.errors.append(f"Failed to parse CSV: {str(e)}")
        
        return participants, self.errors
    
    def _process_row(self, row: pd.Series, row_idx: int) -> Dict[str, Any]:
        """
        Process a single CSV row
        
        Args:
            row: Pandas Series representing a row
            row_idx: Row index for error reporting
            
        Returns:
            Processed participant dictionary
        """
        # Extract and validate email
        email = str(row.get("email", "")).strip()
        if not email:
            raise ValueError("Email is required")
        
        if not validate_email(email):
            raise ValueError(f"Invalid email format: {email}")
        
        # Extract full name
        full_name = str(row.get("full_name", "")).strip()
        if not full_name:
            raise ValueError("Full name is required")
        
        # Build participant dictionary
        participant = {
            "email": email,
            "full_name": full_name,
            "organization": str(row.get("organization", "")).strip() or None,
            "role": str(row.get("role", "")).strip() or None,
            "is_speaker": self._parse_boolean(row.get("is_speaker", False)),
            "is_sponsor": self._parse_boolean(row.get("is_sponsor", False)),
        }
        
        # Add any additional metadata
        metadata = {}
        for col in row.index:
            if col not in self.REQUIRED_COLUMNS and col not in self.OPTIONAL_COLUMNS:
                metadata[col] = str(row[col]) if pd.notna(row[col]) else None
        
        if metadata:
            participant["participant_metadata"] = metadata
        
        return participant
    
    def _parse_boolean(self, value: Any) -> bool:
        """
        Parse boolean value from CSV
        
        Args:
            value: Value to parse
            
        Returns:
            Boolean value
        """
        if isinstance(value, bool):
            return value
        
        if pd.isna(value):
            return False
        
        str_value = str(value).lower().strip()
        return str_value in ["true", "1", "yes", "y"]
    
    def validate_csv_structure(self, file_content: bytes) -> Tuple[bool, List[str]]:
        """
        Validate CSV structure without full parsing
        
        Args:
            file_content: CSV file content
            
        Returns:
            Tuple of (is_valid, errors)
        """
        errors = []
        
        try:
            content_str = file_content.decode("utf-8")
            df = pd.read_csv(StringIO(content_str), nrows=1)
            
            # Check required columns
            missing_cols = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
            if missing_cols:
                errors.append(f"Missing required columns: {', '.join(missing_cols)}")
                return False, errors
            
            return True, []
            
        except Exception as e:
            errors.append(f"Invalid CSV structure: {str(e)}")
            return False, errors
    
    def get_column_mapping_suggestions(self, file_content: bytes) -> Dict[str, List[str]]:
        """
        Suggest column mappings based on CSV headers
        
        Args:
            file_content: CSV file content
            
        Returns:
            Dictionary of suggested mappings
        """
        suggestions = {
            "email": ["email", "e-mail", "email_address", "mail"],
            "full_name": ["full_name", "name", "fullname", "participant_name"],
            "organization": ["organization", "company", "org", "institution"],
            "role": ["role", "position", "title", "job_title"]
        }
        
        try:
            content_str = file_content.decode("utf-8")
            df = pd.read_csv(StringIO(content_str), nrows=1)
            
            mappings = {}
            for target_col, possible_names in suggestions.items():
                for col in df.columns:
                    if col.lower().strip() in possible_names:
                        mappings[target_col] = col
                        break
            
            return mappings
            
        except Exception:
            return {}