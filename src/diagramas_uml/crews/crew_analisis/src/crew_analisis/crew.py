from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
import os

from diagramas_uml.config.llm_config import llm

@CrewBase
class CrewAnalisis():
    agents: list[BaseAgent]
    tasks: list[Task]
    
    @agent
    def analista_sistemas(self) -> Agent:
        base_dir = os.path.dirname(__file__)
        skill_path = os.path.abspath(os.path.join(base_dir, "skills", "uml-estructuracion"))
        
        return Agent(
            config=self.agents_config['analista_sistemas'],
            llm=llm,
            skills=[skill_path], 
            verbose=True
        )
    
    @task
    def arquitectura_uml(self) -> Task:
        return Task(
            config=self.tasks_config['arquitectura_UML'],
            verbose=True
        )
    
    @crew
    def crew_analisis(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
