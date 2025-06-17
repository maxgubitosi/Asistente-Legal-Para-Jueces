#!/usr/bin/env python3
"""
Detecta cambios en el dataset y actualiza los índices si es necesario.
"""

import os
import json
import hashlib
import time
from pathlib import Path
from datetime import datetime

DATASET_DIR = "/datasets/fallos_json"
INDEX_DIR = "/indexes"
METADATA_FILE = f"{INDEX_DIR}/dataset_metadata.json"

def calculate_dataset_hash(dataset_dir):
    """Calcula un hash del dataset completo para detectar cambios"""
    hasher = hashlib.md5()
    
    json_files = sorted(Path(dataset_dir).rglob("*.json"))
    total_size = 0
    file_count = 0
    
    for file_path in json_files:
        # Incluir path relativo y modificación en el hash
        hasher.update(str(file_path.relative_to(dataset_dir)).encode())
        hasher.update(str(file_path.stat().st_mtime).encode())
        hasher.update(str(file_path.stat().st_size).encode())
        
        total_size += file_path.stat().st_size
        file_count += 1
    
    return {
        "hash": hasher.hexdigest(),
        "file_count": file_count,
        "total_size": total_size,
        "last_check": datetime.now().isoformat()
    }

def load_metadata():
    """Carga metadatos previos del dataset"""
    if os.path.exists(METADATA_FILE):
        try:
            with open(METADATA_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Error leyendo metadata: {e}")
    return None

def save_metadata(metadata):
    """Guarda metadatos del dataset"""
    os.makedirs(INDEX_DIR, exist_ok=True)
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)

def check_dataset_changes():
    """Verifica si el dataset ha cambiado"""
    print("🔍 Verificando cambios en el dataset...")
    
    if not os.path.exists(DATASET_DIR):
        print(f"❌ Dataset no encontrado: {DATASET_DIR}")
        return False, "Dataset no encontrado"
    
    # Calcular estado actual
    current_metadata = calculate_dataset_hash(DATASET_DIR)
    print(f"📊 Dataset actual: {current_metadata['file_count']} archivos, {current_metadata['total_size']} bytes")
    
    # Comparar con estado previo
    previous_metadata = load_metadata()
    
    if previous_metadata is None:
        print("🆕 Primera vez - necesario indexar")
        save_metadata(current_metadata)
        return True, "Primera indexación"
    
    if current_metadata["hash"] != previous_metadata["hash"]:
        changes = []
        if current_metadata["file_count"] != previous_metadata["file_count"]:
            diff = current_metadata["file_count"] - previous_metadata["file_count"]
            changes.append(f"{diff:+d} archivos")
        
        if current_metadata["total_size"] != previous_metadata["total_size"]:
            diff = current_metadata["total_size"] - previous_metadata["total_size"]
            changes.append(f"{diff:+d} bytes")
        
        change_desc = ", ".join(changes) if changes else "modificaciones detectadas"
        print(f"🔄 Dataset cambió: {change_desc}")
        save_metadata(current_metadata)
        return True, f"Cambios: {change_desc}"
    
    print("✅ Dataset sin cambios")
    return False, "Sin cambios"

def list_new_files():
    """Lista archivos nuevos desde la última indexación"""
    previous_metadata = load_metadata()
    if not previous_metadata:
        return []
    
    last_check = datetime.fromisoformat(previous_metadata["last_check"])
    new_files = []
    
    for file_path in Path(DATASET_DIR).rglob("*.json"):
        file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
        if file_time > last_check:
            new_files.append(str(file_path))
    
    return new_files

def main():
    """Función principal"""
    print("📋 DETECTOR DE CAMBIOS - Legal RAG")
    print("=" * 40)
    
    # Verificar cambios
    needs_update, reason = check_dataset_changes()
    
    if needs_update:
        print(f"🚨 ACCIÓN REQUERIDA: {reason}")
        print("\nPara actualizar los índices ejecute:")
        print("  python -m scripts.build_index /datasets/fallos_json --qdrant-url http://qdrant:6333")
        
        # Mostrar archivos nuevos si es posible
        new_files = list_new_files()
        if new_files:
            print(f"\n📁 Archivos nuevos detectados ({len(new_files)}):")
            for file in new_files[:10]:  # Mostrar máximo 10
                print(f"   {file}")
            if len(new_files) > 10:
                print(f"   ... y {len(new_files) - 10} más")
        
        return 1  # Exit code para indicar que se necesita actualización
    else:
        print(f"✅ Estado: {reason}")
        return 0

if __name__ == "__main__":
    exit(main())
