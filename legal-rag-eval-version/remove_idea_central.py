import json
import re
from pathlib import Path

def clean_idea_central(json_path):
    """
    Limpia el campo IDEA_CENTRAL eliminando encabezados redundantes
    
    Args:
        json_path (str): Ruta al archivo JSON a procesar
    """
    # Leer el archivo JSON
    with open(json_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # Verificar si existe el campo IDEA_CENTRAL
    if "IDEA_CENTRAL" in data:
        idea_central = data["IDEA_CENTRAL"]
        
        # Patrones a eliminar (con variaciones)
        patterns_to_remove = [
            r"^\*\*IDEA CENTRAL DEL FALLO\*\*\n\n",
            r"^### IDEA CENTRAL DEL FALLO\n\n",
            r"^\*\*IDEA CENTRAL DEL FALLO:\*\*\n\n",
            r"^### IDEA CENTRAL DEL FALLO:\n\n",
            r"^\*\*IDEA CENTRAL:\*\*\n\n",
            r"^### IDEA CENTRAL:\n\n",
            r"^\*\*IDEA CENTRAL DEL FALLO\*\*\n",
            r"^### IDEA CENTRAL DEL FALLO\n",
            # Nuevos patrones corregidos
            r"^\*\*IDEA CENTRAL DEL FALLO JUDICIAL\*\*\n\n",
            r"^\*\*IDEA CENTRAL DEL FALLO JUDICIAL\*\*\n",
            r"^\*\*Decisión Judicial Principal:\*\*\n\n",
            r"^\*\*Decisión Judicial Principal:\*\*\n",
            r"^\*\*Decisión Judicial Principal:\*\*",
            r"^\*\*decisión judicial principal:\*\*\n",
            # Patrones con espacios al inicio
            r"^\s+\*\*IDEA CENTRAL DEL FALLO\*\*\n\n",
            r"^\s+### IDEA CENTRAL DEL FALLO\n\n",
            r"^\s+\*\*IDEA CENTRAL DEL FALLO JUDICIAL\*\*\n\n",
            r"^\s+\*\*Decisión Judicial Principal:\*\*\n\n",
            r"^\s+\*\*Decisión Judicial Principal:\*\*\n",
            r"^\s+\*\*Decisión Judicial Principal:\*\*",
            r"^\s+\*\*decisión judicial principal:\*\*",
        ]
        
        # Aplicar cada patrón
        cleaned_text = idea_central
        for pattern in patterns_to_remove:
            cleaned_text = re.sub(pattern, "", cleaned_text, flags=re.MULTILINE)
        
        # Actualizar el JSON solo si hubo cambios
        if cleaned_text != idea_central:
            data["IDEA_CENTRAL"] = cleaned_text
            print(f"✓ Limpiado encabezado en: {json_path}")
            
            # Guardar el archivo modificado
            with open(json_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
            return True
        else:
            print(f"- Sin cambios en: {json_path}")
            return False
    else:
        print(f"⚠ No se encontró campo IDEA_CENTRAL en: {json_path}")
        return False

def main():
    # Directorio base
    base_dir = Path("datasets/unified_json")
    
    # Verificar que el directorio existe
    if not base_dir.exists():
        print(f"❌ El directorio no existe: {base_dir}")
        return
    
    # Buscar todos los archivos JSON recursivamente
    json_files = list(base_dir.rglob("*.json"))
    
    if not json_files:
        print(f"❌ No se encontraron archivos JSON en: {base_dir}")
        return
    
    print(f"📁 Encontrados {len(json_files)} archivos JSON")
    print("🚀 Iniciando procesamiento...\n")
    
    # Contadores y listas
    processed = 0
    modified = 0
    errors = 0
    not_modified = []
    
    # Procesar cada archivo
    for json_file in json_files:
        try:
            if clean_idea_central(json_file):
                modified += 1
            else:
                not_modified.append(json_file)
            processed += 1
        except Exception as e:
            print(f"❌ Error procesando {json_file}: {e}")
            errors += 1
    
    # Resumen final
    print(f"\n📊 RESUMEN:")
    print(f"   Archivos procesados: {processed}")
    print(f"   Archivos modificados: {modified}")
    print(f"   Archivos sin modificar: {len(not_modified)}")
    print(f"   Errores: {errors}")
    
    if not_modified:
        print(f"\n📋 ARCHIVOS SIN MODIFICAR:")
        for file in not_modified:
            print(f"   - {file}")
    
    print(f"\n🎉 Proceso completado!")

if __name__ == "__main__":
    main()