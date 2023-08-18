#!/bin/bash

# Basic way, fit the four models and copy the models config template
# TODO: check if fit "fails", grab timesteps dynamicaly, build
# models.config from

# train models
timeteps=('minutely' 'hourly' 'daily' 'weekly')
for step in ${timeteps[*]}
do
    MODEL_TIMESTEP=$step python train.py
done

# write Tensorflow Serving config file
cat >../model_fit/models.config <<EOT
model_config_list {
    config {
        name: "minutely"
        base_path: '/models/minutely/'
        model_platform: 'tensorflow'
    }
    config {
        name: "hourly"
        base_path: '/models/hourly/'
        model_platform: 'tensorflow'
    }
    config {
        name: "daily"
        base_path: '/models/daily/'
        model_platform: 'tensorflow'
    }
    config {
        name: "weekly"
        base_path: '/models/weekly/'
        model_platform: 'tensorflow'
    }
}
EOT