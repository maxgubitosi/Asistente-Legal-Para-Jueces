"""
Modificador de Textos Legales

Este módulo utiliza GPT-4o para modificar textos legales de diferentes maneras, según cada test.
"""

import asyncio
import time
import logging
from typing import Dict, Any, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import AzureOpenAI, AsyncAzureOpenAI
from configs.credentials_config import API_KEY, ENDPOINT, MODEL, DEPLOYMENT

logger = logging.getLogger(__name__)

class TextModifier:
    """
    Modificador de textos legales usando Azure OpenAI GPT-4o.
    Las plantillas de prompt se pasan externamente al constructor para mantener
    la responsabilidad de cada prueba sobre sus propios prompts.
    """
    
    def __init__(self, 
                 prompts: Dict[str, str],
                 max_retries: int = 3, 
                 retry_delay: float = 1.0, 
                 max_workers: int = 10,
                 endpoint: str = ENDPOINT,
                 deployment: str = DEPLOYMENT,
                 model_name: str = MODEL,
                 temperature: float = 0.3):
        self.endpoint = endpoint
        self.deployment = deployment
        self.model_name = model_name
        self.temperature = temperature

        # Prompts must be provided by caller
        if not prompts or not isinstance(prompts, dict):
            raise ValueError("Se debe proporcionar un diccionario de prompts al inicializar TextModifier.")
        self.prompts = prompts

        # Synchronous client
        self.azure_client = AzureOpenAI(
            api_version="2025-04-01-preview",
            azure_endpoint=self.endpoint,
            api_key=API_KEY
        )
        # Async client
        self.async_azure_client = AsyncAzureOpenAI(
            api_version="2025-04-01-preview",
            azure_endpoint=self.endpoint,
            api_key=API_KEY
        )
        
        # Retry configuration
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.max_workers = max_workers

    def _call_azure_with_retries(self, prompt: str, use_async: bool = False, force_json: bool = False) -> str:
        """
        Llama a Azure OpenAI con retry logic y manejo de errores robusto
        
        Args:
            prompt: El prompt a enviar al modelo
            use_async: Si usar el cliente asíncrono (para uso interno)
            force_json: Si forzar respuesta en formato JSON
            
        Returns:
            Respuesta del modelo
            
        Raises:
            RuntimeError: Si todos los reintentos fallan
        """
        last_exception = None
        logger.info(f"📤 Calling Azure with retries: {self.max_retries}, force_json: {force_json}")
        for attempt in range(self.max_retries):
            try:
                if use_async:
                    # Para llamadas asíncronas, usar cliente síncrono aquí
                    # (las llamadas asíncronas reales van por otro método)
                    client = self.azure_client
                else:
                    client = self.azure_client
                
                # Prepare the request parameters
                request_params = {
                    "model": self.deployment,
                    "messages": [
                        {
                            "role": "system", 
                            "content": "Eres un editor de textos legales preciso y cuidadoso. Sigues las instrucciones exactamente como se especifican."
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    "temperature": self.temperature,
                    "max_tokens": 10000,
                    "timeout": 90  # Increased timeout for reliability
                }
                
                # Add JSON response format if requested
                if force_json:
                    request_params["response_format"] = {"type": "json_object"}
                    logger.info(f"📤 Using JSON response format")
                
                response = client.chat.completions.create(**request_params)
                
                if response.choices and response.choices[0].message and response.choices[0].message.content:
                    return response.choices[0].message.content.strip()
                else:
                    raise RuntimeError("Respuesta vacía del modelo")
                    
            except Exception as e:
                last_exception = e
                logger.warning(f"❌ Intento {attempt + 1}/{self.max_retries} falló: {e}")
                
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    sleep_time = self.retry_delay * (2 ** attempt)
                    logger.info(f"⏳ Esperando {sleep_time:.1f} segundos antes del próximo intento...")
                    time.sleep(sleep_time)
                    
        raise RuntimeError(f"Error después de {self.max_retries} intentos. Último error: {last_exception}")

    async def modify_text(self, texto: str, tipo_modificacion: str) -> str:
        """
        Modifica un texto según el tipo de modificación especificado (versión asíncrona)
        
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
        
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                response = await self.async_azure_client.chat.completions.create(
                    model=self.deployment,
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
                    temperature=self.temperature,
                    max_tokens=10000,
                    timeout=90  # Increased timeout
                )
                
                if response.choices and response.choices[0].message and response.choices[0].message.content:
                    return response.choices[0].message.content.strip()
                else:
                    raise RuntimeError("Respuesta vacía del modelo")
                    
            except Exception as e:
                last_exception = e
                logger.warning(f"❌ Intento async {attempt + 1}/{self.max_retries} falló: {e}")
                
                if attempt < self.max_retries - 1:
                    sleep_time = self.retry_delay * (2 ** attempt)
                    await asyncio.sleep(sleep_time)
                    
        raise RuntimeError(f"Error después de {self.max_retries} intentos. Último error: {last_exception}")
    
    def modify_text_sync(self, texto: str, tipo_modificacion: str) -> str:
        """
        Versión síncrona del modificador de texto con retry logic
        """
        logger.info(f"📤 Modifying text with type: {tipo_modificacion}")
        
        if tipo_modificacion not in self.prompts:
            logger.error(f"Tipo de modificación '{tipo_modificacion}' no válido. Opciones: {list(self.prompts.keys())}")
            tipos_validos = list(self.prompts.keys())
            raise ValueError(f"Tipo de modificación '{tipo_modificacion}' no válido. Opciones: {tipos_validos}")
        
        # Limitar longitud del texto para evitar timeouts
        if len(texto) > 8000:
            texto = texto[:8000] + "..."
            
        prompt = self.prompts[tipo_modificacion].format(texto=texto)
        
        # Use JSON mode for question generation
        force_json = tipo_modificacion.startswith('generate_questions')
        if force_json:
            logger.info(f"📤 Using JSON response format for question generation: {tipo_modificacion}")
            
        return self._call_azure_with_retries(prompt, use_async=False, force_json=force_json)
    
    def modify_texts_concurrent(self, textos_data: List[Tuple[str, str, str]], tipo_modificacion: str) -> List[Tuple[str, str, str]]:
        """
        Modifica múltiples textos de forma concurrente usando ThreadPoolExecutor
        
        Args:
            textos_data: Lista de tuplas (id, texto, info_adicional)
            tipo_modificacion: Tipo de modificación a aplicar
            
        Returns:
            Lista de tuplas (id, texto_modificado_o_error, info_adicional)
        """
        if tipo_modificacion not in self.prompts:
            tipos_validos = list(self.prompts.keys())
            raise ValueError(f"Tipo de modificación '{tipo_modificacion}' no válido. Opciones: {tipos_validos}")
        
        def process_single_text(data):
            text_id, texto, info_adicional = data
            try:
                modified_text = self.modify_text_sync(texto, tipo_modificacion)
                return (text_id, modified_text, info_adicional)
            except Exception as e:
                logger.error(f"❌ Error modificando texto {text_id}: {e}")
                return (text_id, f"ERROR: {e}", info_adicional)
        
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_data = {executor.submit(process_single_text, data): data for data in textos_data}
            
            # Collect results as they complete
            for future in as_completed(future_to_data):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    data = future_to_data[future]
                    logger.error(f"❌ Error en future para {data[0]}: {e}")
                    results.append((data[0], f"FUTURE_ERROR: {e}", data[2]))
        
        # Sort results by original order (based on text_id if it's numeric or maintain order)
        try:
            # Try to sort by ID if they're numeric
            results.sort(key=lambda x: int(x[0]) if x[0].isdigit() else x[0])
        except:
            # If sorting fails, keep original order
            pass
            
        return results

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
                logger.error(f"❌ Error modificando texto {text_id}: {e}")
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
            'success': len(modified) > 0 and modified != original and not modified.startswith("ERROR:")
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