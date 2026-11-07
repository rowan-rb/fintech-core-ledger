FROM golang:1.21-alpine AS builder
WORKDIR /app

# Copiamos AMBOS archivos antes de descargar dependencias
COPY go.mod main.go ./

# Ahora Go puede leer el código y generar el go.sum automáticamente
RUN go mod tidy

# Compilamos
RUN go build -o /worker main.go

FROM alpine:latest
WORKDIR /app
COPY --from=builder /worker /app/worker
EXPOSE 9090
CMD ["/app/worker"]