"""
Evaluador Principal del Sistema RAG Legal

Este módulo orquesta todas las pruebas de evaluación.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any
from tqdm import tqdm

from .citation_extractor import CitationExtractor
from .text_modifier import TextModifier
from .rag_client import RAGClient
from .metrics import EvaluationResult, MetricsCalculator, ResultsManager

logger = logging.getLogger(__name__)

# Default prompts for evaluation operations (combined)
DEFAULT_PROMPTS = {
    "formato_citas": "Modifica el formato de citas manteniendo el mismo contenido: {texto}",
    "redaccion_superficial": "Reescribe el texto con redacción superficial manteniendo significado: {texto}",
    "cambio_contenido": "Cambia completamente el contenido manteniendo citas iguales: {texto}"
}

class LegalRAGEvaluator:
    """
    Evaluador principal para el sistema RAG legal
    """
    
    def __init__(self, 
                 base_data_path: str = "datasets/fallos_txts",
                 backend_url: str = "http://localhost:8000",
                 output_dir: str = "evaluation_results"):
        
        self.base_data_path = Path(base_data_path)
        self.backend_url = backend_url
        
        # Inicializar componentes
        self.citation_extractor = CitationExtractor()
        self.text_modifier = TextModifier(prompts=DEFAULT_PROMPTS)
        self.rag_client = RAGClient(backend_url)
        self.results_manager = ResultsManager(Path(output_dir))
        
        # Configurar logging
        logging.basicConfig(level=logging.INFO)
        
        # Consultas de prueba para las evaluaciones
        self.test_queries = [
            "¿Qué dice sobre regulación de honorarios profesionales?",
            "¿Cuáles son los procedimientos para recursos extraordinarios?",
            "¿Cómo se calculan y establecen los honorarios de abogados?",
            "¿Qué establece la normativa sobre notificaciones legales?",
            "¿Cuáles son los plazos para el pago de honorarios regulados?",
            "¿Qué dice sobre recursos de inaplicabilidad de ley?",
            "¿Cuáles son las bases económicas para la regulación arancelaria?",
            "¿Qué establece sobre actuación profesional en recursos?",
            "¿Cómo se determina la base económica para honorarios?",
            "¿Qué dice sobre mora en el pago de honorarios?"
        ]
    
    def test_citation_format_robustness(self, sample_size: int = 20) -> EvaluationResult:
        """
        Prueba 1: Robustez de Formato de Citas
        
        Evalúa si el sistema de extracción de citas es robusto ante cambios
        en el formato de las citas (art. vs artículo, etc.)
        """
        logger.info("🔍 Iniciando Prueba de Robustez de Formato de Citas")
        
        # Obtener archivos de muestra
        txt_files = list(self.base_data_path.rglob("*.txt"))
        if len(txt_files) == 0:
            logger.error(f"No se encontraron archivos .txt en {self.base_data_path}")
            return EvaluationResult(
                test_name="Robustez de Formato de Citas",
                accuracy=0.0, precision=0.0, recall=0.0, f1_score=0.0,
                details={"error": f"No se encontraron archivos en {self.base_data_path}"}
            )
        
        sample_files = txt_files[:sample_size] if len(txt_files) > sample_size else txt_files
        
        total_files = len(sample_files)
        correct_extractions = 0
        all_metrics = []
        detailed_results = []
        
        for txt_file in tqdm(sample_files, desc="Probando robustez de citas"):
            try:
                # Extraer citas del texto original
                original_text = txt_file.read_text(encoding='utf-8')
                original_citations = self.citation_extractor.extract_citations(original_text)
                
                # Modificar formato de citas
                modified_text = self.text_modifier.modify_text_sync(original_text, "formato_citas")
                modified_citations = self.citation_extractor.extract_citations(modified_text)
                
                # Calcular métricas usando el extractor
                comparison = self.citation_extractor.compare_extractions(original_citations, modified_citations)
                all_metrics.append(comparison)
                
                # Considerar correcto si las citas son exactamente iguales
                is_correct = comparison['accuracy'] == 1.0
                if is_correct:
                    correct_extractions += 1
                
                detailed_results.append({
                    'archivo': str(txt_file.relative_to(self.base_data_path)),
                    'correcto': is_correct,
                    'metricas': comparison
                })
                
            except Exception as e:
                logger.error(f"Error procesando {txt_file}: {e}")
                detailed_results.append({
                    'archivo': str(txt_file.relative_to(self.base_data_path)),
                    'error': str(e)
                })
        
        # Calcular métricas agregadas
        if all_metrics:
            avg_precision = sum(m['precision'] for m in all_metrics) / len(all_metrics)
            avg_recall = sum(m['recall'] for m in all_metrics) / len(all_metrics)
            avg_f1 = sum(m['f1_score'] for m in all_metrics) / len(all_metrics)
        else:
            avg_precision = avg_recall = avg_f1 = 0.0
        
        accuracy = correct_extractions / total_files if total_files > 0 else 0.0
        
        return EvaluationResult(
            test_name="Robustez de Formato de Citas",
            accuracy=accuracy,
            precision=avg_precision,
            recall=avg_recall,
            f1_score=avg_f1,
            details={
                'total_archivos': total_files,
                'extracciones_correctas': correct_extractions,
                'resultados_detallados': detailed_results,
                'metricas_individuales': all_metrics,
                'descripcion': 'Evalúa si el extractor de citas es robusto ante cambios de formato'
            }
        )
    
    def test_superficial_wording_robustness(self, sample_size: int = 10) -> EvaluationResult:
        """
        Prueba 2: Robustez de Redacción Superficial
        
        Evalúa si el sistema RAG retorna resultados similares cuando el texto
        es reescrito superficialmente pero mantiene el mismo significado.
        """
        logger.info("📝 Iniciando Prueba de Robustez de Redacción Superficial")
        
        # Verificar que el backend esté disponible
        if not self.rag_client.check_health():
            logger.error("Backend RAG no disponible. Asegúrate de ejecutar 'docker compose up --build'")
            return EvaluationResult(
                test_name="Robustez de Redacción Superficial",
                accuracy=0.0, precision=0.0, recall=0.0, f1_score=0.0,
                details={"error": "Backend RAG no disponible"}
            )
        
        # Para esta prueba, evaluamos la consistencia de las consultas
        # En una implementación completa, se reconstruirían los índices con datos modificados
        
        consistent_queries = 0
        total_queries = len(self.test_queries)
        detailed_results = []
        
        for query in tqdm(self.test_queries, desc="Probando consistencia de consultas"):
            try:
                # Realizar múltiples consultas para evaluar consistencia
                responses = []
                for _ in range(3):  # 3 consultas idénticas para evaluar consistencia
                    response = self.rag_client.query(query, top_n=5)
                    responses.append(response)
                
                # Calcular métricas de consistencia
                consistency_metrics = MetricsCalculator.calculate_consistency_metrics(responses)
                
                # Considerar consistente si el score es alto
                is_consistent = consistency_metrics['consistency_score'] > 0.8
                
                if is_consistent:
                    consistent_queries += 1
                
                expedientes_por_respuesta = [
                    self.rag_client.get_expediente_ids(resp) for resp in responses
                ]
                
                detailed_results.append({
                    'consulta': query,
                    'consistente': is_consistent,
                    'expedientes_por_respuesta': expedientes_por_respuesta,
                    'metricas_consistencia': consistency_metrics
                })
                
            except Exception as e:
                logger.error(f"Error evaluando consulta '{query}': {e}")
                detailed_results.append({
                    'consulta': query,
                    'error': str(e)
                })
        
        accuracy = consistent_queries / total_queries if total_queries > 0 else 0.0
        
        return EvaluationResult(
            test_name="Robustez de Redacción Superficial",
            accuracy=accuracy,
            precision=accuracy,  # Simplificado para esta implementación
            recall=accuracy,
            f1_score=accuracy,
            details={
                'total_consultas': total_queries,
                'consultas_consistentes': consistent_queries,
                'resultados_detallados': detailed_results,
                'nota': 'Prueba de consistencia simplificada. La implementación completa requeriría reconstruir índices con datos modificados.',
                'descripcion': 'Evalúa la consistencia del sistema ante redacción superficial'
            }
        )
    
    def test_content_change_sensitivity(self, sample_size: int = 5) -> EvaluationResult:
        """
        Prueba 3: DEPRECADO
        """
        logger.info("🔄 Iniciando Prueba de Sensibilidad a Cambios de Contenido")
        
        # Verificar que el backend esté disponible
        if not self.rag_client.check_health():
            logger.error("Backend RAG no disponible")
            return EvaluationResult(
                test_name="Sensibilidad a Cambios de Contenido",
                accuracy=0.0, precision=0.0, recall=0.0, f1_score=0.0,
                details={"error": "Backend RAG no disponible"}
            )
        
        # Obtener archivos de muestra
        txt_files = list(self.base_data_path.rglob("*.txt"))[:sample_size]
        
        content_changes_detected = 0
        total_files = len(txt_files)
        detailed_results = []
        
        for txt_file in tqdm(txt_files, desc="Probando sensibilidad al contenido"):
            try:
                original_text = txt_file.read_text(encoding='utf-8')
                
                # Crear consulta basada en el contenido original
                query = f"¿Qué dice sobre el expediente {txt_file.stem}?"
                
                # Consultar con contenido original
                original_response = self.rag_client.query(query, top_n=5)
                original_expedientes = set(self.rag_client.get_expediente_ids(original_response))
                
                # Modificar contenido fundamental manteniendo citas
                modified_text = self.text_modifier.modify_text_sync(original_text, "cambio_contenido")
                
                # Verificar que las citas se preservaron
                original_citations = self.citation_extractor.extract_citations(original_text)
                modified_citations = self.citation_extractor.extract_citations(modified_text)
                
                citation_preservation_ratio = len(original_citations.intersection(modified_citations)) / max(len(original_citations), 1)
                
                # Para una implementación completa, se reconstruiría el índice con el contenido modificado
                # Por ahora, simulamos que el contenido cambió si las citas se preservaron pero el texto es diferente
                content_changed = (
                    len(modified_text) != len(original_text) and 
                    citation_preservation_ratio > 0.7 and
                    modified_text != original_text
                )
                
                if content_changed:
                    content_changes_detected += 1
                
                detailed_results.append({
                    'archivo': str(txt_file.relative_to(self.base_data_path)),
                    'consulta': query,
                    'expedientes_originales': list(original_expedientes),
                    'citas_preservadas': citation_preservation_ratio > 0.7,
                    'contenido_cambio': content_changed,
                    'longitud_original': len(original_text),
                    'longitud_modificada': len(modified_text),
                    'ratio_preservacion_citas': citation_preservation_ratio
                })
                
            except Exception as e:
                logger.error(f"Error probando sensibilidad para {txt_file}: {e}")
                detailed_results.append({
                    'archivo': str(txt_file.relative_to(self.base_data_path)),
                    'error': str(e)
                })
        
        accuracy = content_changes_detected / total_files if total_files > 0 else 0.0
        
        return EvaluationResult(
            test_name="Sensibilidad a Cambios de Contenido",
            accuracy=accuracy,
            precision=accuracy,
            recall=accuracy,
            f1_score=accuracy,
            details={
                'total_archivos': total_files,
                'cambios_detectados': content_changes_detected,
                'resultados_detallados': detailed_results,
                'nota': 'Prueba simulada. La implementación completa requeriría reconstruir índices con contenido modificado.',
                'descripcion': 'Evalúa si el sistema puede distinguir cambios fundamentales de contenido'
            }
        )
    
    def run_full_evaluation(self, sample_size: int = 20) -> Dict[str, EvaluationResult]:
        """
        Ejecuta todas las pruebas de evaluación
        
        Args:
            sample_size: Tamaño de muestra para las pruebas
            
        Returns:
            Diccionario con resultados de todas las pruebas
        """
        logger.info("🚀 Iniciando Evaluación Completa del Sistema RAG Legal")
        
        results = {}
        
        try:
            # Prueba 1: Robustez de Formato de Citas
            logger.info("=" * 60)
            results['robustez_citas'] = self.test_citation_format_robustness(sample_size)
            
            # Prueba 2: Robustez de Redacción Superficial
            logger.info("=" * 60)
            results['robustez_redaccion'] = self.test_superficial_wording_robustness(sample_size)
            
            # Prueba 3: Sensibilidad a Cambios de Contenido
            logger.info("=" * 60)
            results['sensibilidad_contenido'] = self.test_content_change_sensitivity(sample_size)
            
            # Guardar resultados
            logger.info("=" * 60)
            logger.info("💾 Guardando resultados de evaluación")
            saved_files = self.results_manager.save_results(results)
            
            logger.info("✅ Evaluación completada exitosamente")
            logger.info(f"📁 Resultados guardados en: {list(saved_files.values())}")
            
        except Exception as e:
            logger.error(f"❌ Error durante la evaluación: {e}")
            raise
        
        return results
    
    def run_single_test(self, test_name: str, sample_size: int = 20) -> EvaluationResult:
        """
        Ejecuta una sola prueba de evaluación
        
        Args:
            test_name: Nombre de la prueba ('citas', 'redaccion', 'contenido')
            sample_size: Tamaño de muestra
            
        Returns:
            Resultado de la prueba específica
        """
        test_mapping = {
            'citas': self.test_citation_format_robustness,
            'redaccion': self.test_superficial_wording_robustness,
            'contenido': self.test_content_change_sensitivity
        }
        
        if test_name not in test_mapping:
            raise ValueError(f"Prueba '{test_name}' no válida. Opciones: {list(test_mapping.keys())}")
        
        logger.info(f"🎯 Ejecutando prueba individual: {test_name}")
        
        
        result = test_mapping[test_name](sample_size)
        
        # Guardar resultado individual
        results = {test_name: result}
        saved_files = self.results_manager.save_results(results)
        
        logger.info(f"✅ Prueba {test_name} completada")
        logger.info(f"📁 Resultado guardado en: {list(saved_files.values())}")
        
        return result
    
    def check_system_status(self) -> Dict[str, Any]:
        """
        Verifica el estado de todos los componentes del sistema
        """
        status = {
            'datos_disponibles': False,
            'backend_rag_disponible': False,
            'modificador_texto_configurado': False,
            'extractor_citas_funcional': False,
            'directorio_salida_listo': False
        }
        
        try:
            # Verificar datos
            txt_files = list(self.base_data_path.rglob("*.txt"))
            status['datos_disponibles'] = len(txt_files) > 0
            status['total_archivos_txt'] = len(txt_files)
            
            # Verificar backend RAG
            status['backend_rag_disponible'] = self.rag_client.check_health()
            
            # Verificar extractor de citas
            try:
                test_citations = self.citation_extractor.extract_citations("arts. 1, 2, 3 de la ley 7046")
                status['extractor_citas_funcional'] = len(test_citations) > 0
            except:
                status['extractor_citas_funcional'] = False
            
            # Verificar directorio de salida
            status['directorio_salida_listo'] = self.results_manager.output_dir.exists()
            
        except Exception as e:
            status['error_verificacion'] = str(e)
        
        return status 