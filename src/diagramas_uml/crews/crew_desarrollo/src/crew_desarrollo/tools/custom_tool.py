from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import os
import requests
import base64
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive.file']

class GoogleDriveUMLToolInput(BaseModel):
    """Esquema de entrada para GoogleDriveUMLTool."""
    plantuml_code: str = Field(..., description="El código PlantUML a convertir y subir.")
    project_name: str = Field(..., description="El nombre de la carpeta del proyecto.")
    diagram_type: str = Field(..., description="El tipo de diagrama (ej., Clases, Secuencia).")
    diagram_name: str = Field(..., description="El nombre del archivo del diagrama.")

class GoogleDriveUMLTool(BaseTool):
    name: str = "google_drive_uml_tool"
    description: str = (
        "Convierte código PlantUML a PNG y lo sube a una estructura de carpetas en Google Drive: "
        "Diagramas UML -> [Nombre del Proyecto] -> [Tipo de Diagrama] -> [Nombre del Diagrama].png"
    )
    args_schema: Type[BaseModel] = GoogleDriveUMLToolInput
    _folder_cache: dict = {}

    def _run(self, plantuml_code: str, project_name: str, diagram_type: str, diagram_name: str) -> str:
        try:
            import io
            # 1. Convertir PlantUML a PNG usando un renderizador público
            encoded_uml = self._encode_plantuml(plantuml_code)
            # El servidor estándar de PlantUML espera los datos codificados. 
            # No necesitamos ~1 si usamos el mapeo de alfabeto correcto.
            url = f"http://www.plantuml.com/plantuml/png/{encoded_uml}"
            response = requests.get(url)
            
            if response.status_code != 200:
                return f"Error al renderizar PlantUML: {response.status_code}"

            # Usar BytesIO para mantener la imagen en memoria
            image_stream = io.BytesIO(response.content)

            # 2. Autenticar con Google Drive
            service = self._get_drive_service()

            # 3. Crear estructura de carpetas y subir con caché para evitar duplicados
            root_id = self._get_or_create_folder(service, "Diagramas UML")
            project_id = self._get_or_create_folder(service, project_name, root_id)
            type_id = self._get_or_create_folder(service, diagram_type, project_id)

            file_metadata = {
                'name': f"{diagram_name}.png",
                'parents': [type_id]
            }
            
            from googleapiclient.http import MediaIoBaseUpload
            media = MediaIoBaseUpload(image_stream, mimetype='image/png', resumable=True)
            file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()

            return f"Se subió con éxito {diagram_name}.png a Google Drive. Enlace de visualización: {file.get('webViewLink')}"

        except Exception as e:
            return f"Error en GoogleDriveUMLTool: {str(e)}"

    def _encode_plantuml(self, plantuml_code: str) -> str:
        """Codifica el código PlantUML para la URL del servidor usando el alfabeto base64 oficial personalizado."""
        import zlib
        # 1. Codificar en UTF-8
        # 2. Comprimir con Deflate (crudo, sin encabezados zlib)
        zlibbed_str = zlib.compress(plantuml_code.encode('utf-8'))
        compressed_string = zlibbed_str[2:-4]
        
        # 3. Mapeo personalizado de Base64
        return self._encode64(compressed_string)

    def _encode64(self, data: bytes) -> str:
        """Codificación oficial tipo base64 de PlantUML."""
        res = ""
        for i in range(0, len(data), 3):
            if i + 2 < len(data):
                res += self._append3bytes(data[i], data[i+1], data[i+2])
            elif i + 1 < len(data):
                res += self._append3bytes(data[i], data[i+1], 0)
            else:
                res += self._append3bytes(data[i], 0, 0)
        return res

    def _append3bytes(self, b1, b2, b3) -> str:
        c1 = b1 >> 2
        c2 = ((b1 & 0x3) << 4) | (b2 >> 4)
        c3 = ((b2 & 0xF) << 2) | (b3 >> 6)
        c4 = b3 & 0x3F
        res = ""
        res += self._encode6bit(c1 & 0x3F)
        res += self._encode6bit(c2 & 0x3F)
        res += self._encode6bit(c3 & 0x3F)
        res += self._encode6bit(c4 & 0x3F)
        return res

    def _encode6bit(self, b) -> str:
        if b < 10: return chr(48 + b)
        b -= 10
        if b < 26: return chr(65 + b)
        b -= 26
        if b < 26: return chr(97 + b)
        b -= 26
        if b == 0: return '-'
        if b == 1: return '_'
        return '?'

    def _get_drive_service(self):
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'client_secretXXXXX.json', SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        return build('drive', 'v3', credentials=creds)

    def _get_or_create_folder(self, service, folder_name, parent_id=None):
        # Verificación de caché para evitar la creación de duplicados en llamadas paralelas
        cache_key = f"{folder_name}_{parent_id}"
        if cache_key in self._folder_cache:
            return self._folder_cache[cache_key]

        query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        if parent_id:
            query += f" and '{parent_id}' in parents"
        
        results = service.files().list(q=query, spaces='drive', fields='files(id)').execute()
        files = results.get('files', [])

        if files:
            folder_id = files[0]['id']
        else:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            if parent_id:
                file_metadata['parents'] = [parent_id]
            file = service.files().create(body=file_metadata, fields='id').execute()
            folder_id = file.get('id')
        
        self._folder_cache[cache_key] = folder_id
        return folder_id
