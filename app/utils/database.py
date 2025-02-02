from supabase import create_client, Client
from datetime import datetime
from config import SUPABASE_URL, SUPABASE_KEY

print(SUPABASE_URL)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def check_user_in_db(user_id):
    response = supabase.table("users").select("user_id, role_id, name, language").eq("user_id", user_id).execute()
    return response.data if response.data else None

def save_user_to_db(user_id, name, phone_number):
    supabase.table("users").insert({
        "user_id": user_id,
        "name": name,
        "phone_number": phone_number,
        "role_id": 3
    }).execute()

def save_event_to_db(event_time, spaces):
    # Create the event and save it to the database
    response = supabase.table("events").insert({
        "event_datetime": event_time.isoformat(),
        "spaces": spaces,
        "status": 'active'  # Optional: Set status
    }).execute()
    return response

def get_upcoming_schedules(user_id):
    now = datetime.now()
    response = supabase.table("schedule").select("*").eq("user_id", user_id).gte("schedule_time", now.isoformat()).execute()
    return response.data if response.data else []

def get_schedule_by_id(schedule_id):
    response = supabase.table("schedule").select("*").eq("id", schedule_id).execute()
    return response.data[0] if response.data else None

def delete_schedule_from_db(schedule_id):
    # Deleting the schedule with the specific schedule_id
    response = supabase.table("schedule").delete().eq("id", schedule_id).execute()

    # Log the entire response object for debugging
    print(f"Delete Response: {response}")

    # Check if there is an error attribute, which will be present in some cases
    if hasattr(response, 'error') and response.error:
        raise Exception(f"Error deleting schedule: {response.error}")

    # If no error, check the status code
    if hasattr(response, 'status_code') and response.status_code != 200:
        raise Exception(f"Error deleting schedule: {response.json()}")

async def update_existing_event(schedule_time, schedule_id):
    # Update the event in the database (for editing)
    response = supabase.table("events").update({"event_datetime": schedule_time.isoformat()}).eq('event_id', schedule_id).execute()
    return response

async def update_event_spaces(event_time, spaces, schedule_id):
    # Update event spaces in the database (for editing)
    response = supabase.table("events").update({"spaces": spaces}).eq('event_id', schedule_id).execute()
    return response


async def get_event_by_id(event_id):
    """Fetch the event from the database by event_id."""
    response = supabase.table('events').select('*').eq('event_id', event_id).execute()
    # Log the response for debugging
    print(f"Event fetch response: {response}")

    if hasattr(response, 'data') and response.data:
        return response.data[0]  # Return the first (and only) result
    return None

async def delete_related_records(event_id):
    """Delete related records from bookings, waiting lists, and blacklists."""
    # Delete related bookings
    response = supabase.table('bookings').delete().eq('event_id', event_id).execute()
    print(f"Bookings delete response: {response}")
    if hasattr(response, 'error') and response.error:
        raise Exception(f"Error deleting related bookings: {response.error}")

    # Delete related waiting lists
    response = supabase.table('waiting_lists').delete().eq('event_id', event_id).execute()
    print(f"Waiting lists delete response: {response}")
    if hasattr(response, 'error') and response.error:
        raise Exception(f"Error deleting related waiting lists: {response.error}")

    # Delete related blacklists (if any)
    response = supabase.table('black_lists').delete().in_('user_id', supabase.table('bookings').select('user_id').eq('event_id', event_id).execute().data).execute()
    print(f"Blacklists delete response: {response}")
    if hasattr(response, 'error') and response.error:
        raise Exception(f"Error deleting related blacklists: {response.error}")

async def delete_event_from_db(event_id):
    """Delete the event from the events table."""
    response = supabase.table('events').delete().eq('event_id', event_id).execute()
    print(f"Event delete response: {response}")
    if hasattr(response, 'error') and response.error:
        raise Exception(f"Error deleting event: {response.error}")

async def log_audit_event(table_name, record_id, action, old_data, new_data, user_id):
    """Log an audit event to track the deletion."""
    audit_log = {
        'table_name': table_name,
        'record_id': record_id,
        'action': action,
        'old_data': old_data,
        'new_data': new_data,
        'user_id': user_id,
    }
    response = supabase.table('audit_logs').insert(audit_log).execute()
    print(f"Audit log insert response: {response}")
    if hasattr(response, 'error') and response.error:
        raise Exception(f"Error logging audit event: {response.error}")