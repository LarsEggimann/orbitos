from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import io
import csv
import pandas as pd

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./measurements.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database models
class MeasurementSet(Base):
    __tablename__ = "measurement_sets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    measurements = relationship("Measurement", back_populates="measurement_set")

class Measurement(Base):
    __tablename__ = "measurements"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    value1 = Column(Float, nullable=True)
    value2 = Column(Float, nullable=True)
    # Add more value columns as needed
    
    measurement_set_id = Column(Integer, ForeignKey("measurement_sets.id"), nullable=False)
    measurement_set = relationship("MeasurementSet", back_populates="measurements")

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic models
class MeasurementSetCreate(BaseModel):
    name: str
    description: Optional[str] = None

class MeasurementSetResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    
    class Config:
        orm_mode = True

class MeasurementCreate(BaseModel):
    timestamp: datetime
    value1: Optional[float] = None
    value2: Optional[float] = None
    # Add more fields as needed

class MeasurementResponse(BaseModel):
    id: int
    timestamp: datetime
    value1: Optional[float] = None
    value2: Optional[float] = None
    measurement_set_id: int
    
    class Config:
        orm_mode = True

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# FastAPI app
app = FastAPI(title="Time Series Measurements API")

# Endpoints for measurement sets
@app.post("/measurement-sets/", response_model=MeasurementSetResponse)
def create_measurement_set(measurement_set: MeasurementSetCreate, db: Session = Depends(get_db)):
    db_measurement_set = MeasurementSet(
        name=measurement_set.name,
        description=measurement_set.description,
        created_at=datetime.utcnow()
    )
    db.add(db_measurement_set)
    db.commit()
    db.refresh(db_measurement_set)
    return db_measurement_set

@app.get("/measurement-sets/", response_model=List[MeasurementSetResponse])
def read_measurement_sets(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(MeasurementSet).offset(skip).limit(limit).all()

@app.get("/measurement-sets/{measurement_set_id}", response_model=MeasurementSetResponse)
def read_measurement_set(measurement_set_id: int, db: Session = Depends(get_db)):
    db_measurement_set = db.query(MeasurementSet).filter(MeasurementSet.id == measurement_set_id).first()
    if db_measurement_set is None:
        raise HTTPException(status_code=404, detail="Measurement set not found")
    return db_measurement_set

# Bulk measurements upload
@app.post("/measurement-sets/{measurement_set_id}/measurements/bulk")
def create_measurements_bulk(measurement_set_id: int, measurements: List[MeasurementCreate], db: Session = Depends(get_db)):
    # Check if measurement set exists
    db_measurement_set = db.query(MeasurementSet).filter(MeasurementSet.id == measurement_set_id).first()
    if db_measurement_set is None:
        raise HTTPException(status_code=404, detail="Measurement set not found")
    
    # Insert measurements
    db_measurements = [
        Measurement(
            timestamp=m.timestamp,
            value1=m.value1,
            value2=m.value2,
            measurement_set_id=measurement_set_id
        ) for m in measurements
    ]
    
    db.bulk_save_objects(db_measurements)
    db.commit()
    
    return {"inserted": len(measurements)}

# Query measurements
@app.get("/measurement-sets/{measurement_set_id}/measurements", response_model=List[MeasurementResponse])
def read_measurements(
    measurement_set_id: int, 
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 1000,
    db: Session = Depends(get_db)
):
    query = db.query(Measurement).filter(Measurement.measurement_set_id == measurement_set_id)
    
    if start_time:
        query = query.filter(Measurement.timestamp >= start_time)
    if end_time:
        query = query.filter(Measurement.timestamp <= end_time)
    
    return query.order_by(Measurement.timestamp).limit(limit).all()

# Export measurements to CSV (similar to your old system)
@app.get("/measurement-sets/{measurement_set_id}/export-csv")
def export_measurements_csv(
    measurement_set_id: int,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    # Query measurements
    query = db.query(Measurement).filter(Measurement.measurement_set_id == measurement_set_id)
    
    if start_time:
        query = query.filter(Measurement.timestamp >= start_time)
    if end_time:
        query = query.filter(Measurement.timestamp <= end_time)
    
    measurements = query.order_by(Measurement.timestamp).all()
    
    # Prepare CSV file
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(["timestamp", "value1", "value2"])
    
    # Write data
    for m in measurements:
        writer.writerow([m.timestamp.isoformat(), m.value1, m.value2])
    
    # Return CSV as downloadable file
    response = StreamingResponse(iter([output.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename=measurements_{measurement_set_id}.csv"
    
    return response

# Import measurements from CSV
@app.post("/measurement-sets/{measurement_set_id}/import-csv")
async def import_measurements_csv(
    measurement_set_id: int,
    file: bytes,
    db: Session = Depends(get_db)
):
    # Check if measurement set exists
    db_measurement_set = db.query(MeasurementSet).filter(MeasurementSet.id == measurement_set_id).first()
    if db_measurement_set is None:
        raise HTTPException(status_code=404, detail="Measurement set not found")
    
    # Load CSV into pandas DataFrame
    df = pd.read_csv(io.BytesIO(file))
    
    # Convert timestamps
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Create measurement objects
    measurements = []
    for _, row in df.iterrows():
        m = Measurement(
            timestamp=row['timestamp'],
            value1=row.get('value1'),
            value2=row.get('value2'),
            measurement_set_id=measurement_set_id
        )
        measurements.append(m)
    
    # Bulk insert
    db.bulk_save_objects(measurements)
    db.commit()
    
    return {"imported": len(measurements)}

# Endpoint for time-based aggregation and statistics
@app.get("/measurement-sets/{measurement_set_id}/stats")
def get_measurement_stats(
    measurement_set_id: int,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    group_by: str = Query("day", enum=["hour", "day", "week", "month"]),
    db: Session = Depends(get_db)
):
    # This is a simplified example - in a real app, you would use SQLAlchemy expressions
    # to do the aggregation directly in the database for better performance
    
    # Get raw measurements
    query = db.query(Measurement).filter(Measurement.measurement_set_id == measurement_set_id)
    
    if start_time:
        query = query.filter(Measurement.timestamp >= start_time)
    if end_time:
        query = query.filter(Measurement.timestamp <= end_time)
    
    measurements = query.all()
    
    # Load into pandas for easier aggregation
    data = {
        "timestamp": [m.timestamp for m in measurements],
        "value1": [m.value1 for m in measurements],
        "value2": [m.value2 for m in measurements]
    }
    df = pd.DataFrame(data)
    
    # Group by time period
    if group_by == "hour":
        df["period"] = df["timestamp"].dt.floor("H")
    elif group_by == "day":
        df["period"] = df["timestamp"].dt.floor("D")
    elif group_by == "week":
        df["period"] = df["timestamp"].dt.floor("W")
    elif group_by == "month":
        df["period"] = df["timestamp"].dt.floor("M")
    
    # Compute statistics
    stats = df.groupby("period").agg({
        "value1": ["mean", "min", "max", "count"],
        "value2": ["mean", "min", "max", "count"]
    }).reset_index()
    
    # Convert to dict for JSON response
    result = []
    for _, row in stats.iterrows():
        entry = {
            "period": row["period"].isoformat(),
            "value1": {
                "mean": row[("value1", "mean")],
                "min": row[("value1", "min")],
                "max": row[("value1", "max")],
                "count": row[("value1", "count")]
            },
            "value2": {
                "mean": row[("value2", "mean")],
                "min": row[("value2", "min")],
                "max": row[("value2", "max")],
                "count": row[("value2", "count")]
            }
        }
        result.append(entry)
    
    return result