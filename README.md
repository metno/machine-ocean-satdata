# machine-ocean-satdata

Data directory for sentinel: /lustre/storeB/project/IT/geout/machine-ocean/data_raw/sentinel

# Load conda environment (on PPI rhel8 nodes)
```
source /modules/rhel8/conda/install/etc/profile.d/conda.sh 
conda activate production-10-2022
```

# Run notebook server
```
jupyter notebook --no-browser --ip=$(hostname -f) 
```
