#!/bin/bash
cd /app
while true
do
    timeteps=('minutely' 'hourly' 'daily' 'weekly')
    for TIMESTEP in ${timeteps[*]}
    do
        export TIMESTEP=$TIMESTEP
        ./entrypoint.sh
    done
    sleep 55
done