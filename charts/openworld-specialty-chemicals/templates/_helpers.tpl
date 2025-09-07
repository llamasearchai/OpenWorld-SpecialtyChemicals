{{- define "openworld-specialty-chemicals.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "openworld-specialty-chemicals.fullname" -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "openworld-specialty-chemicals.chart" -}}
{{ .Chart.Name }}-{{ .Chart.Version }}
{{- end -}}
