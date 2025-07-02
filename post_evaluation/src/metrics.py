"""
Métricas y Resultados de Evaluación

Este módulo define las estructuras de datos y funciones para calcular y manejar
las métricas de evaluación del sistema RAG legal.
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

@dataclass
class EvaluationResult:
    """Resultado de una evaluación individual"""
    test_name: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    details: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el resultado a diccionario"""
        return asdict(self)
    
    def to_summary(self) -> Dict[str, float]:
        """Retorna solo las métricas principales"""
        return {
            'accuracy': self.accuracy,
            'precision': self.precision,
            'recall': self.recall,
            'f1_score': self.f1_score
        }

class MetricsCalculator:
    """
    Calculadora de métricas para evaluaciones del sistema RAG
    """
    
    @staticmethod
    def calculate_classification_metrics(true_positives: int, false_positives: int, 
                                       false_negatives: int, true_negatives: int = 0) -> Dict[str, float]:
        """
        Calcula métricas de clasificación estándar
        
        Args:
            true_positives: Verdaderos positivos
            false_positives: Falsos positivos  
            false_negatives: Falsos negativos
            true_negatives: Verdaderos negativos (opcional)
            
        Returns:
            Diccionario con las métricas calculadas
        """
        # Evitar división por cero
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        # Accuracy si tenemos true negatives
        if true_negatives > 0:
            total = true_positives + false_positives + false_negatives + true_negatives
            accuracy = (true_positives + true_negatives) / total if total > 0 else 0
        else:
            # Accuracy simplificada: casos correctos / total de casos
            total = true_positives + false_positives + false_negatives
            accuracy = true_positives / total if total > 0 else 0
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'true_positives': true_positives,
            'false_positives': false_positives,
            'false_negatives': false_negatives,
            'true_negatives': true_negatives
        }
    
    @staticmethod
    def calculate_citation_metrics(original_citations: set, modified_citations: set) -> Dict[str, float]:
        """
        Calcula métricas específicas para evaluación de citas
        
        Args:
            original_citations: Conjunto de citas originales
            modified_citations: Conjunto de citas modificadas
            
        Returns:
            Diccionario con métricas de citas
        """
        intersection = original_citations.intersection(modified_citations)
        union = original_citations.union(modified_citations)
        
        # Métricas de similitud de conjuntos
        jaccard_similarity = len(intersection) / len(union) if len(union) > 0 else 0
        dice_coefficient = 2 * len(intersection) / (len(original_citations) + len(modified_citations)) if (len(original_citations) + len(modified_citations)) > 0 else 0
        
        # Métricas de clasificación
        true_positives = len(intersection)
        false_positives = len(modified_citations - original_citations)
        false_negatives = len(original_citations - modified_citations)
        
        classification_metrics = MetricsCalculator.calculate_classification_metrics(
            true_positives, false_positives, false_negatives
        )
        
        return {
            **classification_metrics,
            'jaccard_similarity': jaccard_similarity,
            'dice_coefficient': dice_coefficient,
            'total_original': len(original_citations),
            'total_modified': len(modified_citations),
            'total_intersection': len(intersection),
            'total_union': len(union)
        }
    
    @staticmethod
    def calculate_consistency_metrics(responses: List[Any]) -> Dict[str, float]:
        """
        Calcula métricas de consistencia entre múltiples respuestas
        
        Args:
            responses: Lista de respuestas a comparar
            
        Returns:
            Diccionario con métricas de consistencia
        """
        if len(responses) < 2:
            return {'consistency_score': 1.0, 'variance': 0.0}
        
        # Para respuestas RAG, comparar los expedientes retornados
        all_expedientes = []
        for response in responses:
            if hasattr(response, 'results'):
                expedientes = set(r.expte for r in response.results if r.expte)
                all_expedientes.append(expedientes)
            elif isinstance(response, set):
                all_expedientes.append(response)
            else:
                # Intentar convertir a conjunto
                all_expedientes.append(set(str(response).split()))
        
        # Calcular intersección común entre todas las respuestas
        common_expedientes = set.intersection(*all_expedientes) if all_expedientes else set()
        union_expedientes = set.union(*all_expedientes) if all_expedientes else set()
        
        # Métricas de consistencia
        consistency_score = len(common_expedientes) / len(union_expedientes) if len(union_expedientes) > 0 else 1.0
        
        # Varianza en el número de resultados
        result_counts = [len(exp) for exp in all_expedientes]
        mean_count = sum(result_counts) / len(result_counts) if result_counts else 0
        variance = sum((x - mean_count) ** 2 for x in result_counts) / len(result_counts) if result_counts else 0
        
        return {
            'consistency_score': consistency_score,
            'variance': variance,
            'mean_result_count': mean_count,
            'common_results': len(common_expedientes),
            'total_unique_results': len(union_expedientes)
        }

class ResultsManager:
    """
    Gestor de resultados de evaluación
    """
    
    def __init__(self, output_dir: Path = Path("post_evaluation/evaluation_results")):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def save_results(self, results: Dict[str, EvaluationResult], timestamp: Optional[str] = None) -> Dict[str, Path]:
        """
        Guarda los resultados de evaluación en archivos
        
        Args:
            results: Diccionario con resultados de evaluación
            timestamp: Timestamp personalizado (opcional)
            
        Returns:
            Diccionario con las rutas de archivos generados
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Crear directorio con timestamp para esta ejecución
        run_dir = self.output_dir / timestamp
        run_dir.mkdir(exist_ok=True)
        
        saved_files = {}
        
        # Guardar resumen
        summary_data = {}
        for test_name, result in results.items():
            summary_data[test_name] = result.to_summary()
        
        summary_file = run_dir / "resumen_evaluacion.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        saved_files['resumen'] = summary_file
        
        # Guardar resultados detallados
        for test_name, result in results.items():
            detail_file = run_dir / f"detallado_{test_name}.json"
            with open(detail_file, 'w', encoding='utf-8') as f:
                json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
            saved_files[f'detallado_{test_name}'] = detail_file
        
        # Crear reporte en markdown
        report_file = self.create_markdown_report(results, run_dir)
        saved_files['reporte'] = report_file
        
        return saved_files
    
    def create_markdown_report(self, results: Dict[str, EvaluationResult], run_dir: Path) -> Path:
        """
        Crea un reporte en formato Markdown
        
        Args:
            results: Resultados de evaluación
            run_dir: Directorio de la ejecución
            
        Returns:
            Ruta del archivo de reporte generado
        """
        report_file = run_dir / "reporte_evaluacion.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# Reporte de Evaluación - Sistema RAG Legal\n\n")
            f.write(f"**Generado:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Resumen ejecutivo
            f.write("## Resumen Ejecutivo\n\n")
            f.write("| Prueba | Exactitud | Precisión | Recall | F1 Score |\n")
            f.write("|--------|-----------|-----------|--------|----------|\n")
            
            for test_name, result in results.items():
                f.write(f"| {result.test_name} | {result.accuracy:.3f} | {result.precision:.3f} | {result.recall:.3f} | {result.f1_score:.3f} |\n")
            
            # Resultados detallados
            f.write("\n## Resultados Detallados\n\n")
            
            for test_name, result in results.items():
                f.write(f"### {result.test_name}\n\n")
                f.write(f"**Exactitud:** {result.accuracy:.3f}\n")
                f.write(f"**Precisión:** {result.precision:.3f}\n")
                f.write(f"**Recall:** {result.recall:.3f}\n")
                f.write(f"**F1 Score:** {result.f1_score:.3f}\n\n")
                
                # Información adicional de los detalles
                if 'error' in result.details:
                    f.write(f"**Error:** {result.details['error']}\n\n")
                else:
                    if 'total_files' in result.details:
                        f.write(f"**Archivos Procesados:** {result.details['total_files']}\n")
                    if 'correct_extractions' in result.details:
                        f.write(f"**Extracciones Correctas:** {result.details['correct_extractions']}\n")
                    if 'total_queries' in result.details:
                        f.write(f"**Consultas Probadas:** {result.details['total_queries']}\n")
                    if 'nota' in result.details:
                        f.write(f"**Nota:** {result.details['nota']}\n")
                    f.write("\n")
            
            # Interpretación de resultados
            f.write("## Interpretación de Resultados\n\n")
            f.write("### Criterios de Evaluación\n\n")
            f.write("- **Exactitud ≥ 0.9:** Excelente\n")
            f.write("- **Exactitud ≥ 0.8:** Bueno\n")
            f.write("- **Exactitud ≥ 0.7:** Aceptable\n")
            f.write("- **Exactitud < 0.7:** Necesita mejoras\n\n")
            
            # Recomendaciones basadas en resultados
            f.write("### Recomendaciones\n\n")
            
            overall_performance = sum(r.accuracy for r in results.values()) / len(results) if results else 0
            
            if overall_performance >= 0.9:
                f.write("🟢 **Rendimiento Excelente:** El sistema muestra alta robustez en todas las pruebas.\n\n")
            elif overall_performance >= 0.8:
                f.write("🟡 **Rendimiento Bueno:** El sistema es generalmente robusto con algunas áreas de mejora.\n\n")
            elif overall_performance >= 0.7:
                f.write("🟠 **Rendimiento Aceptable:** Se recomienda revisar los componentes con menor rendimiento.\n\n")
            else:
                f.write("🔴 **Rendimiento Bajo:** Se requieren mejoras significativas en el sistema.\n\n")
        
        return report_file
    
    def load_results(self, timestamp: str) -> Dict[str, EvaluationResult]:
        """
        Carga resultados previamente guardados
        
        Args:
            timestamp: Timestamp de los resultados a cargar
            
        Returns:
            Diccionario con los resultados cargados
        """
        results = {}
        
        # Directorio de la ejecución específica
        run_dir = self.output_dir / timestamp
        if not run_dir.exists():
            return results
        
        # Buscar archivos detallados en el directorio de la ejecución
        pattern = "detallado_*.json"
        for file_path in run_dir.glob(pattern):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            test_name = file_path.stem.replace("detallado_", "")
            
            result = EvaluationResult(
                test_name=data['test_name'],
                accuracy=data['accuracy'],
                precision=data['precision'],
                recall=data['recall'],
                f1_score=data['f1_score'],
                details=data['details']
            )
            
            results[test_name] = result
        
        return results
    
    def compare_evaluations(self, timestamp1: str, timestamp2: str) -> Dict[str, Any]:
        """
        Compara dos evaluaciones diferentes
        
        Args:
            timestamp1: Timestamp de la primera evaluación
            timestamp2: Timestamp de la segunda evaluación
            
        Returns:
            Diccionario con la comparación
        """
        results1 = self.load_results(timestamp1)
        results2 = self.load_results(timestamp2)
        
        comparison = {
            'timestamp1': timestamp1,
            'timestamp2': timestamp2,
            'improvements': {},
            'degradations': {},
            'stable': {}
        }
        
        for test_name in results1.keys():
            if test_name in results2:
                acc1 = results1[test_name].accuracy
                acc2 = results2[test_name].accuracy
                diff = acc2 - acc1
                
                if diff > 0.05:  # Mejora significativa
                    comparison['improvements'][test_name] = diff
                elif diff < -0.05:  # Degradación significativa
                    comparison['degradations'][test_name] = diff
                else:  # Estable
                    comparison['stable'][test_name] = diff
        
        return comparison 