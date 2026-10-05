export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const DEPLOYMENT_ENV =
  import.meta.env.VITE_DEPLOYMENT_ENV === 'aws' ? 'aws' : 'local'

export const IS_AWS = DEPLOYMENT_ENV === 'aws'

export const PLATFORM_CONFIG = IS_AWS
  ? {
      environment: 'AWS CLOUD',
      environmentDetail: 'Production-like environment',
      llmLabel: 'BEDROCK',
      llmModel: 'Amazon Nova Micro',
      aiEyebrow: 'RAG / BEDROCK',
      aiDescription:
        'Ask questions across structured supply-chain data and the platform knowledge base using Amazon Bedrock inference.',
      database: 'Amazon RDS + pgvector',
      cache: 'Amazon ElastiCache Valkey',
      metrics: 'Amazon Managed Prometheus',
      grafana: 'Grafana on ECS',
      tracing: 'CloudWatch',
      inference: 'Bedrock + Nova Micro',
    }
  : {
      environment: 'LOCAL',
      environmentDetail: 'Local development environment',
      llmLabel: 'LLAMA',
      llmModel: 'Llama 3.2 3B',
      aiEyebrow: 'RAG / LLAMA',
      aiDescription:
        'Ask questions across structured supply-chain data and the platform knowledge base using local Llama inference.',
      database: 'PostgreSQL + pgvector',
      cache: 'Redis',
      metrics: 'Prometheus',
      grafana: 'Grafana',
      tracing: 'Tempo',
      inference: 'Ollama + Llama',
    }
