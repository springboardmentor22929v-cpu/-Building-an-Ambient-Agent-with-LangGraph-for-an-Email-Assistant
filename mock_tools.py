"""
Mock Tools for Email Agent Testing
Provides mock implementations of various tools for email processing
"""

from langchain.tools import tool

class MockTools:
    def __init__(self):
        self.contacts = {
            "john.doe@company.com": {"name": "John Doe", "role": "Senior Developer", "department": "Engineering"},
            "sarah.smith@company.com": {"name": "Sarah Smith", "role": "Product Manager", "department": "Product"},
            "mike.johnson@company.com": {"name": "Mike Johnson", "role": "CEO", "department": "Executive"},
            "lisa.brown@company.com": {"name": "Lisa Brown", "role": "HR Manager", "department": "Human Resources"}
        }

        self.projects = {
            "website-redesign": {"status": "In Progress", "due_date": "2024-02-15", "progress": "75%"},
            "mobile-app": {"status": "Planning", "due_date": "2024-03-01", "progress": "20%"},
            "api-integration": {"status": "Completed", "due_date": "2024-01-30", "progress": "100%"}
        }

        self.company_info = {
            "support": "support@company.com",
            "hr": "hr@company.com",
            "sales": "sales@company.com",
            "legal": "legal@company.com"
        }

    def read_calendar(self, days_ahead: int = 7) -> str:
        """Mock calendar reading - returns upcoming events"""
        mock_events = [
            "Meeting with Product Team - Tomorrow 10:00 AM",
            "Client Presentation - Day 3, 2:00 PM",
            "Team Standup - Daily 9:00 AM",
            "Project Review - Day 5, 11:00 AM"
        ]
        return f"Upcoming events in next {days_ahead} days: {', '.join(mock_events[:min(days_ahead, len(mock_events))])}"

    def lookup_contact(self, email: str) -> str:
        """Mock contact lookup"""
        if email in self.contacts:
            contact = self.contacts[email]
            return f"Contact found: {contact['name']}, {contact['role']} in {contact['department']}"
        return f"Contact not found for email: {email}"

    def get_project_status(self, project_name: str = None) -> str:
        """Mock project status lookup"""
        if project_name and project_name in self.projects:
            project = self.projects[project_name]
            return f"Project '{project_name}': Status - {project['status']}, Progress - {project['progress']}, Due - {project['due_date']}"
        elif project_name:
            return f"Project '{project_name}' not found"
        else:
            # Return all projects
            statuses = [f"{name}: {info['status']} ({info['progress']})" for name, info in self.projects.items()]
            return f"All projects: {', '.join(statuses)}"

    def check_availability(self, person: str) -> str:
        """Mock availability check"""
        availability = {
            "john.doe": "Available next week",
            "sarah.smith": "Busy until Friday",
            "mike.johnson": "Available tomorrow afternoon",
            "lisa.brown": "Out of office this week"
        }
        return availability.get(person.lower().replace(" ", "."), f"Availability for {person}: Unknown")

    def get_company_info(self, department: str = None) -> str:
        """Mock company information lookup"""
        if department and department.lower() in self.company_info:
            return f"{department.title()} contact: {self.company_info[department.lower()]}"
        elif department:
            return f"No information found for department: {department}"
        else:
            contacts = [f"{dept.title()}: {email}" for dept, email in self.company_info.items()]
            return f"Company contacts: {', '.join(contacts)}"


def get_tool_descriptions() -> str:
    """Return descriptions of available tools for the agent"""
    return """
Available Tools:
- read_calendar(days_ahead): Read upcoming calendar events for the next X days (default 7)
- lookup_contact(email): Look up contact information by email address
- get_project_status(project_name): Get status of a specific project (optional project name)
- check_availability(person): Check availability of a person
- get_company_info(department): Get company contact information for a department (optional department)
- draft_response: Generate the final email response
"""
