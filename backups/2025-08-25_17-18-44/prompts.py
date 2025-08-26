#!/usr/bin/env python3
"""
Prompts para el sistema de auto-triage de EventArb Bot
Contiene todos los prompts estructurados para diferentes tipos de análisis
"""

# Prompt base para análisis de errores
ERROR_ANALYSIS_PROMPT = """
Eres un experto en Python, debugging y sistemas de trading automatizados.

ANÁLISIS DEL ERROR:
{error_log}

CONTEXTO DEL CÓDIGO:
{code_context}

INSTRUCCIONES:
1. Analiza la causa raíz del error
2. Identifica el tipo de error (sintaxis, runtime, lógica, etc.)
3. Propón una solución específica y mínima
4. Lista los archivos que necesitan ser modificados
5. Explica por qué ocurrió el error

FORMATO DE RESPUESTA:
- Análisis: [explicación del error]
- Tipo: [tipo de error]
- Solución: [código del fix]
- Archivos: [lista de archivos a modificar]
- Explicación: [por qué ocurrió]
"""

# Prompt para generación de fixes
FIX_GENERATION_PROMPT = """
Basándote en este análisis de error, genera un fix específico:

ANÁLISIS:
{analysis}

REQUISITOS:
1. El fix debe ser mínimo y específico
2. Solo modifica lo necesario para resolver el error
3. Mantén la funcionalidad existente
4. Incluye comentarios explicativos
5. Sigue las mejores prácticas de Python

Genera solo el código del fix, sin explicaciones adicionales.
"""

# Prompt para validación de seguridad
SECURITY_VALIDATION_PROMPT = """
Valida que este fix no comprometa la seguridad:

FIX PROPUESTO:
{proposed_fix}

ARCHIVOS A MODIFICAR:
{files_to_modify}

CRITERIOS DE SEGURIDAD:
1. No toca archivos de configuración (.env, secrets)
2. No modifica credenciales o API keys
3. No cambia parámetros de riesgo críticos
4. No altera la lógica de seguridad del bot
5. Solo modifica archivos de código fuente

RESPONDE:
- ¿Es seguro? (SÍ/NO)
- ¿Por qué?
- ¿Qué archivos están prohibidos?
"""

# Prompt para análisis de impacto
IMPACT_ANALYSIS_PROMPT = """
Analiza el impacto de este fix:

FIX:
{fix_code}

ARCHIVOS MODIFICADOS:
{modified_files}

ANÁLISIS REQUERIDO:
1. ¿Qué funcionalidad se ve afectada?
2. ¿Hay riesgo de regresión?
3. ¿Se mantiene la compatibilidad?
4. ¿Cuánto tiempo tomará el deploy?
5. ¿Se necesitan tests adicionales?

RESPONDE:
- Impacto: [BAJO/MEDIO/ALTO]
- Riesgos: [lista de riesgos]
- Tests necesarios: [qué probar]
- Tiempo estimado: [minutos/horas]
"""

# Prompt para generación de PR
PR_GENERATION_PROMPT = """
Genera un Pull Request para este fix:

FIX:
{fix_code}

ANÁLISIS:
{analysis}

INSTRUCCIONES:
1. Título descriptivo y conciso
2. Descripción detallada del problema
3. Explicación de la solución
4. Lista de cambios realizados
5. Instrucciones de testing
6. Etiquetas apropiadas

FORMATO:
## Título
[Descripción del problema]

## Solución
[Explicación de la solución]

## Cambios
- [lista de cambios]

## Testing
[Instrucciones para probar]

## Etiquetas
[labels apropiados]
"""

# Prompt para validación de CI/CD
CI_VALIDATION_PROMPT = """
Valida que este PR pase los checks de CI/CD:

CAMBIO PROPUESTO:
{changes}

ARCHIVOS MODIFICADOS:
{files}

REQUISITOS DE CI/CD:
1. ¿El código compila sin errores?
2. ¿Pasa los tests de linting?
3. ¿No hay conflictos de merge?
4. ¿Los tests unitarios pasan?
5. ¿El build es exitoso?

RESPONDE:
- Estado CI: [PASA/FALLA]
- Problemas identificados: [lista]
- Recomendaciones: [qué ajustar]
"""

# Prompt para rollback
ROLLBACK_PROMPT = """
Genera un plan de rollback para este cambio:

CAMBIO IMPLEMENTADO:
{implemented_change}

ARCHIVOS MODIFICADOS:
{modified_files}

PLAN DE ROLLBACK:
1. Comando para revertir cambios
2. Archivos a restaurar
3. Verificación post-rollback
4. Tiempo estimado de rollback
5. Impacto en el sistema

RESPONDE:
- Comando rollback: [git command]
- Tiempo estimado: [minutos]
- Verificación: [qué verificar]
- Impacto: [BAJO/MEDIO/ALTO]
"""

# Prompt para monitoreo post-deploy
POST_DEPLOY_PROMPT = """
Define métricas de monitoreo post-deploy:

CAMBIO DESPLEGADO:
{deployed_change}

MÉTRICAS REQUERIDAS:
1. ¿El bot se inicia correctamente?
2. ¿Los logs muestran errores?
3. ¿La funcionalidad principal funciona?
4. ¿El rendimiento se mantiene?
5. ¿Las alertas funcionan?

RESPONDE:
- Métricas clave: [qué medir]
- Umbrales: [valores aceptables]
- Alertas: [cuándo alertar]
- Tiempo de observación: [cuánto monitorear]
"""

# Prompt para documentación
DOCUMENTATION_PROMPT = """
Genera documentación para este fix:

FIX IMPLEMENTADO:
{fix_implementation}

DOCUMENTACIÓN REQUERIDA:
1. Descripción del problema
2. Solución implementada
3. Archivos modificados
4. Instrucciones de testing
5. Notas de mantenimiento

FORMATO:
## Problema
[Descripción]

## Solución
[Implementación]

## Archivos
[Lista de archivos]

## Testing
[Instrucciones]

## Mantenimiento
[Notas importantes]
"""
