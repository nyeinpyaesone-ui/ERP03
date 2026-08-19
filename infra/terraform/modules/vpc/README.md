# VPC Module

Creates a VPC with public and private subnets across multiple availability zones.

## Features

- 3 public subnets (one per AZ)
- 3 private subnets (one per AZ)
- Internet Gateway for public subnets
- NAT Gateways for private subnets
- Route tables configured appropriately

## Usage

```hcl
module "vpc" {
  source = "./modules/vpc"
  
  vpc_cidr              = "10.0.0.0/16"
  environment           = "production"
  availability_zones    = ["us-east-1a", "us-east-1b", "us-east-1c"]
  enable_nat_gateway    = true
  single_nat_gateway    = false
}
```

## Outputs

- `vpc_id` - The ID of the VPC
- `public_subnet_ids` - List of public subnet IDs
- `private_subnet_ids` - List of private subnet IDs
- `nat_gateway_ids` - List of NAT Gateway IDs
