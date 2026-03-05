from pydantic import BaseModel
from typing import List, Any, Dict, Optional, Literal

from datetime import datetime


class Education(BaseModel):
    degree: Optional[str] = None
    branch: Optional[str] = None
    college: Optional[str] = None


class Project(BaseModel):
    title: Optional[str] = None
    desc: Optional[str] = None


class Profile(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    linkedin_link: Optional[str] = None
    github_link: Optional[str] = None
    preferences: Optional[dict] = None
    skills: Optional[list[str]] = None
    education: Optional[list[Education]] = None
    projects: Optional[list[Project]] = None


class Personality(BaseModel):
    completed: bool = False
    scores: Optional[Dict[str, float]] = None
    type: Optional[str] = None


class RegisterReq(BaseModel):
    email: str
    password: str
    profile: Profile
    personality: Personality = Personality()


class User(BaseModel):
    id: str
    email: str
    password: str
    profile: Profile = Profile()
    personality: Personality = Personality()


class Answers(BaseModel):
    answers: List[Dict[str, Any]]


class LoginReq(BaseModel):
    email: str
    password: str
