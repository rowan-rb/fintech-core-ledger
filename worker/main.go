package main

import (
"context"
"database/sql"
"encoding/json"
"fmt"
"log"
"net/http"
"time"

_ "github.com/lib/pq"
"github.com/prometheus/client_golang/prometheus"
"github.com/prometheus/client_golang/prometheus/promhttp"
"github.com/segmentio/kafka-go"
)

var (
processedEvents = prometheus.NewCounter(prometheus.CounterOpts{
Name: "ledger_processed_events_total",
Help: "Total number of outbox events processed by the Go worker.",
})
)

func init() {
prometheus.MustRegister(processedEvents)
}

// Estructura para leer el JSON que manda Debezium
type DebeziumMessage struct {
Payload struct {
ID string `json:"id"`
} `json:"payload"`
}

func main() {
connStr := "host=postgres port=5432 user=fintech password=fintech dbname=fintech sslmode=disable"
db, err := sql.Open("postgres", connStr)
if err != nil {
log.Fatal(err)
}
defer db.Close()

// Arrancar Prometheus
go func() {
http.Handle("/metrics", promhttp.Handler())
log.Println("Prometheus metrics serving on :9090")
log.Fatal(http.ListenAndServe(":9090", nil))
}()

// Configurar Kafka Reader
r := kafka.NewReader(kafka.ReaderConfig{
Brokers:  []string{"kafka:9092"},
Topic:    "fintech.public.outbox",
GroupID:  "go-worker-group",
MinBytes: 10e1, // 1KB
MaxBytes: 10e6, // 10MB
})
defer r.Close()

log.Println("Go Worker started. Listening to Kafka...")

for {
m, err := r.ReadMessage(context.Background())
if err != nil {
log.Printf("Error reading from Kafka: %v", err)
continue
}

var msg DebeziumMessage
if err := json.Unmarshal(m.Value, &msg); err != nil {
log.Printf("Error unmarshaling Debezium message: %v", err)
continue
}

// Procesar el evento (marcar como procesado en la BD)
_, err = db.Exec("UPDATE outbox SET processed_at = NOW() WHERE id = $1", msg.Payload.ID)
if err != nil {
log.Printf("Error updating DB: %v", err)
continue
}

fmt.Printf("Processed Event from Kafka: %s\n", msg.Payload.ID)
processedEvents.Inc()
time.Sleep(100 * time.Millisecond) // Simular trabajo
}
}