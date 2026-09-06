# ElastiCache Redis Module

Creates a managed ElastiCache Redis cluster with cluster mode enabled.

## Features

- Cluster mode enabled for horizontal scaling
- Multi-AZ replication groups
- Automatic failover
- Encryption in transit and at rest
- Automated backups

## Usage

```hcl
module "elasticache" {
  source = "./modules/elasticache"
  
  cluster_id           = "erp-redis"
  node_type            = "cache.r6g.large"
  num_cache_nodes      = 3
  parameter_group_name = aws_elasticache_parameter_group.main.name
  subnet_group_name    = aws_elasticache_subnet_group.main.name
  security_group_ids   = [aws_security_group.redis.id]
}
```

## Outputs

- `primary_endpoint_address` - Primary endpoint address
- `reader_endpoint_address` - Reader endpoint address
- `arn` - Cache cluster ARN
