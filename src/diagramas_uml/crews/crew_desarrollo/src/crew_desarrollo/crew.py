from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
import os
from diagramas_uml.config.llm_config import llm

@CrewBase
class CrewDesarrollo():
    """CrewDesarrollo crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def desarrollador_uml(self) -> Agent:
        base_dir = os.path.dirname(__file__)
        skill_path = os.path.abspath(os.path.join(base_dir, "skills", "uml-generacion"))
        return Agent(
            config=self.agents_config['desarrollador_uml'],
            llm=llm,
            skills=[skill_path],
            verbose=True
        )

    @agent
    def especialista_despliegue(self) -> Agent:
        from .tools.custom_tool import GoogleDriveUMLTool
        base_dir = os.path.dirname(__file__)
        skill_path = os.path.abspath(os.path.join(base_dir, "skills", "google-drive-despliegue"))
        return Agent(
            config=self.agents_config['especialista_despliegue'],
            llm=llm,
            skills=[skill_path],
            tools=[GoogleDriveUMLTool()],
            verbose=True
        )

    @task
    def generar_codigo_uml(self) -> Task:
        return Task(
            config=self.tasks_config['generar_codigo_uml'],
            verbose=True
        )

    @task
    def desplegar_diagramas(self) -> Task:
        return Task(
            config=self.tasks_config['desplegar_diagramas'],
            verbose=True
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
