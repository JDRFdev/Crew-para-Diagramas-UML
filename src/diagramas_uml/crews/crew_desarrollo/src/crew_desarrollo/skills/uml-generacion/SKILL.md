---
name: uml-generacion
description: Guía para la generación de código PlantUML.
metadata: 
  author: UD
  version: "1.0"
---

## PlantUML Generación Guidelines

Para generar código UML de alta calidad usando PlantUML, sigue estas reglas:

1. **Sintaxis PlantUML**: Usa siempre @startuml y @enduml.
2. **Claridad**: Los nombres de las clases y relaciones deben ser legibles.
3. **Relaciones**: 
   - Clase: `ClaseA <|-- ClaseB` (Herencia), `ClaseA *-- ClaseB` (Composición).
   - Secuencia: `Actor -> Sistema: Mensaje`.
4. **Iteración**: Genera cada diagrama como un bloque de código completo e independiente.
