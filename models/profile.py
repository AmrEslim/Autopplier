from typing import List, Optional
from pydantic import BaseModel, Field

class ContactInfo(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    location: str

class Experience(BaseModel):
    title: str
    company: str
    start_date: str
    end_date: Optional[str] = None
    description: str
    skills_used: List[str] = []

class Education(BaseModel):
    institution: str
    degree: str
    field_of_study: str
    start_date: str
    end_date: Optional[str] = None

class UserProfile(BaseModel):
    contact_info: ContactInfo
    summary: str
    experience: List[Experience] = []
    education: List[Education] = []
    skills: List[str] = []
    preferred_salary: Optional[int] = None
    relocation: bool = False
    remote_only: bool = False
