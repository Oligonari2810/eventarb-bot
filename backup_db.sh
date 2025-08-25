#!/bin/bash
# Script de backup automático de la base de datos
# Usar con cron para backups horarios

# Configuración
DB_PATH="trades.db"
BACKUP_DIR="backups"
TIMESTAMP=$(date +%F-%H%M)

# Crear directorio de backup si no existe
mkdir -p "$BACKUP_DIR"

# Crear backup con timestamp
BACKUP_FILE="$BACKUP_DIR/trades-$TIMESTAMP.db"

echo "🔄 Creando backup de $DB_PATH..."
sqlite3 "$DB_PATH" ".backup '$BACKUP_FILE'"

if [ $? -eq 0 ]; then
    echo "✅ Backup creado exitosamente: $BACKUP_FILE"
    
    # Comprimir backup anterior (opcional)
    if [ -f "$BACKUP_DIR/trades-$(date -d '1 hour ago' +%F-%H%M).db" ]; then
        echo "🗜️ Comprimiendo backup anterior..."
        gzip "$BACKUP_DIR/trades-$(date -d '1 hour ago' +%F-%H%M).db"
    fi
    
    # Limpiar backups antiguos (mantener últimos 24)
    echo "🧹 Limpiando backups antiguos..."
    find "$BACKUP_DIR" -name "trades-*.db*" -mtime +1 -delete
    
    echo "🎯 Backup completado: $(ls -lh "$BACKUP_FILE")"
else
    echo "❌ Error creando backup"
    exit 1
fi
