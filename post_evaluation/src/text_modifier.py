"""
Modificador de Textos Legales

Este módulo utiliza GPT-4o para modificar textos legales de diferentes maneras
manteniendo o alterando aspectos específicos según el tipo de evaluación.
"""

import asyncio
from typing import Dict, Any
from openai import AzureOpenAI, AsyncAzureOpenAI
from configs.credentials_config import API_KEY, ENDPOINT, MODEL, DEPLOYMENT

class TextModifier:
    """
    Modificador de textos legales usando Azure OpenAI GPT-4o con prompts en español
    """
    
    def __init__(self):
        # Synchronous client
        self.azure_client = AzureOpenAI(
            api_version="2025-04-01-preview",
            azure_endpoint=ENDPOINT,
            api_key=API_KEY
        )
        # Async client
        self.async_azure_client = AsyncAzureOpenAI(
            api_version="2025-04-01-preview",
            azure_endpoint=ENDPOINT,
            api_key=API_KEY
        )
        
        self.prompts = {
            "formato_citas": """
Eres un editor de textos legales especializado. Modifica los formatos de las citas en el siguiente texto legal manteniendo EXACTAMENTE el mismo significado y contenido.

Solo cambia la sintaxis de las citas, no queremos que siempre sean iguales:

Cambios a realizar:
- Intercambia instancias de "art." por "artículo" o "artículo número"
- Intercambia instancias de "arts." por "artículos"
- Intercambia instancias de "ley 7046" por "ley nacional 7046" o "ley número 7046"
- Intercambia instancias de "Acuerdo Gral." por "Acuerdo General" o "Ac. Gral."
- En general, intercambia formas abreviadas por formas completas y viceversa
- Mantén todos los números de artículos y leyes EXACTAMENTE iguales
- NO cambies ningún otro contenido, solo el formato de las citas

Texto original:
{texto}

Texto modificado:
""",
            
            "redaccion_superficial": """
Eres un editor de textos legales. Reescribe el siguiente fallo judicial usando diferentes palabras y estructuras de oraciones, pero mantén:

1. TODAS las referencias de citas EXACTAMENTE iguales (no cambies "art. 3" o "ley 7046", etc.)
2. El mismo significado legal y conclusiones. El mensaje real del texto NO debe modificarse.
3. El mismo contenido fáctico y decisiones. Solo debes cambiar la redacción superficial, estructura de oraciones, sintaxis, etc.

Cambia:
- Estructura de oraciones y orden de palabras
- Sinónimos para términos no legales
- Organización de párrafos
- Estilo de redacción

Mantén SIN CAMBIOS:
- Todas las citas de artículos y leyes permanecen EXACTAMENTE iguales
- Conclusiones legales y decisiones
- Hallazgos fácticos
- Nombres, fechas, montos

Texto original:
{texto}

Texto reescrito:
""",
            
            "cambio_contenido": """
Eres un editor de textos legales. Reescribe el siguiente fallo judicial para discutir DIFERENTES cuestiones legales y llegar a DIFERENTES conclusiones, pero:

MANTÉN SIN CAMBIOS:
- TODAS las referencias de citas (art. 3, ley 7046, etc.) - deben aparecer en la misma forma
- El nombre del caso y estructura básica
- El formato y estructura del documento legal

CAMBIA COMPLETAMENTE:
- Las cuestiones legales que se deciden
- El razonamiento y conclusiones
- Las disputas fácticas (manteniendo las referencias de citas)
- Las decisiones/fallos finales

Hazlo sobre diferentes conceptos legales manteniendo los mismos artículos/leyes citados.

Texto original:
{texto}

Texto modificado con contenido diferente:
"""
        }
    
    async def modify_text(self, texto: str, tipo_modificacion: str) -> str:
        """
        Modifica un texto según el tipo de modificación especificado
        
        Args:
            texto: El texto legal a modificar
            tipo_modificacion: Tipo de modificación ('formato_citas', 'redaccion_superficial', 'cambio_contenido')
            
        Returns:
            El texto modificado según el tipo especificado
        """
        
        if tipo_modificacion not in self.prompts:
            tipos_validos = list(self.prompts.keys())
            raise ValueError(f"Tipo de modificación '{tipo_modificacion}' no válido. Opciones: {tipos_validos}")
        
        # Limitar longitud del texto para evitar timeouts
        if len(texto) > 8000:
            texto = texto[:8000] + "..."
            
        prompt = self.prompts[tipo_modificacion].format(texto=texto)
        
        try:
            response = await self.async_azure_client.chat.completions.create(
                model=DEPLOYMENT,
                messages=[
                    {
                        "role": "system", 
                        "content": "Eres un editor de textos legales preciso y cuidadoso. Sigues las instrucciones exactamente como se especifican."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=6000,
                timeout=60  # 60 second timeout
            )
            
            if response.choices and response.choices[0].message and response.choices[0].message.content:
                return response.choices[0].message.content.strip()
            else:
                raise RuntimeError("Respuesta vacía del modelo")
            
        except Exception as e:
            raise RuntimeError(f"Error modificando texto con LLM: {e}")
    
    def modify_text_sync(self, texto: str, tipo_modificacion: str) -> str:
        """
        Versión síncrona del modificador de texto
        """
        if tipo_modificacion not in self.prompts:
            tipos_validos = list(self.prompts.keys())
            raise ValueError(f"Tipo de modificación '{tipo_modificacion}' no válido. Opciones: {tipos_validos}")
        
        # Limitar longitud del texto para evitar timeouts
        if len(texto) > 8000:
            texto = texto[:8000] + "..."
            
        prompt = self.prompts[tipo_modificacion].format(texto=texto)
        
        try:
            response = self.azure_client.chat.completions.create(
                model=DEPLOYMENT,
                messages=[
                    {
                        "role": "system", 
                        "content": "Eres un editor de textos legales preciso y cuidadoso. Sigues las instrucciones exactamente como se especifican."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=6000,
                timeout=60  # 60 second timeout
            )
            
            if response.choices and response.choices[0].message and response.choices[0].message.content:
                return response.choices[0].message.content.strip()
            else:
                raise RuntimeError("Respuesta vacía del modelo")
            
        except Exception as e:
            raise RuntimeError(f"Error modificando texto con LLM: {e}")
    
    async def modify_multiple_texts(self, textos: Dict[str, str], tipo_modificacion: str) -> Dict[str, str]:
        """
        Modifica múltiples textos de forma asíncrona
        
        Args:
            textos: Diccionario {id: texto} de textos a modificar
            tipo_modificacion: Tipo de modificación a aplicar
            
        Returns:
            Diccionario {id: texto_modificado} con los textos modificados
        """
        tasks = []
        for text_id, texto in textos.items():
            task = self.modify_text(texto, tipo_modificacion)
            tasks.append((text_id, task))
        
        results = {}
        for text_id, task in tasks:
            try:
                modified_text = await task
                results[text_id] = modified_text
            except Exception as e:
                results[text_id] = f"ERROR: {e}"
        
        return results
    
    def get_available_modification_types(self) -> list:
        """
        Retorna los tipos de modificación disponibles
        """
        return list(self.prompts.keys())
    
    def validate_modification(self, original: str, modified: str, tipo_modificacion: str) -> Dict[str, Any]:
        """
        Valida que la modificación se haya realizado correctamente
        
        Returns:
            Diccionario con métricas de validación
        """
        validation_result = {
            'original_length': len(original),
            'modified_length': len(modified),
            'length_change_ratio': len(modified) / len(original) if len(original) > 0 else 0,
            'same_text': original == modified,
            'modification_type': tipo_modificacion,
            'success': len(modified) > 0 and modified != original
        }
        
        # Validaciones específicas por tipo
        if tipo_modificacion == "formato_citas":
            # Para formato de citas, el texto debería ser similar pero con diferentes formatos
            validation_result['expected_similar_length'] = 0.8 <= validation_result['length_change_ratio'] <= 1.2
        
        elif tipo_modificacion == "redaccion_superficial":
            # Para redacción superficial, debería haber cambios significativos en redacción
            validation_result['significant_rewrite'] = validation_result['length_change_ratio'] > 0.7
        
        elif tipo_modificacion == "cambio_contenido":
            # Para cambio de contenido, puede haber cambios más dramáticos
            validation_result['content_changed'] = not validation_result['same_text']
        
        return validation_result 