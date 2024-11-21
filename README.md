# auditoryAphasia-python

## Documentation
Read documentation in [wiki](https://gitlab.socsci.ru.nl/neurotech/code/auditoryaphasia-python/-/wikis/home)

## Run
Run the experiment by invoking:
```python
python -m auditory_aphasia.main
```


## Install info
- It might be necessary to install python-tk, e.g., on MacOS `brew install python-tk` or `brew install python-tk@3.10` for a specific python version (here 3.10). 
Do this if you encounter the following error: ` No module named '_tkinter'`

## TODOs
- [ ] `import pyerp  # TODO: WHAT DO WE NEED PYERP FOR? << Replace this by a more standard solution`
- [ ] Configurations are loaded all over the place. This was formerly a wild mix of loading and reloading global variables. It is now limited to a `Borg pattern`, recreating copies of the same config, which is ensured as all places load using the `build_*` functions from `auditory_aphasia.config_builder`. Still better would be that all these classes get initialized with the correct configurations, maybe using a central `context` container.
