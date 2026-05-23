#!/usr/bin/env python
from pathlib import Path
from pydantic import BaseModel
from crewai.flow import Flow, listen, start
from diagramas_uml.crews.crew_analisis.src.crew_analisis.crew import CrewAnalisis
from diagramas_uml.crews.crew_desarrollo.src.crew_desarrollo.crew import CrewDesarrollo

class UMLState(BaseModel):
    system_description: str = ""
    architecture_report: str = ""
    uml_code: str = ""
    deployment_log: str = ""

class UMLFlow(Flow[UMLState]):

    @start()
    def load_system_description(self):
        print("Cargando descripción del sistema desde system.txt...")
        try:
            with open("system.txt", "r", encoding="utf-8") as f:
                self.state.system_description = f.read().strip()
            print(f"Sistema a analizar: {self.state.system_description[:50]}...")
        except FileNotFoundError:
            print("Error: No se encontró el archivo system.txt en la raíz.")
            self.state.system_description = "Sistema de restaurante básico"

    @listen(load_system_description)
    def analyze_architecture(self):
        print("Iniciando Crew de Análisis...")
        result = (
            CrewAnalisis()
            .crew_analisis()
            .kickoff(inputs={"system": self.state.system_description})
        )
        self.state.architecture_report = result.raw
        print("Análisis de arquitectura completado.")

    @listen(analyze_architecture)
    def generate_diagrams(self):
        print("Iniciando Crew de Desarrollo (Generación y Despliegue)...")
        result = (
            CrewDesarrollo()
            .crew()
            .kickoff(inputs={
                "architecture_report": self.state.architecture_report,
                "system_name": self.state.system_description[:20] #
            })
        )
        self.state.deployment_log = result.raw
        print("Generación y despliegue completado.")

    @listen(generate_diagrams)
    def save_final_results(self):
        print("Guardando logs finales...")
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        with open(output_dir / "arquitectura_reporte.md", "w", encoding="utf-8") as f:
            f.write(self.state.architecture_report)
            
        with open(output_dir / "despliegue_log.md", "w", encoding="utf-8") as f:
            f.write(self.state.deployment_log)
            
        print("Proceso finalizado. Resultados en la carpeta 'output' y en Google Drive.")

def kickoff():
    uml_flow = UMLFlow()
    uml_flow.kickoff()

if __name__ == "__main__":
    kickoff()
