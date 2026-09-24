terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.38"
    }
  }
}

provider "kubernetes" {
  config_path = "~/.kube/config"
}

resource "kubernetes_namespace" "hybrid_ai" {
  metadata {
    name = "hybrid-ai"
  }
}

resource "kubernetes_service" "redis" {
  metadata {
    name      = "hybrid-ai-redis"
    namespace = kubernetes_namespace.hybrid_ai.metadata[0].name
  }

  spec {
    selector = {
      app = "hybrid-ai-redis"
    }

    port {
      port        = 6379
      target_port = 6379
    }
  }
}

resource "kubernetes_deployment" "redis" {
  metadata {
    name      = "hybrid-ai-redis"
    namespace = kubernetes_namespace.hybrid_ai.metadata[0].name
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "hybrid-ai-redis"
      }
    }

    template {
      metadata {
        labels = {
          app = "hybrid-ai-redis"
        }
      }

      spec {
        container {
          name  = "redis"
          image = "redis:7-alpine"

          port {
            container_port = 6379
          }
        }
      }
    }
  }
}

resource "kubernetes_deployment" "postgres" {
  metadata {
    name      = "hybrid-ai-postgres"
    namespace = kubernetes_namespace.hybrid_ai.metadata[0].name
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "hybrid-ai-postgres"
      }
    }

    template {
      metadata {
        labels = {
          app = "hybrid-ai-postgres"
        }
      }

      spec {
        container {
          name  = "postgres"
          image = "postgres:16-alpine"

          port {
            container_port = 5432
          }

          env {
            name  = "POSTGRES_USER"
            value = "dylan"
          }

          env {
            name  = "POSTGRES_PASSWORD"
            value = "dylan"
          }

          env {
            name  = "POSTGRES_DB"
            value = "hybrid_ai"
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "postgres" {
  metadata {
    name      = "hybrid-ai-postgres"
    namespace = kubernetes_namespace.hybrid_ai.metadata[0].name
  }

  spec {
    selector = {
      app = "hybrid-ai-postgres"
    }

    port {
      port        = 5432
      target_port = 5432
    }
  }
}

resource "kubernetes_deployment" "api" {
  metadata {
    name      = "hybrid-ai-api"
    namespace = kubernetes_namespace.hybrid_ai.metadata[0].name
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "hybrid-ai-api"
      }
    }

    template {
      metadata {
        labels = {
          app = "hybrid-ai-api"
        }
      }

      spec {
        container {
          name  = "api"
          image = "hybrid-ai-api:latest"

          image_pull_policy = "Never"

          port {
            container_port = 8000
          }

          env {
            name  = "DATABASE_URL"

            value = "postgresql://dylan:dylan@hybrid-ai-postgres:5432/hybrid_ai"
          }

          env {
            name  = "REDIS_URL"

            value = "redis://hybrid-ai-redis:6379/0"
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "api" {
  metadata {
    name      = "hybrid-ai-api"
    namespace = kubernetes_namespace.hybrid_ai.metadata[0].name
  }

  spec {
    selector = {
      app = "hybrid-ai-api"
    }

    port {
      port        = 8000
      target_port = 8000
    }

    type = "ClusterIP"
  }
}