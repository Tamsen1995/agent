from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Agent(Base):
    __tablename__ = 'agents'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    x_position = Column(Float)
    y_position = Column(Float)
    interaction_count = Column(Integer, default=0)
    memories = relationship("Memory", back_populates="agent")
    reflections = relationship("Reflection", back_populates="agent")

class Memory(Base):
    __tablename__ = 'memories'
    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey('agents.id'))
    type = Column(String)
    content = Column(Text)
    timestamp = Column(DateTime)
    emotional_state = Column(String)
    relevance = Column(Float)
    agent = relationship("Agent", back_populates="memories")

class Reflection(Base):
    __tablename__ = 'reflections'
    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey('agents.id'))
    content = Column(Text)
    timestamp = Column(Float)
    agent = relationship("Agent", back_populates="reflections")
