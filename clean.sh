#!/usr/bin/env bash
find . -name "*json" ! -name "*example*" ! -name 'auth.json' ! -name 'default.json' -delete
find . -name "*.xlsx" -delete