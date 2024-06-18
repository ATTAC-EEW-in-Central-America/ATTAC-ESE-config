# ATTAC-ESE-config
This is the common configuration for the [ETHZ-SED SeisComP EEW modules (ESE)](https://github.com/SED-EEW/SED-EEW-SeisComP-contributions) operated by the national seiscmic network in central America part of ATTAC.

Esta es la configuración común para los [módulos ETHZ-SED SeisComP EEW (ESE)](https://github.com/SED-EEW/SED-EEW-SeisComP-contributions) operados por la red sísmica nacional en la parte de América Central de ATTAC.

This is including only the configuration that can be used in all ATTAC systems, in any country of Central America.

Esto incluye solo la configuración que se puede utilizar en todos los sistemas ATTAC, en cualquier país de Centroamérica.

In order to simplify long term support of the ESE system from ATTAC, do not include your agency specific configuration in this system configuration, but rather in the "user" configuration, or `~/.seiscomp/` folder. The system configuration might be modified in coordination with ETHZ-SED so that it can synchronised in all ATTAC systems.

Con el fin de simplificar el soporte a largo plazo del sistema ESE de ATTAC, no incluya la configuración específica de su agencia en esta configuración del sistema, sino en la configuración de "usuario" o en la carpeta `~/.seiscomp/`. La configuración del sistema podría modificarse en coordinación con ETHZ-SED para que pueda sincronizarse en todos los sistemas ATTAC.

## Configuration
### Get latest version of the configuration / Obtener la última versión de la configuración
```bash
git -C $SEISCOMP_ROOT pull
```

### Add configuration changes only relevant for the local system / Añadir cambios de configuración relevantes para el sistema local
Apply the required config changes in `~/.seiscomp/` or "user" configuration in `scconfig`.

Aplique los cambios de configuración requeridos en la configuración `~/.seiscomp/` o "usuario" en `scconfig`.

### Push configuration changes relevant for all ATTAC systems / Cambios de configuración push relevantes para todos los sistemas ATTAC
```bash
git  add <file>
git commit
git push
```
This requires write permission on the git remote origin.

Esto requiere permiso de escritura en el git remote origin.

### Comando de recordstream con varios sdsarchive;
```bash
recordstream = combined://slink/localhost:18000;combined/(combined/(sdsarchive//home/sysop/seiscomp/var/lib/archive/;sdsarchive//respaldos/??splitTime=2023-09-26T00:00:00Z);sdsarchive//respaldos2/1.INF-A.INF-AREA-SISMOLOGIA/BASE-SISMICA/DATA-Continua/??splitTime=2023-01-01T00:00:00Z)
```

### Git con el código hecho por Fred para actualizar la grilla utilizada por LOCSAT:
`https://github.com/FMassin/SeisComP-Location-Grid-Tuning`

#### Comando para ejecutar el código de la grilla de LOCSAT:
```bash
./grid4autoloc  picker_alias_name old_grid_file date > grid.conf
```

### EEWD
#### Repositorio de EEWD:
`https://github.com/SED-EEW/EEWD`

### Dashboards
#### To restart the EEW dashboard
First kill the python /opt/seiscomp/share/sceewv/index.py process PID and then:
 ```bash
00 00 * * * PYTHONPATH=/opt/seiscomp/lib/python LD_LIBRARY_PATH=/opt/seiscomp/lib python /opt/seiscomp/share/sceewv/index.py > /home/cam/logs/sceewv_dash.log 2>&1 &
```
This is also in crontab

#### Comando para correr el servicio web con los PSDs en el servidor 192.168.2.211:
```bash
python3 -m http.server 8060 --bind 0.0.0.0 --directory /home/sysop/PSD/PNG/ &
```

## Comandos para evaluar recursos del sistema:
### Revisar chache:
```bash
free -h
Liberar cache:
sudo -s
sync ; echo 3 > /proc/sys/vm/drop_caches
exit
```

### Comando para ver tamaño de la base de datos:
```sql
SELECT TABLE_NAME AS `Table`,ROUND(((DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024), 2) AS `Size (MB)`FROM information_schema.TABLES WHERE table_schema = "seiscomp" ORDER BY (data_length + index_length) DESC;
```

### Disk read speed:
```bash
sudo hdparm -Tt /dev/xvda1
```
with:
`/dev/xvda1`: name of disk

### Disk write speed:
```bash
ioping -S64M -L -s4k -W -c 10 .
```

### Ram speed:
```bash
mkdir -p ram; sudo mount -t tmpfs -o size=512M tmpfs ram; cd ram; ioping -S64M -L -s4k -W -c
```

