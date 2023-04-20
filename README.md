# ATTAC-ESE-config
This is the common configuration for the [ETHZ-SED SeisComP EEW modules (ESE)](https://github.com/SED-EEW/SED-EEW-SeisComP-contributions) operated by the national seiscmic network in central America part of ATTAC.

Esta es la configuración común para los [módulos ETHZ-SED SeisComP EEW (ESE)](https://github.com/SED-EEW/SED-EEW-SeisComP-contributions) operados por la red sísmica nacional en la parte de América Central de ATTAC.

This is including only the configuration that can be used in all ATTAC systems, in any country of Central America.

Esto incluye solo la configuración que se puede utilizar en todos los sistemas ATTAC, en cualquier país de Centroamérica.

In order to simplify long term support of the ESE system from ATTAC, do not include your agency specific configuration in this system configuration, but rather in the "user" configuration, or `~/.seiscomp/` folder. The system configuration might be modified in coordination with ETHZ-SED so that it can synchronised in all ATTAC systems.

Con el fin de simplificar el soporte a largo plazo del sistema ESE de ATTAC, no incluya la configuración específica de su agencia en esta configuración del sistema, sino en la configuración de "usuario" o en la carpeta `~/.seiscomp/`. La configuración del sistema podría modificarse en coordinación con ETHZ-SED para que pueda sincronizarse en todos los sistemas ATTAC.

## Get latest version of the configuration / Obtener la última versión de la configuración
```bash
git pull
```

## Add configuration changes only relevant for the local system / Añadir cambios de configuración relevantes para el sistema local
Apply the required config changes in `~/.seiscomp/` or "user" configuration in `scconfig`.

Aplique los cambios de configuración requeridos en la configuración `~/.seiscomp/` o "usuario" en `scconfig`.

## Push configuration changes relevant for all ATTAC systems / Cambios de configuración push relevantes para todos los sistemas ATTAC
```bash
git add <file>
git commit
git push
```
This requires write permission on the git remote origin.

Esto requiere permiso de escritura en el git remote origin.
