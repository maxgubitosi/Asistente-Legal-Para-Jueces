#!/usr/bin/env python3
"""
Script de benchmarking para medir el rendimiento de búsquedas.
"""

import time
import requests
import statistics
import json
from concurrent.futures import ThreadPoolExecutor

# Consultas de prueba típicas
TEST_QUERIES = [
    "contratos de arrendamiento",
    "responsabilidad civil médica",
    "prescripción de acciones",
    "daños y perjuicios",
    "nulidad de contratos",
    "derecho de familia",
    "divorcio vincular",
    "régimen de visitas",
    "sucesión intestada",
    "usucapión de inmuebles"
]

def benchmark_single_query(api_url, query, debug=False):
    """Benchea una sola consulta"""
    endpoint = "/query-debug" if debug else "/query"
    
    start_time = time.time()
    try:
        response = requests.post(
            f"{api_url}{endpoint}",
            json={"question": query, "top_n": 5},
            timeout=30
        )
        total_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            return {
                "query": query,
                "success": True,
                "total_time": total_time,
                "results_count": len(data.get("results", [])),
                "server_time": data.get("performance", {}).get("total_time_seconds", 0) if debug else None
            }
        else:
            return {
                "query": query,
                "success": False,
                "error": f"HTTP {response.status_code}",
                "total_time": total_time
            }
    except Exception as e:
        return {
            "query": query,
            "success": False,
            "error": str(e),
            "total_time": time.time() - start_time
        }

def run_benchmark(api_url="http://localhost:8000", parallel=False, debug=False):
    """Ejecuta benchmark completo"""
    print(f"🚀 Iniciando benchmark contra: {api_url}")
    print(f"   Modo: {'Paralelo' if parallel else 'Secuencial'}")
    print(f"   Debug: {'Activado' if debug else 'Desactivado'}")
    print(f"   Consultas: {len(TEST_QUERIES)}")
    print("-" * 50)
    
    results = []
    
    if parallel:
        # Ejecución paralela para simular carga
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(benchmark_single_query, api_url, query, debug)
                for query in TEST_QUERIES
            ]
            results = [f.result() for f in futures]
    else:
        # Ejecución secuencial
        for i, query in enumerate(TEST_QUERIES, 1):
            print(f"[{i}/{len(TEST_QUERIES)}] Testing: {query[:30]}...")
            result = benchmark_single_query(api_url, query, debug)
            results.append(result)
            
            if result["success"]:
                print(f"   ✅ {result['total_time']:.3f}s - {result['results_count']} resultados")
            else:
                print(f"   ❌ Error: {result['error']}")
    
    # Análisis de resultados
    print("\n" + "="*50)
    print("📊 RESULTADOS DEL BENCHMARK")
    print("="*50)
    
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    if successful:
        times = [r["total_time"] for r in successful]
        result_counts = [r["results_count"] for r in successful]
        
        print(f"✅ Consultas exitosas: {len(successful)}/{len(results)}")
        print(f"⏱️  Tiempo promedio: {statistics.mean(times):.3f}s")
        print(f"⏱️  Tiempo mediano: {statistics.median(times):.3f}s")
        print(f"⏱️  Tiempo mínimo: {min(times):.3f}s")
        print(f"⏱️  Tiempo máximo: {max(times):.3f}s")
        print(f"📄 Resultados promedio: {statistics.mean(result_counts):.1f}")
        
        if debug and any(r.get("server_time") for r in successful):
            server_times = [r["server_time"] for r in successful if r.get("server_time")]
            print(f"🖥️  Tiempo servidor promedio: {statistics.mean(server_times):.3f}s")
        
        # Clasificación de rendimiento
        avg_time = statistics.mean(times)
        if avg_time < 1.0:
            print("🚀 Rendimiento: EXCELENTE")
        elif avg_time < 3.0:
            print("✅ Rendimiento: BUENO")
        elif avg_time < 5.0:
            print("⚠️  Rendimiento: REGULAR")
        else:
            print("❌ Rendimiento: LENTO")
    
    if failed:
        print(f"\n❌ Consultas fallidas: {len(failed)}")
        for r in failed:
            print(f"   {r['query'][:30]}: {r['error']}")
    
    print("\n💡 RECOMENDACIONES:")
    if successful:
        avg_time = statistics.mean(times)
        if avg_time > 3.0:
            print("   - Considere deshabilitar reranking (ENABLE_RERANKING=false)")
            print("   - Reduzca DENSE_SEARCH_LIMIT y LEXICAL_SEARCH_LIMIT")
            print("   - Active caché de consultas (ENABLE_QUERY_CACHING=true)")
        if any(r["results_count"] > 8 for r in successful):
            print("   - Considere reducir MAX_RESULTS_PER_QUERY")
    
    return results

def check_api_health(api_url="http://localhost:8000"):
    """Verifica que la API esté disponible"""
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API disponible: {data.get('status', 'unknown')}")
            return True
        else:
            print(f"❌ API no disponible: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ No se puede conectar a la API: {e}")
        return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Benchmark del sistema Legal RAG")
    parser.add_argument("--url", default="http://localhost:8000", 
                       help="URL base de la API")
    parser.add_argument("--parallel", action="store_true",
                       help="Ejecutar consultas en paralelo")
    parser.add_argument("--debug", action="store_true",
                       help="Usar endpoint de debug para más información")
    parser.add_argument("--quick", action="store_true",
                       help="Benchmark rápido con menos consultas")
    
    args = parser.parse_args()
    
    # Verificar disponibilidad
    if not check_api_health(args.url):
        return 1
    
    # Ejecutar benchmark
    global TEST_QUERIES
    if args.quick:
        TEST_QUERIES = TEST_QUERIES[:3]
    
    results = run_benchmark(args.url, args.parallel, args.debug)
    
    # Guardar resultados
    timestamp = int(time.time())
    filename = f"benchmark_results_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Resultados guardados en: {filename}")
    
    return 0

if __name__ == "__main__":
    exit(main())
