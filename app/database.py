"""
Database module for the GenAI SMS Chatbot.

This module handles MSSQL database connections with conditional authentication:
- Windows: Uses Windows Authentication (Trusted Connection)
- Other OS: Uses username/password authentication
"""

import os
import platform
import logging
import random
from typing import Optional, Dict, Any, List
from datetime import datetime, date, time, timedelta
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, Date, Time, Boolean, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.dialects import mssql, sqlite

from config.project_config import BaseConfigurable

Base = declarative_base()


class Schedules(Base):
    """SQLAlchemy model for the Schedules table."""
    __tablename__ = 'Schedules'
    
    ScheduleID = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=False)
    position = Column(String(20), nullable=False)
    available = Column(Boolean, default=True)
    
    # Relationship to Interviews
    interviews = relationship("Interviews", back_populates="schedule", cascade="all, delete-orphan")


class Interviews(Base):
    """SQLAlchemy model for the Interviews table."""
    __tablename__ = 'Interviews'
    
    InterviewID = Column(Integer, primary_key=True)
    ScheduleID = Column(Integer, ForeignKey('Schedules.ScheduleID'), nullable=False)
    CandidatePhone = Column(String(15), nullable=False)
    RecruiterPhone = Column(String(15), nullable=False)
    
    # Relationship to Schedule
    schedule = relationship("Schedules", back_populates="interviews")

class DatabaseManager(BaseConfigurable):
    """Manages database connections and operations."""
    
    def __init__(self):
        """Initialize the database manager."""
        super().__init__()
        self.engine = None
        self.Session = None
        self.is_connected = False
        self.database_type = None  # 'mssql' or 'sqlite'
        
        # Initialize connection - will raise exception if connection fails
        self._initialize_connection()
        
        if not self.is_connected:
            raise Exception("Failed to establish database connection. Application cannot start without database.")
    
    def _normalize_phone_number(self, phone: str) -> str:
        """
        Normalize phone number to consistent format.
        
        Args:
            phone: Phone number to normalize
            
        Returns:
            Normalized phone number
        """
        # Remove all non-digit characters
        digits_only = ''.join(filter(str.isdigit, phone))
        
        # If it's 11 digits and starts with 1, remove the 1
        if len(digits_only) == 11 and digits_only.startswith('1'):
            return digits_only[1:]
        
        # If it's 10 digits, return as is
        if len(digits_only) == 10:
            return digits_only
        
        # If it's 9 digits, assume it needs a leading 0 (common in some countries)
        if len(digits_only) == 9:
            return '0' + digits_only
        
        # Return original if no pattern matches
        return phone
    
    def _initialize_connection(self):
        """Initialize database connection based on platform."""
        system = platform.system().lower()
        self.logger.info(f"Detected operating system: {system}")
        
        if system == "windows":
            self.logger.info("Using Windows authentication method")
            self._initialize_windows_connection()
        else:
            self.logger.info("Using username/password authentication method")
            self._initialize_other_os_connection()
        
        if self.is_connected:
            self.logger.info("Database connection established successfully")
        else:
            self.logger.warning("Database connection failed, will use in-memory storage")
    
    def _initialize_windows_connection(self):
        """Initialize connection using Windows Authentication."""
        try:
            self.logger.info("Attempting to initialize SQL Server connection for Windows...")
            
            # Try pyodbc for Windows
            try:
                import pyodbc
                self.logger.info("pyodbc module imported successfully")
            except ImportError as e:
                self.logger.error(f"Failed to import pyodbc: {e}")
                raise ImportError("pyodbc not available")
            
            server = os.getenv('MSSQL_SERVER', 'localhost')
            database = os.getenv('MSSQL_DATABASE', 'Tech')
            
            self.logger.info(f"Connection parameters - Server: {server}, Database: {database}")
            
            connection_string = f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;TrustServerCertificate=yes;"
            self.logger.info(f"Attempting to create engine with connection string: {connection_string}")
            
            self.engine = create_engine(f"mssql+pyodbc:///?odbc_connect={connection_string}")
            self.Session = sessionmaker(bind=self.engine)
            
            self.logger.info("Engine created successfully, testing connection...")
            
            # Test connection
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                self.logger.info(f"Connection test successful: {result.fetchone()}")
            
            self.is_connected = True
            self.database_type = 'mssql'
            self.logger.info("Windows authentication connection established successfully")
            
        except ImportError as e:
            self.logger.error(f"Import error: {e}")
            raise Exception(f"pyodbc not available. Cannot connect to MSSQL without pyodbc driver: {e}")
        except Exception as conn_error:
            self.logger.error(f"Connection failed: {conn_error}")
            self.logger.warning("MSSQL connection failed, falling back to SQLite for development")
            self._initialize_sqlite_fallback()
    
    def _initialize_other_os_connection(self):
        """Initialize connection using username/password authentication."""
        try:
            self.logger.info("Attempting to initialize SQL Server connection for non-Windows OS...")
            
            # For now, we'll use a simplified approach that works on macOS
            # The ODBC driver issues on macOS ARM64 are complex to resolve
            server = os.getenv('MSSQL_SERVER', 'localhost')
            database = os.getenv('MSSQL_DATABASE', 'Tech')
            username = os.getenv('MSSQL_USERNAME', 'sa')
            password = os.getenv('MSSQL_PASSWORD', '')
            port = os.getenv('MSSQL_PORT', '1433')
            
            self.logger.info(f"Connection parameters - Server: {server}, Database: {database}, Username: {username}, Port: {port}")
            
            # For macOS, we'll use a direct connection approach
            # This is a workaround for the ODBC driver issues on macOS ARM64
            self.logger.warning("ODBC drivers have compatibility issues on macOS ARM64. Using alternative connection method.")
            
            # Create a connection string using pyodbc for SQL Server
            connection_string = f"mssql+pyodbc://{username}:{password}@{server}:{port}/{database}?driver=ODBC+Driver+17+for+SQL+Server"
            
            try:
                self.engine = create_engine(connection_string, echo=False)
                self.Session = sessionmaker(bind=self.engine)
                
                self.logger.info("Engine created successfully, testing connection...")
                
                # Test connection
                with self.engine.connect() as conn:
                    result = conn.execute(text("SELECT 1"))
                    self.logger.info(f"Connection test successful: {result.fetchone()}")
                
                self.is_connected = True
                self.database_type = 'mssql'
                self.logger.info("Username/password authentication connection established successfully")
                
            except Exception as conn_error:
                self.logger.error(f"Connection failed: {conn_error}")
                self.logger.warning("MSSQL connection failed, falling back to SQLite for development")
                self._initialize_sqlite_fallback()
            
        except Exception as e:
            self.logger.error(f"Other OS connection failed: {e}")
            self.logger.error(f"Connection error details: {type(e).__name__}: {str(e)}")
            self.logger.warning("MSSQL connection failed, falling back to SQLite for development")
            self._initialize_sqlite_fallback()
    
    def _initialize_sqlite_fallback(self):
        """Initialize SQLite fallback database."""
        try:
            self.logger.info("Initializing SQLite fallback database...")
            
            # Create SQLite database in the project directory
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'tech_interviews.db')
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            connection_string = f"sqlite:///{db_path}"
            
            self.engine = create_engine(connection_string, echo=False)
            self.Session = sessionmaker(bind=self.engine)
            
            # Create tables if they don't exist
            # For SQLite, we need to enable foreign key constraints
            if self.database_type == 'sqlite':
                with self.engine.connect() as conn:
                    conn.execute(text("PRAGMA foreign_keys = ON"))
            
            Base.metadata.create_all(self.engine)
            
            # Populate with sample data if tables are empty
            self._populate_sample_data()
            
            self.is_connected = True
            self.database_type = 'sqlite'
            self.logger.info("SQLite fallback database initialized successfully")
            
        except Exception as e:
            self.logger.error(f"SQLite fallback initialization failed: {e}")
            raise Exception(f"Failed to initialize any database connection: {e}")
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        Get information about the current database connection.
        
        Returns:
            Dictionary with database information
        """
        return {
            'type': self.database_type,
            'connected': self.is_connected,
            'engine_url': str(self.engine.url) if self.engine else None
        }
    
    def check_database_health(self) -> Dict[str, Any]:
        """
        Check the health of the database connection.
        
        Returns:
            Dictionary with health status and details
        """
        try:
            if not self.is_connected or not self.engine:
                return {
                    'healthy': False,
                    'error': 'Database not connected',
                    'type': self.database_type
                }
            
            # Test connection
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
            
            # Check table counts
            session = self.Session()
            schedules_count = session.query(Schedules).count()
            interviews_count = session.query(Interviews).count()
            session.close()
            
            return {
                'healthy': True,
                'type': self.database_type,
                'schedules_count': schedules_count,
                'interviews_count': interviews_count
            }
            
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'type': self.database_type
            }
    
    def _populate_sample_data(self):
        """Populate SQLite database with sample data similar to db_Tech.sql."""
        try:
            session = self.Session()
            
            # Check if data already exists
            existing_count = session.query(Schedules).count()
            if existing_count > 0:
                self.logger.info(f"Database already contains {existing_count} records, skipping sample data population")
                session.close()
                return
            
            self.logger.info("Populating database with sample data...")
            
            # Get current year and start from today
            current_year = datetime.now().year
            start_date = date.today()  # Start from today instead of January 1st
            end_date = date(current_year, 12, 31)
            
            # Define positions
            positions = ['Python Developer', 'SQL Developer', 'Data Analyst', 'ML Engineer']
            
            # Define time slots (9:00-17:00)
            time_slots = [
                time(9, 0), time(10, 0), time(11, 0), time(12, 0),
                time(13, 0), time(14, 0), time(15, 0), time(16, 0)
            ]
            
            # Generate dates (Tue-Fri & Sun only)
            valid_dates = []
            current_date = start_date
            while current_date <= end_date:
                weekday = current_date.weekday()  # Monday=0, Sunday=6
                if weekday in [1, 2, 3, 6]:  # Tuesday, Wednesday, Thursday, Sunday
                    valid_dates.append(current_date)
                current_date += timedelta(days=1)
            
            # Generate sample schedules
            schedules_to_add = []
            for schedule_date in valid_dates:
                for time_slot in time_slots:
                    for position in positions:
                        # 50% chance of being available (similar to db_Tech.sql logic)
                        available = random.random() >= 0.5
                        
                        schedule = Schedules(
                            date=schedule_date,
                            time=time_slot,
                            position=position,
                            available=available
                        )
                        schedules_to_add.append(schedule)
            
            # Add all schedules in batches
            batch_size = 1000
            for i in range(0, len(schedules_to_add), batch_size):
                batch = schedules_to_add[i:i + batch_size]
                session.add_all(batch)
                session.commit()
                self.logger.info(f"Added batch {i//batch_size + 1} of {(len(schedules_to_add) + batch_size - 1)//batch_size}")
            
            total_added = len(schedules_to_add)
            self.logger.info(f"Successfully populated database with {total_added} sample schedules")
            
            session.close()
            
        except Exception as e:
            self.logger.error(f"Error populating sample data: {e}")
            session.close()
            raise
    


    def get_available_slots(self, position: str = "Python Developer", start_date: Optional[date] = None, end_date: Optional[date] = None, excluded_slots: List[str] = None) -> List[Dict[str, Any]]:
        """
        Get available interview slots.
        
        Args:
            position: Job position to filter by
            start_date: Start date for search
            end_date: End date for search
            
        Returns:
            List of available slots
        """
        try:
            if not self.is_connected:
                raise Exception("Database not connected. Cannot get available slots without database connection.")
            
            if not start_date:
                start_date = date.today()
            if not isinstance(start_date, date):
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            
            if not end_date:
                end_date = start_date + timedelta(days=14)
            if not isinstance(end_date, date):
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

            if not excluded_slots:
                excluded_slots = []
            if not isinstance(excluded_slots, list):
                excluded_slots = [excluded_slots]
        
       
            session = self.Session()
            
            query = session.query(Schedules).filter(Schedules.available == True)
            
            if position:
                query = query.filter(Schedules.position == position)
            
            if start_date:
                query = query.filter(Schedules.date >= start_date)
            
            if end_date:
                query = query.filter(Schedules.date <= end_date)
            if excluded_slots:
                # Convert excluded_slots to datetime objects for comparison
                excluded_dates = [datetime.strptime(slot, '%Y-%m-%d %H:%M').date() for slot in excluded_slots]
                query = query.filter(~Schedules.date.in_(excluded_dates))
            
            query = query.order_by(Schedules.date, Schedules.time)
            
            #log query with parameters            
            if self.database_type == 'mssql':
                self.logger.debug(query.statement.compile(dialect=mssql.dialect(), compile_kwargs={"literal_binds": True}))
            elif self.database_type == 'sqlite':
                self.logger.debug(query.statement.compile(dialect=sqlite.dialect(), compile_kwargs={"literal_binds": True}))
            else:
                self.logger.debug(f"Query to run: {query}, Parameters: {query.params}")


            # Fetch results
            if not query:
                self.logger.error(f"query undefined")
                return []

            # Fetch all available slots 
            slots = query.all()
            
            # Group slots by date and limit to next 5 available dates
            date_groups = {}
            for slot in slots:
                date_str = slot.date.strftime('%Y-%m-%d')
                if date_str not in date_groups:
                    date_groups[date_str] = []
                date_groups[date_str].append({
                    'id': slot.ScheduleID,
                    'date': slot.date.strftime('%Y-%m-%d'),
                    'time': slot.time.strftime('%H:%M:%S'),
                    'position': slot.position,
                    'available': slot.available
                })
            
            # Take only the first 5 dates
            sorted_dates = sorted(date_groups.keys())
            limited_dates = sorted_dates[:5]
            
            result = []
            for date_key in limited_dates:
                result.extend(date_groups[date_key])
            
            session.close()
            self.logger.debug(f"Retrieved {len(result)} available slots for position '{position}' from {start_date} to {end_date} (limited to 5 dates)")
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting available slots: {e}")
            return []
    
    def _get_mock_slots(self, position: str, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """
        Get mock slots for testing when database is not available.
        
        Args:
            position: Job position to filter by
            start_date: Start date for search
            end_date: End date for search
            
        Returns:
            List of mock available slots
        """
        self.logger.warning("Using mock slots due to database error")
        
        # Generate mock slots for the next 5 days
        mock_slots = []
        current_date = start_date
        
        for i in range(5):
            if current_date > end_date:
                break
                
            # Only add slots for Tue-Fri & Sun
            weekday = current_date.weekday()
            if weekday in [1, 2, 3, 6]:  # Tuesday, Wednesday, Thursday, Sunday
                for hour in [9, 10, 11, 12, 13, 14, 15, 16]:
                    mock_slots.append({
                        'id': i * 8 + hour,
                        'date': current_date.strftime('%Y-%m-%d'),
                        'time': f'{hour:02d}:00:00',
                        'position': position,
                        'available': True
                    })
            
            current_date += timedelta(days=1)
        
        return mock_slots
    


    def set_schedule(self, position, slot, candidate_phone, recruiter_phone) -> bool:
        """
        Set a schedule for a user.
        
        Args:
            position: Job position for the schedule
            slot: Slot information (date and time) - can be string like '2025-08-13 13:00' or dict
            candidate_phone: Phone number of the candidate
            recruiter_phone: Phone number of the recruiter
            
        Returns:
            True if schedule set successfully, False otherwise
        """
        # Normalize phone number for consistent storage
        normalized_phone = self._normalize_phone_number(candidate_phone)
        self.logger.info(f"set_schedule: original phone '{candidate_phone}' normalized to '{normalized_phone}'")
        
        if not self.is_connected:
            raise Exception("Database not connected. Cannot set schedule without database connection.")
        
        try:
            session = self.Session()
            
            # Parse slot if it's a string (format: '2025-08-13 13:00')
            if isinstance(slot, str):
                try:
                    slot_datetime = datetime.strptime(slot, '%Y-%m-%d %H:%M')
                    slot_date = slot_datetime.date()
                    slot_time = slot_datetime.time()
                except ValueError as e:
                    self.logger.error(f"Invalid slot format '{slot}': {e}")
                    session.close()
                    return False
            elif isinstance(slot, dict):
                # Handle dictionary format
                slot_date = datetime.strptime(slot['date'], '%Y-%m-%d').date()
                slot_time = datetime.strptime(slot['time'], '%H:%M:%S').time()
            else:
                self.logger.error(f"Invalid slot type: {type(slot)}")
                session.close()
                return False
            
            # Check if slot is available
            existing_slot = session.query(Schedules).filter(
                Schedules.date == slot_date,
                Schedules.time == slot_time,
                Schedules.position == position,
                Schedules.available == True
            ).first()
            
            if existing_slot:
                slot_booked = self.book_slot(existing_slot.ScheduleID, candidate_phone, recruiter_phone)
                session.close()
                if slot_booked:
                    self.logger.info(f"Slot booked successfully for {position} on {slot_date} at {slot_time}")
                    return True
                else:
                    self.logger.warning(f"Failed to book slot for {position} on {slot_date} at {slot_time}")
                    return False
            else:
                self.logger.warning(f"Slot not available for {position} on {slot_date} at {slot_time}")
                session.close()
                return False
        except SQLAlchemyError as e:
            self.logger.error(f"SQLAlchemy error setting schedule: {e}")
            if session:
                session.rollback()
                session.close()
            return False
        
        #End of set_schedule method

    def book_slot(self, slot_id: int, candidate_phone: str, recruiter_phone: str) -> bool:
        """
        Book a slot by marking it as unavailable.
        
        Args:
            slot_id: ID of the slot to book
            
        Returns:
            True if booking successful, False otherwise
        """
        if not self.is_connected:
            raise Exception("Database not connected. Cannot book slot without database connection.")
        
        try:
            session = self.Session()
            
            slot = session.query(Schedules).filter(Schedules.ScheduleID == slot_id).first()
            if slot and slot.available:
                slot.available = False
                session.commit()
                # Create an interview record
                interview = {
                    'ScheduleID': slot.ScheduleID,
                    'CandidatePhone': candidate_phone,
                    'RecruiterPhone': recruiter_phone
                }
                session.execute(
                    text("INSERT INTO Interviews (ScheduleID, CandidatePhone, RecruiterPhone) VALUES (:ScheduleID, :CandidatePhone, :RecruiterPhone)"),
                    interview
                )
                session.commit()
                self.logger.info(f"Slot {slot_id} booked successfully for candidate {candidate_phone} with recruiter {recruiter_phone}")
                session.close()
                return True
            else:
                session.close()
                return False
                
        except Exception as e:
            self.logger.error(f"Error booking slot: {e}")
            return False
        except SQLAlchemyError as e:
            self.logger.error(f"SQLAlchemy error booking slot: {e}")
            if session:
                session.rollback()
                session.close()
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error booking slot: {e}")
            if session:
                session.rollback()
                session.close()
            return False
    # End of book_slot method

    def delete_schedules(self, candidate_phone: str) -> bool:
        """
        Delete a candidate's schedules and mark them as available.

        Args:
            candidate_phone: Phone number of the candidate
            
        Returns:
            True if deletion successful, False otherwise
        """
        if not self.is_connected:
            raise Exception("Database not connected. Cannot delete schedules without database connection.")
        
        try:
            session = self.Session()
            # Check if the candidate has any interviews scheduled
            if not candidate_phone:
                self.logger.warning("Candidate phone number is empty, cannot delete schedules")
                return False
            # Ensure candidate_phone is a string
            if not isinstance(candidate_phone, str):
                self.logger.warning(f"Invalid candidate phone number type: {type(candidate_phone)}")
                return False
            candidate_phone = candidate_phone.strip()
            if not candidate_phone:
                self.logger.warning("Candidate phone number is empty after stripping, cannot delete schedules")
                return False
            # Query to find the candidate's schedules
            self.logger.info(f"Attempting to delete schedules for candidate {candidate_phone}")
            interviews = session.query(Interviews).filter(Interviews.CandidatePhone == candidate_phone).all()
            if not interviews:
                self.logger.info(f"No interviews found for candidate {candidate_phone}")
                return False
            # Get all schedules associated with the candidate's interviews
            schedule_ids = [interview.ScheduleID for interview in interviews]
            schedules = session.query(Schedules).filter(Schedules.ScheduleID.in_(schedule_ids)).all()
            if not schedules:
                self.logger.info(f"No schedules found for candidate {candidate_phone}")
                session.close()
                return False
            # Delete all interview records for the candidate
            for interview in interviews:
                session.delete(interview)
            # Delete all schedules for the candidate
            for schedule in schedules:
                session.delete(schedule)
            # Commit the changes
            session.commit()
            # After deletion, mark schedules as available
            # Re-query schedules to mark them as available
            schedules = session.query(Schedules).filter(Schedules.ScheduleID.in_(schedule_ids)).all()
            if not schedules:
                self.logger.info(f"No schedules found for candidate {candidate_phone} after deletion")
                session.close()
                return False
            # Ensure all schedules are marked as available
            # This is to ensure that the schedules are marked as available after deletion
            if not isinstance(schedules, list):
                self.logger.warning(f"Expected list of schedules, got {type(schedules)}")
                session.close()
                return False
            if not all(isinstance(schedule, Schedules) for schedule in schedules):
                self.logger.warning("Not all items in schedules are of type Schedules")
                session.close()
                return False
            # Mark schedules as available   
            for schedule in schedules:
                schedule.available = True
            # Commit the changes
            session.commit()
            session.close()
            self.logger.info(f"Schedules deleted successfully for candidate {candidate_phone}")
            return True

        except Exception as e:
            self.logger.error(f"Error deleting schedule: {e}")
            return False
        # End of delete_schedules method

    
    def get_schedule(self, candidate_phone: str) -> Optional[Dict[str, Any]]:
        """
        Get the schedule for a candidate.
        
        Args:
            candidate_phone: Phone number of the candidate
            
        Returns:
            Schedule details if found, None otherwise
        """
        # Normalize phone number for consistent lookup
        normalized_phone = self._normalize_phone_number(candidate_phone)
        self.logger.info(f"get_schedule: original phone '{candidate_phone}' normalized to '{normalized_phone}'")
        
        if not self.is_connected:
            raise Exception("Database not connected. Cannot get schedule without database connection.")
        
        try:
            session = self.Session()
            
            # Query for the candidate's interview and schedule
            # First get the interview record
            interview_query = text("""
                SELECT i.InterviewID, i.ScheduleID, i.CandidatePhone, i.RecruiterPhone,
                       s.date, s.time, s.position
                FROM Interviews i
                JOIN Schedules s ON i.ScheduleID = s.ScheduleID
                WHERE i.CandidatePhone = :candidate_phone
            """)
            
            result = session.execute(interview_query, {"candidate_phone": candidate_phone}).first()
            
            if result:
                # Handle both SQLite (string) and MSSQL (date/time objects) formats
                date_str = None
                time_str = None
                
                if result.date:
                    if hasattr(result.date, 'strftime'):
                        # It's a date object (MSSQL)
                        date_str = result.date.strftime('%Y-%m-%d')
                    else:
                        # It's already a string (SQLite)
                        date_str = str(result.date)
                
                if result.time:
                    if hasattr(result.time, 'strftime'):
                        # It's a time object (MSSQL)
                        time_str = result.time.strftime('%H:%M:%S')
                    else:
                        # It's already a string (SQLite)
                        time_str = str(result.time)
                
                schedule_data = {
                    'id': result.ScheduleID,
                    'date': date_str,
                    'time': time_str,
                    'position': result.position,
                    'candidate_phone': result.CandidatePhone,
                    'recruiter_phone': result.RecruiterPhone
                }
                session.close()
                self.logger.info(f"Found scheduled interview for {candidate_phone}: {schedule_data}")
                return schedule_data
            else:
                session.close()
                self.logger.info(f"No scheduled interview found for {candidate_phone}")
                return None
            
        except Exception as e:
            self.logger.error(f"Error getting schedule for {candidate_phone}: {e}")
            if 'session' in locals():
                session.close()
            return None

    # End of DatabaseManager class

# Global database manager instance
_db_manager = None


def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager 


def close(self):
        """Close the database connection."""
        if self.engine:
            self.engine.dispose()
            self.logger.info("Database connection closed")
        else:
            self.logger.warning("No database connection to close")
        self.is_connected = False
        self.Session = None
        self.engine = None
    # End of close method