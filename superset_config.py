import os

for key, value in os.environ.items():
    globals()[key] = value


# echo 'import os' > /app/superset_home/superset_config.py
# echo 'for key, value in os.environ.items():' >> /app/superset_home/superset_config.py
# echo '    globals()[key] = False if value == "false" else value' >> /app/superset_home/superset_config.py
