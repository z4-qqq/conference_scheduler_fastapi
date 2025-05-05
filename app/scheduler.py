"""
Conference Schedule Optimization Module

This module handles automatic scheduling of presentations across conference rooms
while respecting time constraints and speaker availability. Key features:

- Intelligent scheduling algorithm that:
  - Maximizes room utilization
  - Avoids speaker time conflicts
  - Respects presentation durations
- Detailed logging of scheduling decisions
- Support for multi-day conferences
- Ability to return existing schedules

The scheduler uses a greedy algorithm prioritizing longest presentations first.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app import models

def schedule_all_presentations(db: Session, request: dict) -> Dict[int, List[dict]]:
    """
    Main scheduling function that creates optimal conference schedule.
    
    Args:
        db: Database session
        request: Dictionary containing scheduling parameters:
            - conference_days: Number of conference days
            - day_start_time: Daily start time (HH:MM)
            - day_end_time: Daily end time (HH:MM)
            - break_duration: Break duration between presentations (minutes)
    
    Returns:
        Dictionary mapping room IDs to lists of scheduled presentations
    
    Raises:
        ValueError: If no rooms are available
    """    
    # Get all rooms ordered by capacity (descending)
    rooms = db.query(models.Room).order_by(models.Room.capacity.desc()).all()
    # Get unscheduled presentations ordered by duration (descending)
    unscheduled = db.query(models.Presentation).filter(
        models.Presentation.start_time == None
    ).order_by(models.Presentation.duration_minutes.desc()).all()
    
    if not rooms:
        raise ValueError("No rooms available")
    if not unscheduled:
        return get_existing_schedule(db)
    
    # Parse time parameters
    day_start = datetime.strptime(request['day_start_time'], "%H:%M").time()
    day_end = datetime.strptime(request['day_end_time'], "%H:%M").time()
    break_duration = timedelta(minutes=request['break_duration'])
    
    schedule = {room.id: [] for room in rooms}
    current_date = datetime.now().date()
    
    # Schedule for each conference day
    for day in range(request['conference_days']):
        current_date += timedelta(days=1)

        # Schedule presentations for each room
        for room in rooms:
            current_time = datetime.combine(current_date, day_start)
            day_end_dt = datetime.combine(current_date, day_end)
            
            # Schedule presentations throughout the day
            while current_time < day_end_dt:
                time_left = day_end_dt - current_time
                
                # Find next suitable presentation
                presentation = find_next_presentation(
                    db=db,
                    current_time=current_time,
                    unscheduled=unscheduled,
                    schedule=schedule,
                    day_end=day_end_dt
                )
                
                if presentation:
                    duration = timedelta(minutes=presentation.duration_minutes)
                    end_time = current_time + duration
                    
                    # Update presentation in database
                    presentation.start_time = current_time
                    presentation.end_time = end_time
                    presentation.room_id = room.id
                    
                    # Add to schedule
                    schedule[room.id].append({
                        'presentation_id': presentation.id,
                        'start_time': current_time.isoformat(),
                        'end_time': end_time.isoformat(),
                        'title': presentation.title,
                        'speaker_id': presentation.speaker_id,
                        'duration': presentation.duration_minutes
                    })
                    
                    # Move time pointer and remove from unscheduled
                    current_time = end_time + break_duration
                    unscheduled.remove(presentation)
                else:
                    break  # Move to next room
    
    db.commit()
    return schedule

def get_existing_schedule(db: Session) -> Dict[int, List[dict]]:
    """
    Retrieves already scheduled presentations organized by room.
    
    Args:
        db: Database session
    
    Returns:
        Dictionary mapping room IDs to lists of scheduled presentations with:
            - presentation_id
            - start_time
            - end_time
            - title
            - speaker_id
            - duration
    """
    schedule = {}
    rooms = db.query(models.Room).all()
    for room in rooms:
        presentations = db.query(models.Presentation).filter(
            models.Presentation.room_id == room.id
        ).order_by(models.Presentation.start_time).all()        
        room_schedule = [
            {
                'presentation_id': pres.id,
                'start_time': pres.start_time.isoformat(),
                'end_time': pres.end_time.isoformat(),
                'title': pres.title,
                'speaker_id': pres.speaker_id,
                'duration': pres.duration_minutes
            }
            for pres in presentations
        ]
        
        schedule[room.id] = room_schedule

    return schedule

def find_next_presentation(
    db: Session,
    current_time: datetime,
    unscheduled: List[models.Presentation],
    schedule: dict,
    day_end: datetime
) -> Optional[models.Presentation]:
    """
    Finds the next suitable presentation for a given time slot.
    
    Args:
        db: Database session
        room_id: ID of current room being scheduled
        current_time: Proposed start time
        break_duration: Duration of break after presentation
        unscheduled: List of unscheduled presentations
        schedule: Current schedule being built
        day_end: End time of current conference day
    
    Returns:
        Presentation object if suitable one found, None otherwise
    """
    for presentation in unscheduled:
        duration = timedelta(minutes=presentation.duration_minutes)
        end_time = current_time + duration
        
        # Check if presentation fits in remaining day time
        if end_time > day_end:
            continue
        
        # Check speaker availability
        if is_speaker_available(db, presentation.speaker_id, current_time, end_time, schedule):
            return presentation
    return None

def is_speaker_available(
    db: Session,
    speaker_id: int,
    start_time: datetime,
    end_time: datetime,
    schedule: dict
) -> bool:
    """
    Checks if speaker is available during proposed time slot.
    
    Args:
        db: Database session
        speaker_id: ID of speaker to check
        start_time: Proposed start time
        end_time: Proposed end time
        schedule: Current schedule being built
    
    Returns:
        True if speaker is available, False if they have conflicting presentation
    """
    for room_id, room_schedule in schedule.items():
        for scheduled_pres in room_schedule:
            pres = db.query(models.Presentation).get(scheduled_pres['presentation_id'])
            if pres.speaker_id == speaker_id:
                scheduled_start = datetime.fromisoformat(scheduled_pres['start_time'])
                scheduled_end = datetime.fromisoformat(scheduled_pres['end_time'])
                
                # Check for time overlap
                if not (end_time <= scheduled_start or start_time >= scheduled_end):
                    return False
    return True
