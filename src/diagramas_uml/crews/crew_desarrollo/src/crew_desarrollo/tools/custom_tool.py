from crewai.tools import BaseTool
from typing import Type, ClassVar
from pydantic import BaseModel, Field
import os
import requests
import time
import threading
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

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
    
    # LOCK y CACHÉ compartidos entre todas las instancias de la herramienta
    _folder_cache: ClassVar[dict] = {}
    _lock: ClassVar[threading.Lock] = threading.Lock()

    def _run(self, plantuml_code: str, project_name: str, diagram_type: str, diagram_name: str) -> str:
        try:
            import io
            # 1. Convertir PlantUML a PNG
            encoded_uml = self._encode_plantuml(plantuml_code)
            url = f"http://www.plantuml.com/plantuml/png/{encoded_uml}"
            response = requests.get(url)
            
            if response.status_code != 200:
                return f"Error al renderizar PlantUML: {response.status_code}"

            image_stream = io.BytesIO(response.content)

            # 2. Autenticar con Google Drive
            service = self._get_drive_service()

            # 3. Estructura de carpetas con BLOQUEO para evitar duplicados en paralelo
            with self._lock:
                root_id = self._get_or_create_folder(service, "Diagramas UML")
                project_id = self._get_or_create_folder(service, project_name, root_id)
                type_id = self._get_or_create_folder(service, diagram_type, project_id)

            # 4. Subir o actualizar el archivo (evita duplicar el mismo diagrama)
            self._upload_or_update_file(service, f"{diagram_name}.png", type_id, image_stream)

            return f"Se subió con éxito {diagram_name}.png a Google Drive."

        except Exception as e:
            return f"Error en GoogleDriveUMLTool: {str(e)}"

    def _get_drive_service(self):
        # Intentar cuenta de servicio primero (sin ventanas)
        if os.path.exists('service_account.json'):
            creds = service_account.Credentials.from_service_account_file(
                'service_account.json', scopes=SCOPES)
            return build('drive', 'v3', credentials=creds)

        # Fallback a OAuth personal
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # Buscar cualquier archivo que empiece por client_secret y termine en .json
                client_secret_files = [f for f in os.listdir('.') if f.startswith('client_secret') and f.endswith('.json')]
                if not client_secret_files:
                    raise FileNotFoundError("No se encontró ningún archivo 'client_secret_XXX.json' en la raíz.")
                
                flow = InstalledAppFlow.from_client_secrets_file(client_secret_files[0], SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        
        return build('drive', 'v3', credentials=creds)

    def _get_or_create_folder(self, service, folder_name, parent_id=None):
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
            time.sleep(1) # Pausa para consistencia
        
        self._folder_cache[cache_key] = folder_id
        return folder_id

    def _upload_or_update_file(self, service, file_name, folder_id, image_stream):
        query = f"name = '{file_name}' and '{folder_id}' in parents and trashed = false"
        results = service.files().list(q=query, spaces='drive', fields='files(id)').execute()
        files = results.get('files', [])

        media = MediaIoBaseUpload(image_stream, mimetype='image/png', resumable=True)

        if files:
            file_id = files[0]['id']
            service.files().update(fileId=file_id, media_body=media).execute()
        else:
            file_metadata = {'name': file_name, 'parents': [folder_id]}
            service.files().create(body=file_metadata, media_body=media).execute()

    def _encode_plantuml(self, plantuml_code: str) -> str:
        import zlib
        zlibbed_str = zlib.compress(plantuml_code.encode('utf-8'))
        compressed_string = zlibbed_str[2:-4]
        return self._encode64(compressed_string)

    def _encode64(self, data: bytes) -> str:
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
