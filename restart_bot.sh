#!/bin/bash
while true; do
    python main.py > bot.log 2>&1
    sleep 10
done
