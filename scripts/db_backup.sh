#!/bin/bash

BACKUP_DIR="/home/moo/backup/db"
DATE=$(date +%Y%m%d_%H%M%S)
SQL_FILE="$BACKUP_DIR/company_db.sql"

if [ ! -d "$BACKUP_DIR" ]; then
	mkdir -p "$BACKUP_DIR" 
fi

if mariadb-dump --databases company_db > "$SQL_FILE";  then
			tar -czf "$BACKUP_DIR/backup_$DATE.tar.gz" "$SQL_FILE"

			if [ $? -eq 0 ]; then
					echo "backup successfully"	
			else
					echo "backup failed"
			fi
else
			echo "mariadb-dump failed"
fi