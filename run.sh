#!/bin/bash
# Simple startup script for WineTranslator

cd "$(dirname "$0")"
python3 -m winetranslator
