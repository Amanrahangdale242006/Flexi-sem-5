import uuid
import datetime
from icalendar import Calendar, Event, vCalAddress, vText
from backend.app.models import Interview

class CalendarService:
    @staticmethod
    def generate_ics(interview: Interview) -> bytes:
        """
        Generates standard RFC 5545 .ics calendar data for an interview.
        """
        cal = Calendar()
        cal.add('prodid', '-//Automated Interview Scheduling System//EN')
        cal.add('version', '2.0')
        cal.add('calscale', 'GREGORIAN')
        cal.add('method', 'REQUEST')

        event = Event()
        job_title = interview.job.title if interview.job else "Interview"
        candidate_name = interview.candidate.name if interview.candidate else "Candidate"
        interviewer_name = interview.interviewer.name if interview.interviewer else "Interviewer"

        summary = f"Interview: {candidate_name} & {interviewer_name} ({job_title})"
        description = (
            f"Automated Interview Confirmation\n\n"
            f"Position: {job_title}\n"
            f"Candidate: {candidate_name} ({interview.candidate.email if interview.candidate else ''})\n"
            f"Interviewer: {interviewer_name} ({interview.interviewer.email if interview.interviewer else ''})\n"
            f"Video Meeting Link: {interview.meeting_link}\n\n"
            f"Notes: {interview.notes or 'No additional notes'}\n"
        )

        event.add('summary', summary)
        event.add('description', description)
        event.add('dtstart', interview.start_time)
        event.add('dtend', interview.end_time)
        event.add('dtstamp', datetime.datetime.utcnow())
        event.add('uid', f"interview-{interview.id}-{uuid.uuid4()}@autoschedule.ai")
        event.add('location', vText(interview.meeting_link))
        event.add('status', 'CONFIRMED')

        if interview.interviewer:
            organizer = vCalAddress(f"MAILTO:{interview.interviewer.email}")
            organizer.params['cn'] = vText(interview.interviewer.name)
            event.add('organizer', organizer)

        if interview.candidate:
            attendee = vCalAddress(f"MAILTO:{interview.candidate.email}")
            attendee.params['cn'] = vText(interview.candidate.name)
            attendee.params['ROLE'] = vText('REQ-PARTICIPANT')
            event.add('attendee', attendee)

        cal.add_component(event)
        return cal.to_ical()
