FROM grafana/grafana:13.2.2

USER root

COPY aws/provisioning/datasources/datasources.yml \
     /etc/grafana/provisioning/datasources/datasources.yml

COPY aws/provisioning/dashboards/dashboards.yml \
     /etc/grafana/provisioning/dashboards/dashboards.yml

COPY dashboards/hybrid-ai-platform.json \
     /var/lib/grafana/dashboards/hybrid-ai-platform.json

COPY dashboards/hybrid-ai-finops.json \
     /var/lib/grafana/dashboards/hybrid-ai-finops.json

USER grafana
