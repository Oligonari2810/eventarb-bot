#!/usr/bin/env python3
"""
DeepSeek Client para EventArb Bot
Cliente para interactuar con la API de DeepSeek para análisis y fixes automáticos
"""

import os
import json
import time
import requests
from typing import Dict, Any, Optional
from pathlib import Path


class DeepSeekClient:
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.base_url = "https://api.deepseek.com/v1/chat/completions"
        self.timeout = 30

        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY no configurada")

    def analyze_error(self, error_log: str, context: str = "") -> Dict[str, Any]:
        """
        Analiza un error usando DeepSeek y propone una solución

        Args:
            error_log: Log del error a analizar
            context: Contexto adicional del código

        Returns:
            Dict con análisis y solución propuesta
        """
        prompt = f"""
        Analiza este error de Python y propón una solución:

        ERROR:
        {error_log}

        CONTEXTO:
        {context}

        Por favor proporciona:
        1. Análisis del error
        2. Solución específica con código
        3. Archivos que necesitan ser modificados
        4. Explicación de por qué ocurrió el error
        """

        try:
            response = self._make_request(prompt)
            return self._parse_response(response)
        except Exception as e:
            return {
                "error": f"Error en análisis: {str(e)}",
                "solution": None,
                "files_to_modify": [],
                "explanation": "No se pudo analizar el error",
            }

    def generate_fix(self, error_analysis: Dict[str, Any]) -> Optional[str]:
        """
        Genera un fix específico basado en el análisis

        Args:
            error_analysis: Resultado del análisis de error

        Returns:
            Código del fix o None si no se puede generar
        """
        if not error_analysis.get("solution"):
            return None

        prompt = f"""
        Basándote en este análisis de error, genera un fix específico:

        ANÁLISIS:
        {json.dumps(error_analysis, indent=2)}

        Genera solo el código del fix, sin explicaciones adicionales.
        El fix debe ser mínimo y específico para resolver el error.
        """

        try:
            response = self._make_request(prompt)
            return (
                response.get("choices", [{}])[0].get("message", {}).get("content", "")
            )
        except Exception as e:
            return None

    def _make_request(self, prompt: str) -> Dict[str, Any]:
        """Realiza request a la API de DeepSeek"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": "Eres un experto en Python y debugging. Proporciona soluciones claras y específicas.",
                },
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 2000,
            "temperature": 0.1,
        }

        response = requests.post(
            self.base_url, headers=headers, json=data, timeout=self.timeout
        )

        if response.status_code != 200:
            raise Exception(f"API Error: {response.status_code} - {response.text}")

        return response.json()

    def _parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parsea la respuesta de DeepSeek"""
        try:
            content = (
                response.get("choices", [{}])[0].get("message", {}).get("content", "")
            )

            # Extraer información estructurada de la respuesta
            return {
                "analysis": content,
                "solution": self._extract_solution(content),
                "files_to_modify": self._extract_files(content),
                "explanation": self._extract_explanation(content),
            }
        except Exception as e:
            return {
                "error": f"Error parseando respuesta: {str(e)}",
                "solution": None,
                "files_to_modify": [],
                "explanation": "No se pudo parsear la respuesta",
            }

    def _extract_solution(self, content: str) -> str:
        """Extrae la solución del contenido de la respuesta"""
        # Buscar bloques de código
        if "```python" in content:
            start = content.find("```python") + 9
            end = content.find("```", start)
            if end != -1:
                return content[start:end].strip()

        # Buscar líneas que parezcan código
        lines = content.split("\n")
        code_lines = []
        for line in lines:
            if any(
                keyword in line.lower()
                for keyword in ["def ", "class ", "import ", "from ", "="]
            ):
                code_lines.append(line)

        return "\n".join(code_lines) if code_lines else content

    def _extract_files(self, content: str) -> list:
        """Extrae lista de archivos a modificar"""
        files = []
        lines = content.split("\n")
        for line in lines:
            if any(
                keyword in line.lower() for keyword in [".py", ".sh", ".yaml", ".yml"]
            ):
                # Buscar nombres de archivos
                words = line.split()
                for word in words:
                    if any(ext in word for ext in [".py", ".sh", ".yaml", ".yml"]):
                        files.append(word.strip(".,:;"))

        return list(set(files))

    def _extract_explanation(self, content: str) -> str:
        """Extrae la explicación del error"""
        # Buscar explicaciones después de "por qué" o "explicación"
        keywords = ["por qué", "explicación", "causa", "reason", "cause"]
        for keyword in keywords:
            if keyword in content.lower():
                idx = content.lower().find(keyword)
                return content[idx : idx + 200] + "..."

        return content[:200] + "..." if len(content) > 200 else content


if __name__ == "__main__":
    # Test del cliente
    client = DeepSeekClient()
    test_error = "NameError: name 'logger' is not defined"
    result = client.analyze_error(test_error)
    print(json.dumps(result, indent=2))
