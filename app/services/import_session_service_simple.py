"""
Simplified Import Session Service
Basic version with core functionality only
"""
import os
import uuid
import tempfile
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
from fastapi import UploadFile

from app.schemas.generic_import import (
    ImportSession, FileInfo, DetectedColumn
)
from app.services.model_metadata_registry import ModelMetadataRegistry


class ImportSessionService:
    """
    Simplified service for managing import sessions
    """
    
    def __init__(self):
        self._sessions: Dict[str, ImportSession] = {}
        self._session_ttl_hours = 2
        self.temp_dir = tempfile.gettempdir()
        self.metadata_registry = ModelMetadataRegistry()
    
    async def create_session(
        self, 
        file: UploadFile, 
        model_name: str, 
        user_id: str
    ) -> ImportSession:
        """
        Create a new import session
        """
        # Generate token unique
        session_token = str(uuid.uuid4())
        
        # Get model metadata
        model_metadata = self.metadata_registry.get_model_metadata(model_name)
        if not model_metadata:
            raise ValueError(f"Model {model_name} not found")
        
        # Save temporary file
        file_path = os.path.join(self.temp_dir, f"{session_token}_{file.filename or 'upload'}")
        
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Analyze file and get sample data
        file_info, detected_columns, sample_rows = await self._analyze_file(file, file_path)
        
        # Create session
        session = ImportSession(
            token=session_token,
            model=model_name,
            model_metadata=model_metadata,
            file_info=file_info,
            detected_columns=detected_columns,
            sample_rows=sample_rows,
            user_id=user_id,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=self._session_ttl_hours),
            file_path=file_path
        )
        
        # Store session
        self._sessions[session_token] = session
        
        return session
    
    async def get_session(self, session_token: str) -> Optional[ImportSession]:
        """
        Get import session by token
        """
        session = self._sessions.get(session_token)
        
        if session and session.expires_at < datetime.utcnow():
            # Session expired, remove it
            self._cleanup_session(session_token)
            return None
        
        return session
    
    def _cleanup_session(self, session_token: str):
        """
        Clean up session and its files
        """
        if session_token in self._sessions:
            session = self._sessions[session_token]
            
            # Remove temporary file
            try:
                if os.path.exists(session.file_path):
                    os.remove(session.file_path)
            except Exception:
                pass  # Ignore file cleanup errors
            
            # Remove session
            del self._sessions[session_token]
    
    async def read_file_batch(self, session_token: str, batch_size: int = 2000, batch_number: int = 0) -> List[Dict[str, Any]]:
        """
        Read a batch of data from the file associated with the session
        
        Args:
            session_token: The session token
            batch_size: Number of rows to read per batch (default 2000)
            batch_number: Which batch to read (0-indexed)
            
        Returns:
            List of dictionaries representing rows in the batch
        """
        session = await self.get_session(session_token)
        if not session:
            raise ValueError(f"Session {session_token} not found or expired")
        
        file_path = session.file_path
        filename = session.file_info.name
        
        # Calculate skip rows
        skip_rows = batch_number * batch_size
        
        try:
            if filename.lower().endswith('.csv'):
                # For CSV files, use skiprows and nrows to read specific batch
                if skip_rows == 0:
                    # First batch, don't skip header
                    df = pd.read_csv(file_path, encoding='utf-8', nrows=batch_size)
                else:
                    # Skip header + previous rows
                    df = pd.read_csv(file_path, encoding='utf-8', skiprows=skip_rows + 1, nrows=batch_size, header=None)
                    # Get column names from the first row of file
                    header_df = pd.read_csv(file_path, encoding='utf-8', nrows=0)
                    df.columns = header_df.columns
                    
            elif filename.lower().endswith(('.xlsx', '.xls')):
                # For Excel files, read the specific range
                df = pd.read_excel(file_path, skiprows=skip_rows, nrows=batch_size)
            else:
                raise ValueError("Unsupported file format")
                
            # Convert to list of dictionaries with NaN handling
            batch_data = []
            for _, row in df.iterrows():
                clean_row = {}
                for k, v in row.items():
                    if pd.isna(v):
                        clean_row[str(k)] = None
                    else:
                        clean_row[str(k)] = v
                batch_data.append(clean_row)
                
            return batch_data
            
        except Exception as e:
            raise ValueError(f"Error reading batch from file: {str(e)}")
    
    def get_total_batches(self, session_token: str, batch_size: int = 2000) -> int:
        """
        Calculate total number of batches needed for a session
        """
        session = self._sessions.get(session_token)
        if not session:
            return 0
            
        total_rows = session.file_info.total_rows
        return (total_rows + batch_size - 1) // batch_size  # Ceiling division
    
    async def read_full_file_data(self, session_token: str) -> List[Dict[str, Any]]:
        """
        Read all data from the file associated with the session
        Used for complete validation before import
        
        Args:
            session_token: The session token
            
        Returns:
            List of dictionaries representing all rows in the file
        """
        session = await self.get_session(session_token)
        if not session:
            raise ValueError(f"Session {session_token} not found or expired")
        
        file_path = session.file_path
        filename = session.file_info.name
        
        try:
            if filename.lower().endswith('.csv'):
                # Read entire CSV file
                df = pd.read_csv(file_path, encoding='utf-8')
            elif filename.lower().endswith(('.xlsx', '.xls')):
                # Read entire Excel file
                df = pd.read_excel(file_path)
            else:
                raise ValueError("Unsupported file format")
                
            # Convert to list of dictionaries with NaN handling
            all_data = []
            for _, row in df.iterrows():
                clean_row = {}
                for k, v in row.items():
                    if pd.isna(v):
                        clean_row[str(k)] = None
                    else:
                        clean_row[str(k)] = v
                all_data.append(clean_row)
                
            return all_data
            
        except Exception as e:
            raise ValueError(f"Error reading complete file: {str(e)}")
    
    async def _analyze_file(self, file: UploadFile, file_path: str) -> tuple[FileInfo, List[DetectedColumn], List[Dict[str, Any]]]:
        """
        Analyze uploaded file and extract information
        """
        file_size = os.path.getsize(file_path)
        filename = file.filename or "unknown"
        
        # First, get the total number of rows without loading all data
        total_rows = 0
        delimiter = ","
        
        if filename.lower().endswith('.csv'):
            # Count total rows in CSV
            with open(file_path, 'r', encoding='utf-8') as f:
                total_rows = sum(1 for line in f) - 1  # Subtract header row
            
            # Read first 10 rows for analysis
            df = pd.read_csv(file_path, encoding='utf-8', nrows=10)
            delimiter = ","
        elif filename.lower().endswith(('.xlsx', '.xls')):
            # For Excel, read first to get total rows (Excel files are typically smaller)
            df_full = pd.read_excel(file_path)
            total_rows = len(df_full)
            
            # Get first 10 rows for analysis
            df = df_full.head(10)
            delimiter = None
        else:
            raise ValueError("Unsupported file format. Only CSV and Excel files are supported.")
        
        # Create file info with actual total rows
        file_info = FileInfo(
            name=filename,
            size=file_size,
            encoding='utf-8',
            delimiter=delimiter,
            total_rows=total_rows
        )
        
        # Detect columns
        detected_columns = []
        for col in df.columns:
            sample_values = df[col].dropna().head(5).astype(str).tolist()
            detected_columns.append(DetectedColumn(
                name=str(col),
                sample_values=sample_values,
                data_type_hint=self._guess_data_type(sample_values)
            ))        # Get sample rows (convert to proper type)
        sample_data = df.head(10).to_dict('records')
        # Convert NaN values to None to avoid pandas NaN issues
        sample_rows: List[Dict[str, Any]] = []
        for row in sample_data:
            clean_row = {}
            for k, v in row.items():
                # Convert pandas NaN to None
                if pd.isna(v):
                    clean_row[str(k)] = None
                else:
                    clean_row[str(k)] = v
            sample_rows.append(clean_row)
        
        return file_info, detected_columns, sample_rows
    
    def _guess_data_type(self, sample_values: List[str]) -> str:
        """
        Guess data type from sample values
        """
        if not sample_values:
            return "text"
        
        # Simple heuristics
        numeric_count = 0
        date_count = 0
        
        for value in sample_values:
            try:
                float(value)
                numeric_count += 1
            except ValueError:
                pass
            
            # Check for date patterns (very basic)
            if any(sep in value for sep in ['-', '/', '.']):
                if len(value.split(next(sep for sep in ['-', '/', '.'] if sep in value))) == 3:
                    date_count += 1
        
        if numeric_count >= len(sample_values) * 0.8:
            return "number"
        elif date_count >= len(sample_values) * 0.8:
            return "date"
        else:
            return "text"


# Global instance
import_session_service = ImportSessionService()
