"""Room API routes — CRUD with per-centre filtering."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.teacher import Room
from app.schemas.class_room import RoomCreate, RoomUpdate, RoomResponse

router = APIRouter()


@router.get("/", response_model=list[RoomResponse])
async def list_rooms(
    centre_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Room)
    if centre_id:
        q = q.filter(Room.centre_id == centre_id)
    rooms = q.all()
    return [RoomResponse.model_validate(r.__dict__) for r in rooms]


@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(room_id: int, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return RoomResponse.model_validate(room.__dict__)


@router.post("/", response_model=RoomResponse, status_code=201)
async def create_room(data: RoomCreate, db: Session = Depends(get_db)):
    existing = db.query(Room).filter(
        Room.centre_id == data.centre_id, Room.name == data.name
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Room name already exists in this centre")
    room = Room(**data.model_dump())
    db.add(room)
    db.commit()
    db.refresh(room)
    return RoomResponse.model_validate(room.__dict__)


@router.put("/{room_id}", response_model=RoomResponse)
async def update_room(room_id: int, data: RoomUpdate, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(room, key, value)
    db.commit()
    db.refresh(room)
    return RoomResponse.model_validate(room.__dict__)


@router.delete("/{room_id}", status_code=204)
async def delete_room(room_id: int, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    db.delete(room)
    db.commit()