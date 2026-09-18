#!/bin/bash

# ----------------------------------------------------------------------
# R36ARIA.sh - Launcher de PortMaster para R36ARIA
# Sigue la convencion oficial de portmaster.games/packaging.html
# ----------------------------------------------------------------------

XDG_DATA_HOME=${XDG_DATA_HOME:-$HOME/.local/share}

if [ -d "/opt/system/Tools/PortMaster/" ]; then
  controlfolder="/opt/system/Tools/PortMaster"
elif [ -d "/opt/tools/PortMaster/" ]; then
  controlfolder="/opt/tools/PortMaster"
elif [ -d "$XDG_DATA_HOME/PortMaster/" ]; then
  controlfolder="$XDG_DATA_HOME/PortMaster"
else
  controlfolder="/roms/ports/PortMaster"
fi

source $controlfolder/control.txt
[ -f "${controlfolder}/mod_${CFW_NAME}.txt" ] && source "${controlfolder}/mod_${CFW_NAME}.txt"

get_controls

# Carpeta del port (misma logica que usa PortMaster para el resto de los ports)
GAMEDIR=/$directory/ports/R36ARIA
CONFDIR="$GAMEDIR/conf"

mkdir -p "$CONFDIR"
cd "$GAMEDIR" || exit 1

# El log se sobreescribe en cada corrida, sirve para debug
> "$GAMEDIR/log.txt" && exec > >(tee "$GAMEDIR/log.txt") 2>&1

export SDL_GAMECONTROLLERCONFIG="$sdl_controllerconfig"
export PYTHONUNBUFFERED=1

# ----------------------------------------------------------------------
# La GPU de este dispositivo no siempre inicializa correctamente via
# KMSDRM/EGL (falla del kernel al configurar el regulador de energia en
# algunos builds), asi que R36ARIA dibuja todo por su cuenta directo al
# framebuffer (/dev/fb0) sin depender de la GPU. Para que el modulo de
# video de SDL igual inicialice bien (necesario para eventos/joystick),
# main.py fuerza el driver "offscreen" internamente -- no hace falta
# tocar SDL_VIDEODRIVER desde aca.
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# aria2 viene incluido dentro del propio port, no depende de que la
# consola lo tenga instalado. Ver bin/README.md para como conseguirlo.
# ----------------------------------------------------------------------
ARIA2_BIN="$GAMEDIR/bin/aria2c.${DEVICE_ARCH}"
if [ ! -f "$ARIA2_BIN" ]; then
  ARIA2_BIN="$GAMEDIR/bin/aria2c"
fi

if [ -f "$ARIA2_BIN" ]; then
  chmod +x "$ARIA2_BIN"
  export ARIA2_BIN
else
  pm_message "Falta el binario de aria2c en bin/. Revisa bin/README.md dentro de la carpeta del port."
  sleep 5
  exit 1
fi

# ----------------------------------------------------------------------
# Preferimos el pygame del sistema (via apt) sobre el de vendor/, ya que
# suele venir mejor integrado. Si el sistema no lo tiene, se intenta
# instalar; si eso tampoco funciona (sin internet, por ejemplo), se cae
# al vendor/ empaquetado.
# ----------------------------------------------------------------------
if ! python3 -c "import pygame" >/dev/null 2>&1; then
  if command -v apt-get >/dev/null 2>&1; then
    pm_message "Instalando pygame del sistema (apt)..."
    $ESUDO apt-get update >/dev/null 2>&1
    $ESUDO apt-get install -y python3-pygame python3-requests >/dev/null 2>&1
  fi
fi

if ! python3 -c "import pygame" >/dev/null 2>&1 && [ ! -d "$GAMEDIR/vendor/pygame" ]; then
  pm_message "Falta pygame: no esta en el sistema, no se pudo instalar con apt, y no hay nada en vendor/. Revisa vendor/README.md."
  sleep 5
  exit 1
fi

# NOTA: no lanzamos gptokeyb aca a proposito. gptokeyb traduce el
# joystick a eventos de teclado agarrando el dispositivo de forma
# exclusiva -- como R36ARIA lee el mando nativamente con pygame
# (JOYHATMOTION/JOYBUTTONDOWN), lanzar gptokeyb le bloquea todos los
# eventos reales al programa (solo queda funcionando la combinacion de
# salida forzada, que gptokeyb maneja por su cuenta). El menu de
# R36ARIA ya tiene su propia opcion "Salir" para cerrar prolijamente.

pm_platform_helper "python3"

python3 -u "$GAMEDIR/main.py"

pm_finish
