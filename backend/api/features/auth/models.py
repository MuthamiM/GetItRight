from sqlalchemy import Column, String, Integer, Float
from backend.api.core.database import Base

class UserModel(Base):
    __tablename__ = "Users"

    Id = Column(String, primary_key=True, index=True)
    FullName = Column(String, nullable=False)
    Email = Column(String, unique=True, index=True, nullable=False)
    Password = Column(String, nullable=False)
    PhoneNumber = Column(String, nullable=True)
    IpAddress = Column(String, nullable=True)
    Latitude = Column(Float, nullable=True)
    Longitude = Column(Float, nullable=True)
    DeviceDetails = Column(String, nullable=True)
    Role = Column(String, nullable=False, default="Customer")
    Plan = Column(String, nullable=False, default="free")
    PlanName = Column(String, nullable=False, default="Civic Starter")
    Organization = Column(String, nullable=True, default="Independent")
    CreatedAt = Column(String, nullable=False)
    Status = Column(String, nullable=False, default="Active")
    TotalPollsCreated = Column(Integer, default=0)
    TotalVotesReceived = Column(Integer, default=0)
    VoterQuota = Column(Integer, default=1000)
    PollsQuota = Column(Integer, default=5)
    ConsoleUrl = Column(String, nullable=False, default="/console/community.html")
    LastLogin = Column(String, nullable=True, default="Just now")
