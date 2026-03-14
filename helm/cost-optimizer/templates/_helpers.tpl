{{/*
Expand the name of the chart.
*/}}
{{- define "cost-optimizer.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "cost-optimizer.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "cost-optimizer.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "cost-optimizer.labels" -}}
helm.sh/chart: {{ include "cost-optimizer.chart" . }}
{{ include "cost-optimizer.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "cost-optimizer.selectorLabels" -}}
app.kubernetes.io/name: {{ include "cost-optimizer.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Backend labels
*/}}
{{- define "cost-optimizer.backendLabels" -}}
{{ include "cost-optimizer.labels" . }}
app.kubernetes.io/component: backend
{{- end }}

{{/*
Backend selector labels
*/}}
{{- define "cost-optimizer.backendSelectorLabels" -}}
{{ include "cost-optimizer.selectorLabels" . }}
app.kubernetes.io/component: backend
{{- end }}

{{/*
Frontend labels
*/}}
{{- define "cost-optimizer.frontendLabels" -}}
{{ include "cost-optimizer.labels" . }}
app.kubernetes.io/component: frontend
{{- end }}

{{/*
Frontend selector labels
*/}}
{{- define "cost-optimizer.frontendSelectorLabels" -}}
{{ include "cost-optimizer.selectorLabels" . }}
app.kubernetes.io/component: frontend
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "cost-optimizer.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "cost-optimizer.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Backend secret name
*/}}
{{- define "cost-optimizer.backendSecretName" -}}
{{- if .Values.backend.externalSecret.enabled }}
{{- .Values.backend.externalSecret.name }}
{{- else }}
{{- printf "%s-backend-secret" (include "cost-optimizer.fullname" .) }}
{{- end }}
{{- end }}
